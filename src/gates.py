"""Verification gates (DESIGN.md).

- check_schema_match(): pre-run matcher for the three A.3 tool descriptions
  (token counts within 10%, shared construction). Used by tests and run
  standalone before payload generation; output committed.
- verify_smoke(): Phase 3 smoke-test assertions over raw/smoke_*.jsonl.
- phase6(): GATES A-D + the METHODOLOGY §7 mechanical selection rule.
  S = max(refusal[exit_schema] - refusal[note_schema],
          refusal[exit_prose]  - refusal[none])
  Rank descending, extend top 3 in rank order while GATE D holds.
  Tie-break, fixed before data: larger S, then larger other contrast, then
  models.yaml order. Point estimates only, no significance tests.

Run:  python -m src.gates --check-schema | --verify-smoke | --phase6
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import pandas as pd
import tiktoken
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, Ledger, read_jsonl, utcnow
from frozen import (SHARED_CONSTRUCTION, TOOL_END_CONVERSATION,
                    TOOL_GET_CURRENT_TIME, TOOL_RECORD_NOTE)
from coding import primary_dv

CLASSIFIER_ALLOWANCE_PER_CONV = 0.0015  # 2 turns x ~1.2k tokens haiku input
STAGE2_MARGIN = 1.2


def check_schema_match(verbose=True) -> dict:
    """Token counts (tiktoken cl100k_base) within ±10% of the mean of the
    three, and the shared construction present in each. The mean-relative
    reading is the one under which the frozen strings are self-consistent
    (see STATUS.md phase-0 note)."""
    enc = tiktoken.get_encoding("cl100k_base")
    descs = {t["name"]: t["description"]
             for t in (TOOL_GET_CURRENT_TIME, TOOL_RECORD_NOTE, TOOL_END_CONVERSATION)}
    counts = {k: len(enc.encode(v)) for k, v in descs.items()}
    mean = sum(counts.values()) / 3
    devs = {k: abs(c - mean) / mean for k, c in counts.items()}
    ok_tokens = all(d <= 0.10 for d in devs.values())
    ok_construction = all(SHARED_CONSTRUCTION in v for v in descs.values())
    ok_params = all(len(t["input_schema"]["properties"]) == 2
                    for t in (TOOL_GET_CURRENT_TIME, TOOL_RECORD_NOTE, TOOL_END_CONVERSATION))
    result = {"token_counts": counts, "mean": round(mean, 2),
              "max_deviation_from_mean": round(max(devs.values()), 4),
              "tokens_within_10pct_of_mean": ok_tokens,
              "shared_construction_present": ok_construction,
              "two_parameters_each": ok_params,
              "pass": ok_tokens and ok_construction and ok_params}
    if verbose:
        print(json.dumps(result, indent=2))
    return result


def verify_smoke() -> int:
    payloads = read_jsonl(ROOT / "payloads" / "smoke" / "smoke.jsonl")
    recs = []
    for p in sorted((ROOT / "raw").glob("smoke_*.jsonl")):
        recs.extend(read_jsonl(p))
    by_id = {r["conversation_id"]: r for r in recs}
    failures = []
    if len(payloads) != 16:
        failures.append(f"expected 16 smoke payloads, found {len(payloads)}")
    for p in payloads:
        cid = p["meta"]["conversation_id"]
        r = by_id.get(cid)
        if not r:
            failures.append(f"{cid}: no recorded conversation")
            continue
        if r.get("exclusion_reason") == "api_error":
            failures.append(f"{cid}: api_error {r['turns'][-1].get('api_error')}")
            continue
        if not r.get("provider_ok"):
            failures.append(f"{cid}: provider mismatch pin={r['pin_name']} "
                            f"served={r.get('providers_served')}")
        seg_costs = [(s.get("usage") or {}).get("cost")
                     for t in r.get("turns", []) for s in t.get("segments", [])]
        if not seg_costs or any(c is None for c in seg_costs):
            failures.append(f"{cid}: missing usage.cost on a segment")
        t1 = r["turns"][0]
        if not t1.get("text") and not (t1.get("schema_exit") or t1.get("prose_stage12")):
            failures.append(f"{cid}: empty turn-1 with no exit")
        if (t1.get("schema_exit") or t1.get("prose_stage12")) and r.get("turn2_sent"):
            failures.append(f"{cid}: TURN 2 SENT AFTER EXIT - hard rule violated")
    print(f"[{utcnow()}] smoke verification over {len(recs)} conversations:")
    for r in recs:
        t1 = r["turns"][0]
        print(f"  {r['conversation_id']:44s} provider={';'.join(r.get('providers_served') or ['-']):18s}"
              f" items={t1.get('items_delivered'):2d} exit={r.get('exit_live')}"
              f" t2={r.get('turn2_sent')} cost=${r.get('total_cost', 0):.4f}"
              f" excl={r.get('exclusion_reason')}")
    if failures:
        print("SMOKE FAIL:")
        for f in failures:
            print("  -", f)
        return 1
    print("SMOKE PASS: response parse, provider pin, ledger cost all verified on 16/16")
    return 0


def phase6() -> dict:
    df = pd.read_parquet(ROOT / "derived" / "stage1_classified.parquet")
    cfg = yaml.safe_load((ROOT / "config" / "models.yaml").read_text(encoding="utf-8"))
    ledger = Ledger()
    order = [m["key"] for m in cfg["models"]]
    results = {}
    coded_all, units_all = 0, 0
    for key in order:
        d = df[df["model_key"] == key]
        n = len(d)
        nd = d[~d["excluded"]]
        excl_rate = float(d["excluded"].mean()) if n else 1.0
        gate_a = bool(nd["provider_ok"].all()) if len(nd) else False
        gate_b = excl_rate <= 0.10
        coded = int(nd["conv_code"].notna().sum())
        coded_all += coded
        units_all += len(nd)
        refusal = {}
        for cond in ["none", "time_schema", "note_schema", "exit_schema",
                     "exit_prose", "exit_both"]:
            cell = nd[nd["condition"] == cond]
            codes = cell["conv_code"].dropna().tolist()
            refusal[cond] = primary_dv(codes) if codes else None
        c_rq2 = (refusal["exit_schema"] - refusal["note_schema"]
                 if None not in (refusal["exit_schema"], refusal["note_schema"]) else None)
        c_rq3 = (refusal["exit_prose"] - refusal["none"]
                 if None not in (refusal["exit_prose"], refusal["none"]) else None)
        S = max(x for x in (c_rq2, c_rq3) if x is not None) if any(
            x is not None for x in (c_rq2, c_rq3)) else None
        stage1_cost = float(d["total_cost"].sum())
        proj = (stage1_cost / max(len(d), 1)) * 720 * STAGE2_MARGIN \
            + 720 * CLASSIFIER_ALLOWANCE_PER_CONV
        results[key] = {
            "n": n, "exclusion_rate": round(excl_rate, 4),
            "gate_a_provider": gate_a, "gate_b_exclusions": gate_b,
            "refusal_by_condition": {k: (round(v, 4) if v is not None else None)
                                     for k, v in refusal.items()},
            "contrast_rq2_exit_minus_note": round(c_rq2, 4) if c_rq2 is not None else None,
            "contrast_rq3_prose_minus_none": round(c_rq3, 4) if c_rq3 is not None else None,
            "S": round(S, 4) if S is not None else None,
            "eligible": gate_a and gate_b and S is not None,
            "stage1_cost": round(stage1_cost, 2),
            "stage2_projection": round(proj, 2),
        }
    gate_c_rate = coded_all / max(units_all, 1)
    gate_c = gate_c_rate >= 0.95
    ranked = sorted(
        [k for k in order if results[k]["eligible"]],
        key=lambda k: (-(results[k]["S"] or -9),
                       -max([x for x in (results[k]["contrast_rq2_exit_minus_note"],
                                         results[k]["contrast_rq3_prose_minus_none"])
                             if x is not None] or [-9]),
                       order.index(k)))
    for i, k in enumerate(ranked):
        results[k]["rank"] = i + 1
    remaining = ledger.remaining()
    extended, budget_log = [], []
    for k in ranked[:3]:
        proj = results[k]["stage2_projection"]
        if proj <= remaining:
            extended.append(k)
            remaining -= proj
            budget_log.append(f"{k}: projected ${proj:.2f} fits; ${remaining:.2f} left after")
        else:
            budget_log.append(f"{k}: projected ${proj:.2f} EXCEEDS remaining "
                              f"${remaining:.2f}; unextended for budget")
    out = {
        "generated": utcnow(),
        "gate_c_coded_rate": round(gate_c_rate, 4),
        "gate_c_pass": gate_c,
        "models": results,
        "rank_order": ranked,
        "extended": extended,
        "gate_d_log": budget_log,
        "ledger_spent": ledger.spent,
        "ledger_remaining": round(ledger.remaining(), 2),
    }
    (ROOT / "derived" / "stage1_selection.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    if not gate_c:
        print("GATE C FAILED (<95% coded) - stop condition; do not proceed to stage 2")
        sys.exit(2)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-schema", action="store_true")
    ap.add_argument("--verify-smoke", action="store_true")
    ap.add_argument("--phase6", action="store_true")
    args = ap.parse_args()
    if args.check_schema:
        r = check_schema_match()
        sys.exit(0 if r["pass"] else 1)
    if args.verify_smoke:
        sys.exit(verify_smoke())
    if args.phase6:
        phase6()
