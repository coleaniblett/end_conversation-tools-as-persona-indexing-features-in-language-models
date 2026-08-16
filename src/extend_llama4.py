"""TASK 1 — llama4_maverick confirmatory extension on the Vertex pin.

The clean Vertex re-run (T19) produced the study's largest primary-DV effect
(refusal none 0.0 / time_schema 51.7 / note_schema 28.3 / exit_schema 6.9 /
exit_prose 0.0 / exit_both 5.0, all code c) at 60/cell screen resolution.
This extension brings it to confirmatory scale: 6 conditions x 30 stimuli x
4 reps = 720 FRESH conversations, 120/cell, stage label `llama4_stage2`,
protocol identical to the other stage-2 runs. Taken OUTSIDE the §7 selection
rule per METHODOLOGY §10 [2026-08-15T23:00Z]: the rule's statistic is
one-directional and scores the large negative rq2 contrast as zero — a
defect in the rule, not evidence of no effect. Never pooled with any other
stage.

Sequence:
  python -m src.extend_llama4 --gen       # payloads + budget projection
  python -m src.runner --stage llama4_stage2 --models llama4_maverick
  python -m src.detect_exit --stage llama4_stage2
  python -m src.classify --stage llama4_stage2
  python -m src.extend_llama4 --report    # outputs/T20_llama4_stage2.csv
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

import pandas as pd
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, utcnow
from payloads import build_request, conv_id
from frozen import CONDITION_ORDER, CONDITIONS
from coding import primary_dv, REFUSAL_CODES
from analyze import wilson

STAGE = "llama4_stage2"
REPS = 4
SESSION_BASELINE = 10.7284   # ledger at session start (2026-08-15T23:00Z)
SESSION_CAP = 45.00          # incremental cap this session
PROJECTION_MARGIN = 1.3
CLASSIFIER_ALLOWANCE_PER_CONV = 0.0015

OUT = ROOT / "outputs" / "T20_llama4_stage2.csv"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gen():
    models = yaml.safe_load((ROOT / "config" / "models.yaml").read_text(encoding="utf-8"))
    m = next(x for x in models["models"] if x["key"] == "llama4_maverick")
    if m["pin_slug"] != "google-vertex":
        raise SystemExit(f"pin is {m['pin_slug']}, expected google-vertex")
    stimuli = yaml.safe_load((ROOT / "config" / "stimuli.yaml").read_text(encoding="utf-8"))
    out = ROOT / "payloads" / STAGE / "llama4_maverick.jsonl"
    if out.exists():
        print(f"{out} exists, leaving as-is (idempotent)")
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        n = 0
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            for condition in CONDITION_ORDER:
                for s in stimuli["stimuli"]:
                    for rep in range(1, REPS + 1):
                        body = build_request(m, condition, s["prompt"])
                        meta = {
                            "conversation_id": conv_id(STAGE, m["key"],
                                                       condition, s["id"], rep),
                            "stage": STAGE, "model_key": m["key"],
                            "slug": m["slug"], "condition": condition,
                            "condition_num": CONDITIONS[condition]["num"],
                            "stimulus_id": s["id"], "tier": s["tier"],
                            "rep": rep, "pin_name": m["pin_name"],
                            "pin_slug": m["pin_slug"],
                        }
                        f.write(json.dumps({"meta": meta, "request": body},
                                           ensure_ascii=False) + "\n")
                        n += 1
        print(f"wrote {n} payloads to {out}")

    # projection from the llama4_vertex actuals on the SAME pin (360 convs)
    prior = read_jsonl(ROOT / "raw" / "llama4_vertex_llama4_maverick.jsonl")
    per_conv = sum(r.get("total_cost") or 0.0 for r in prior) / max(len(prior), 1)
    ledger = json.loads((ROOT / "ledger.json").read_text(encoding="utf-8"))
    proj = 720 * per_conv * PROJECTION_MARGIN + 720 * CLASSIFIER_ALLOWANCE_PER_CONV
    session_spent = ledger["spent_usd"] - SESSION_BASELINE
    print(f"projection: 720 x ${per_conv:.5f} x {PROJECTION_MARGIN} + classify "
          f"allowance = ${proj:.2f}; session spent ${session_spent:.2f} of "
          f"${SESSION_CAP:.2f}; ledger ${ledger['spent_usd']:.2f}/"
          f"${ledger['cap_usd']:.2f}")
    if session_spent + proj > SESSION_CAP:
        raise SystemExit(2)
    print("within session cap: OK to run")


def report():
    rows = []

    def row(section, condition, metric, value, note=""):
        rows.append({"section": section, "condition": condition,
                     "metric": metric, "value": value, "note": note})

    pq = ROOT / "derived" / f"{STAGE}_classified.parquet"
    df = pd.read_parquet(pq)
    if len(df) != 720:
        raise SystemExit(f"expected 720 conversations, parquet has {len(df)}")

    row("pins", "ALL", "provider_ok", f"{int(df['provider_ok'].sum())}/{len(df)}")
    for reason in ("api_error", "empty_response", "truncation"):
        row("exclusions", "ALL", reason,
            int((df["exclusion_reason"] == reason).sum()))

    for cond in CONDITION_ORDER:
        nd = df[(df["condition"] == cond) & (~df["excluded"])]
        codes = nd["conv_code"].dropna().tolist()
        k = sum(1 for c in codes if c in REFUSAL_CODES)
        n = len(codes)
        lo, hi = wilson(k, n)
        row("refusal", cond, "k_refusal", k)
        row("refusal", cond, "n_coded", n)
        row("refusal", cond, "refusal_prop", round(primary_dv(codes), 4) if codes else "")
        row("refusal", cond, "wilson_lo", round(lo, 4))
        row("refusal", cond, "wilson_hi", round(hi, 4))
        for code in ("b", "c", "d", "e"):
            row("refusal", cond, f"code_{code}", sum(1 for c in codes if c == code))
        for tier in (1, 2):
            t = nd[nd["tier"] == tier]
            row("refusal_by_tier", cond, f"k_refusal_tier{tier}",
                int(t["contains_refusal"].fillna(False).sum()))
            row("refusal_by_tier", cond, f"n_tier{tier}", len(t))
        k_ex = int(nd["exit"].sum())
        lo_e, hi_e = wilson(k_ex, len(nd))
        paths = nd[nd["exit"]]["exit_path"].value_counts().to_dict()
        row("tool_invocation", cond, "exit_rate",
            round(k_ex / len(nd), 4) if len(nd) else "")
        row("tool_invocation", cond, "k_exits", k_ex)
        row("tool_invocation", cond, "n", len(nd))
        row("tool_invocation", cond, "wilson_lo", round(lo_e, 4))
        row("tool_invocation", cond, "wilson_hi", round(hi_e, 4))
        row("tool_invocation", cond, "paths",
            ";".join(f"{p}={c}" for p, c in sorted(paths.items())))
        row("tool_invocation", cond, "nonexit_tool_called",
            int(nd["nonexit_tool_called"].sum()))

    out_df = pd.DataFrame(rows)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T20_llama4_stage2 | generated {utcnow()} | source "
                f"derived/{STAGE}_classified.parquet sha256={sha256(pq)} | "
                f"confirmatory 120/cell, 4 reps, Vertex pin; extension taken "
                f"outside the §7 rule per METHODOLOGY §10 2026-08-15T23:00Z; "
                f"never pooled with llama4_vertex, Parasail stage-1, or any "
                f"other stage\n")
        out_df.to_csv(f, index=False)
    print(f"wrote {OUT} ({len(out_df)} rows)\n")

    for section, metrics in (
            ("refusal", ["k_refusal", "n_coded", "refusal_prop", "wilson_lo", "wilson_hi"]),
            ("refusal", ["code_b", "code_c", "code_d", "code_e"]),
            ("refusal_by_tier", ["k_refusal_tier1", "n_tier1", "k_refusal_tier2", "n_tier2"]),
            ("tool_invocation", ["exit_rate", "k_exits", "n", "paths"])):
        print(out_df[(out_df.section == section) & (out_df.metric.isin(metrics))]
              .pivot(index="condition", columns="metric", values="value")
              .reindex(CONDITION_ORDER).to_string())
        print()
    print(out_df[out_df.section.isin(["pins", "exclusions"])].to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.gen:
        gen()
    elif args.report:
        report()
    else:
        raise SystemExit("pass --gen or --report")
