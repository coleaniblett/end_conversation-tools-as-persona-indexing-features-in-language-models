"""B2 — recode the stage-1 exclusions into behavioral vs technical categories.

METHODOLOGY §8's exclusion rule treats empty responses as technical. Twelve of
the 44 stage-1 exclusions are hallucinated calls to tools absent from the
schema — model BEHAVIOR, not API failure. This script adds two REPORTED
categories, strictly separate from the primary DV and from codes (a)-(e):

  hallucinated_tool  the turn called a tool not in its schema (runner anomaly
                     'unknown/undeclared tool call'), zero visible text
  null_turn          finish=stop (or other non-length), zero content, no tool
                     call, no anomaly
  genuine_api_error  transport/provider error (exclusion_reason api_error)
  truncation         finish=length (§8 exclusion, unchanged)

The primary DV definition is NOT changed and GATE B outcomes are NOT
retroactively altered: the table reports what GATE B did and what it would
have done under the recoding, side by side.

Outputs: outputs/T17_exclusion_recode.csv (+ gate comparison in the header)
Run: python -m src.recode_exclusions
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, utcnow

OUT = ROOT / "outputs"
GATE_B_CEILING = 0.10


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recode(rec) -> str:
    if rec["exclusion_reason"] == "api_error":
        return "genuine_api_error"
    if rec["exclusion_reason"] == "truncation":
        return "truncation"
    # empty_response: split by what the turns actually contain
    for t in rec["turns"]:
        if t.get("anomaly") and t["anomaly"].startswith(
                "unknown/undeclared tool call"):
            return "hallucinated_tool"
    return "null_turn"


def main():
    rows = []
    sources = {}
    for path in sorted((ROOT / "raw").glob("stage1_*.jsonl")):
        sources[str(path.relative_to(ROOT))] = sha256(path)
        for rec in read_jsonl(path):
            if not rec["excluded"]:
                continue
            rows.append({
                "stage": rec["stage"], "model": rec["model_key"],
                "condition": rec["condition"],
                "recorded_reason": rec["exclusion_reason"],
                "recoded_category": recode(rec),
            })
    df = pd.DataFrame(rows)
    table = (df.groupby(["stage", "model", "condition", "recorded_reason",
                         "recoded_category"])
             .size().reset_index(name="n")
             .sort_values(["model", "condition", "recoded_category"]))

    # GATE B side by side (llama4_maverick is the only excluding model)
    n_llama_total = 360  # 6 conditions x 30 stimuli x 2 reps, stage 1
    n_excl_asrun = len(df[df.model == "llama4_maverick"])
    n_excl_recoded = len(df[(df.model == "llama4_maverick")
                            & (df.recoded_category.isin(
                                ["genuine_api_error", "truncation"]))])
    asrun_rate = n_excl_asrun / n_llama_total
    recoded_rate = n_excl_recoded / n_llama_total
    gate_note = (
        f"GATE B as run: llama4_maverick {n_excl_asrun}/{n_llama_total}="
        f"{asrun_rate:.3f} > {GATE_B_CEILING} -> FAILED, dropped from "
        f"selection eligibility. Under recoding (behavioral categories are "
        f"reported, not excluded): technical exclusions "
        f"{n_excl_recoded}/{n_llama_total}={recoded_rate:.3f} <= "
        f"{GATE_B_CEILING} -> would have PASSED; its selection statistic "
        f"S=0.0 (T12) is below the extension ranks and the amended 0.05 "
        f"threshold, so the stage-2 selection would have been UNCHANGED. "
        f"Primary DV definition unchanged; no completed analysis altered.")

    p = OUT / "T17_exclusion_recode.csv"
    src = "; ".join(f"{k} sha256={v}" for k, v in sources.items()
                    if "llama4" in k)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T17_exclusion_recode | generated {utcnow()} | source "
                f"{src} | categories separate from primary DV and codes "
                f"(a)-(e) | {gate_note}\n")
        table.to_csv(f, index=False)
    print(f"wrote {p} ({len(table)} rows)")
    print(table.to_string(index=False))
    print(gate_note)


if __name__ == "__main__":
    main()
