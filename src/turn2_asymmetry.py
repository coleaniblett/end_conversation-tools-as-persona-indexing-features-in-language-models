"""B3 — turn-2 gating asymmetry between prose and schema exit detection.

The live turn-2 gate uses prose detection stages 1-2 (regex + opening span);
the stage-3 judge runs later. Every judge overturn (MENTION, not CALL) on a
TURN-1 hit with <20 items delivered is a conversation that was denied the
continuation pressure it should have received under the final coding. In
schema conditions this is structurally impossible (a structured call is
unambiguous), so any denial is an asymmetry between the two detection paths.

Reports, per model per stage:
  - judge overturn counts (total, and split by which turn the stage-1/2 hit
    occurred in),
  - conversations denied turn-2 pressure (turn-1 overturned hit, <20 items,
    turn 2 not sent),
  - turn-2 rate in prose-detected conditions (exit_prose, exit_both) vs
    schema-only (exit_schema) vs no-exit conditions, as run AND
    counterfactually (denied conversations counted as turn-2-eligible).

Output: outputs/T13_turn2_asymmetry.csv
Run: python -m src.turn2_asymmetry
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, utcnow

OUT = ROOT / "outputs"
PROSE_DETECTED = {"exit_prose", "exit_both"}
GROUPS = {
    "prose_detected": PROSE_DETECTED,
    "schema_only": {"exit_schema"},
    "no_exit_affordance": {"none", "time_schema", "note_schema"},
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = {}
    exits = {}  # conversation_id -> exit row (judge verdicts)
    for stage in ("stage1", "stage2"):
        p = ROOT / "derived" / f"{stage}_exits.jsonl"
        sources[str(p.relative_to(ROOT))] = sha256(p)
        for r in read_jsonl(p):
            exits[r["conversation_id"]] = r

    rows = []
    denied_detail = []
    for stage in ("stage1", "stage2"):
        for path in sorted((ROOT / "raw").glob(f"{stage}_*.jsonl")):
            sources[str(path.relative_to(ROOT))] = sha256(path)
            recs = [r for r in read_jsonl(path) if not r["excluded"]]
            if not recs:
                continue
            model = path.stem.replace(f"{stage}_", "")
            # per-conversation overturn + denial flags
            for r in recs:
                er = exits.get(r["conversation_id"], {})
                r["_overturned"] = bool(er.get("stage12_overturned"))
                t1 = r["turns"][0]
                r["_t1_prose_hit"] = bool(t1["prose_stage12"])
                r["_denied"] = (r["_overturned"] and r["_t1_prose_hit"]
                                and not t1["schema_exit"]
                                and t1["items_delivered"] < 20
                                and not r["turn2_sent"])
                if r["_denied"]:
                    denied_detail.append(
                        {"stage": stage, "model": model,
                         "condition": r["condition"],
                         "conversation_id": r["conversation_id"]})
            for gname, conds in GROUPS.items():
                g = [r for r in recs if r["condition"] in conds]
                if not g:
                    continue
                n = len(g)
                sent = sum(1 for r in g if r["turn2_sent"])
                denied = sum(1 for r in g if r["_denied"])
                over_total = sum(1 for r in g if r["_overturned"])
                over_t1 = sum(1 for r in g if r["_overturned"]
                              and r["_t1_prose_hit"])
                rows.append({
                    "stage": stage, "model": model, "condition_group": gname,
                    "n_eligible": n,
                    "overturns_total": over_total,
                    "overturns_turn1_hit": over_t1,
                    "overturns_turn2_hit": over_total - over_t1,
                    "denied_turn2": denied,
                    "turn2_sent": sent,
                    "turn2_rate_as_run": round(sent / n, 4),
                    "turn2_rate_counterfactual": round((sent + denied) / n, 4),
                })

    df = pd.DataFrame(rows).sort_values(
        ["stage", "model", "condition_group"])
    p = OUT / "T13_turn2_asymmetry.csv"
    manifest = hashlib.sha256(
        "".join(f"{k}={v}" for k, v in sorted(sources.items()))
        .encode()).hexdigest()
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T13_turn2_asymmetry | generated {utcnow()} | source "
                f"raw/stage*_*.jsonl + derived/stage*_exits.jsonl manifest "
                f"sha256={manifest} | denied_turn2 = judge-overturned turn-1 "
                f"stage-1/2 hit, <20 items, turn 2 withheld (structurally "
                f"impossible in schema conditions)\n")
        df.to_csv(f, index=False)
    print(f"wrote {p} ({len(df)} rows)")
    nz = df[(df.overturns_total > 0) | (df.denied_turn2 > 0)]
    print(nz.to_string(index=False) if len(nz) else "no overturns anywhere")
    if denied_detail:
        print("\ndenied conversations:")
        for d in denied_detail:
            print(f"  {d['stage']} {d['model']} {d['condition']} "
                  f"{d['conversation_id']}")


if __name__ == "__main__":
    main()
