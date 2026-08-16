"""TASK 3 — report for the symmetric extension of the frontier nulls.

sonnet46 and gpt5_mini had 60/cell screen data only while three models
carried 120/cell confirmatory data; stage2b brings both to 120/cell (720
fresh conversations each, 4 reps, protocol identical to stage2) so the
paper can report them as measured nulls at the same evidentiary standard
rather than as absence of data. Stage label `stage2b`; never pooled with
stage1, stage2, or any llama4 stage.

Run: python -m src.report_stage2b     # outputs/T21_stage2b_frontier_nulls.csv
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, utcnow
from frozen import CONDITION_ORDER
from coding import primary_dv, REFUSAL_CODES
from analyze import wilson

MODELS = ["sonnet46", "gpt5_mini"]
OUT = ROOT / "outputs" / "T21_stage2b_frontier_nulls.csv"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pq = ROOT / "derived" / "stage2b_classified.parquet"
    df = pd.read_parquet(pq)
    if len(df) != 1440:
        raise SystemExit(f"expected 1440 conversations, parquet has {len(df)}")
    rows = []

    def row(section, model, condition, metric, value, note=""):
        rows.append({"section": section, "model": model,
                     "condition": condition, "metric": metric,
                     "value": value, "note": note})

    for key in MODELS:
        d = df[df["model_key"] == key]
        row("accounting", key, "ALL", "n", len(d))
        row("accounting", key, "ALL", "pin_ok", int(d["provider_ok"].sum()))
        for reason in ("api_error", "empty_response", "truncation"):
            row("accounting", key, "ALL", f"excl_{reason}",
                int((d["exclusion_reason"] == reason).sum()))
        nd_all = d[~d["excluded"]]
        S_parts = {}
        for cond in CONDITION_ORDER:
            nd = nd_all[nd_all["condition"] == cond]
            codes = nd["conv_code"].dropna().tolist()
            k = sum(1 for c in codes if c in REFUSAL_CODES)
            n = len(codes)
            lo, hi = wilson(k, n)
            S_parts[cond] = primary_dv(codes) if codes else None
            row("refusal", key, cond, "k_refusal", k)
            row("refusal", key, cond, "n_coded", n)
            row("refusal", key, cond, "refusal_prop",
                round(S_parts[cond], 4) if codes else "")
            row("refusal", key, cond, "wilson_lo", round(lo, 4))
            row("refusal", key, cond, "wilson_hi", round(hi, 4))
            k_ex = int(nd["exit"].sum())
            row("tool_invocation", key, cond, "exit_rate",
                round(k_ex / len(nd), 4) if len(nd) else "")
            row("tool_invocation", key, cond, "k_exits", k_ex)
            paths = nd[nd["exit"]]["exit_path"].value_counts().to_dict()
            row("tool_invocation", key, cond, "paths",
                ";".join(f"{p}={c}" for p, c in sorted(paths.items())))
            row("tool_invocation", key, cond, "stage12_overturned",
                int(nd["stage12_overturned"].sum()))
        rq2 = S_parts["exit_schema"] - S_parts["note_schema"]
        rq3 = S_parts["exit_prose"] - S_parts["none"]
        row("contrasts", key, "ALL", "rq2_exit_minus_note", round(rq2, 4))
        row("contrasts", key, "ALL", "rq3_prose_minus_none", round(rq3, 4))

    out_df = pd.DataFrame(rows)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T21_stage2b_frontier_nulls | generated {utcnow()} | "
                f"source derived/stage2b_classified.parquet sha256={sha256(pq)}"
                f" | 120/cell, 4 reps, fresh data, protocol identical to "
                f"stage2; never pooled with any other stage\n")
        out_df.to_csv(f, index=False)
    print(f"wrote {OUT} ({len(out_df)} rows)\n")
    for key in MODELS:
        print(f"--- {key}")
        sub = out_df[(out_df.model == key) & (out_df.section == "refusal")
                     & (out_df.metric.isin(["k_refusal", "n_coded",
                                            "refusal_prop", "wilson_lo",
                                            "wilson_hi"]))]
        print(sub.pivot(index="condition", columns="metric", values="value")
              .reindex(CONDITION_ORDER).to_string())
        ti = out_df[(out_df.model == key) & (out_df.section == "tool_invocation")
                    & (out_df.metric.isin(["exit_rate", "k_exits", "paths"]))]
        print(ti.pivot(index="condition", columns="metric", values="value")
              .reindex(CONDITION_ORDER).to_string())
    print()
    print(out_df[out_df.section.isin(["contrasts", "accounting"])]
          .to_string(index=False))


if __name__ == "__main__":
    main()
