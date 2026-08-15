"""B5 — combined escape rate (SECONDARY measure; the primary DV is unchanged).

Combined escape = proportion of conversations containing EITHER a verbal
refusal (codes b/c/d) OR a tool exit (code a), per model x condition, stage-2
confirmatory data. Refusal and tool exit remain separate for the primary DV
(§8: code a never enters it); this table is an additional, clearly-labeled
secondary view that treats "took any escape hatch" as one outcome. By §8
coding a conversation cannot be both (any exit -> code a), so combined =
refusal_rate + exit_rate.

Output: outputs/T15_combined_escape.csv
Run: python -m src.combined_escape
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, utcnow

OUT = ROOT / "outputs"
COND_ORDER = ["none", "time_schema", "note_schema", "exit_schema",
              "exit_prose", "exit_both"]


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return round(c - h, 4), round(c + h, 4)


def main():
    src = ROOT / "derived" / "stage2_classified.parquet"
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    df = pd.read_parquet(src)
    df = df[~df.excluded]

    rows = []
    for model in sorted(df.model_key.unique()):
        for cond in COND_ORDER:
            cell = df[(df.model_key == model) & (df.condition == cond)]
            n = len(cell)
            k_ref = int(cell.contains_refusal.sum())
            k_exit = int(cell["exit"].sum())
            k_comb = int((cell.contains_refusal | cell["exit"]).sum())
            lo, hi = wilson_ci(k_comb, n)
            rows.append({
                "model": model, "condition": cond, "n": n,
                "refusal_k": k_ref,
                "refusal_rate": round(k_ref / n, 4),
                "tool_exit_k": k_exit,
                "tool_exit_rate": round(k_exit / n, 4),
                "combined_escape_k": k_comb,
                "combined_escape_rate": round(k_comb / n, 4),
                "combined_ci_lo": lo, "combined_ci_hi": hi,
            })
    out = pd.DataFrame(rows)
    p = OUT / "T15_combined_escape.csv"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T15_combined_escape | generated {utcnow()} | source "
                f"derived/stage2_classified.parquet sha256={digest} | "
                f"SECONDARY measure: refusal (b/c/d) OR tool exit (a); "
                f"primary DV (T1) and tool-exit table (T3) unchanged and "
                f"never pooled | Wilson 95% CI on the combined rate\n")
        out.to_csv(f, index=False)
    print(f"wrote {p} ({len(out)} rows)")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
