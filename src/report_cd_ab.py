"""Part 4 items 3+4 report — outputs/T26_gptoss_deepseek.csv.

gpt_oss_120b and deepseek_chat across all four categories:
  A/B from stage ab_ext (confirmatory, 120/cell-category after 4 reps x 30
      stimuli — the extension closing the last sample-size asymmetry among
      the original eight; never pooled with their stage-1 data)
  C/D from stage cd_screen (screen grade, 2 reps x 9 stimuli/category)

Grades are labeled on every row; screen-grade C/D never sits beside the
confirmatory A/B numbers without its grade column saying so.

Run: python -m src.report_cd_ab
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

import pandas as pd
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, utcnow
from frozen import CONDITION_ORDER
from coding import primary_dv, REFUSAL_CODES
from analyze import wilson

MODELS = ["gpt_oss_120b", "deepseek_chat"]
OUT = ROOT / "outputs" / "T26_gptoss_deepseek.csv"


def sha256(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def main():
    cd_cfg = yaml.safe_load((ROOT / "config" / "stimuli_cd.yaml")
                            .read_text(encoding="utf-8"))["stimuli"]
    cd_cat = {s["id"]: s["category"] for s in cd_cfg if not s["ladder"]}
    ab = pd.read_parquet(ROOT / "derived" / "ab_ext_classified.parquet")
    cd = pd.read_parquet(ROOT / "derived" / "cd_screen_classified.parquet")
    ab["category"] = ab["tier"].map({1: "A", 2: "B"})
    cd = cd[cd["stimulus_id"].isin(cd_cat)]
    cd["category"] = cd["stimulus_id"].map(cd_cat)
    rows = []
    for model in MODELS:
        for df, grade in ((ab, "confirmatory 4-rep (ab_ext)"),
                          (cd, "screen 2-rep (cd_screen)")):
            d = df[(df["model_key"] == model) & (~df["excluded"])]
            for cat in sorted(d["category"].unique()):
                for cond in CONDITION_ORDER:
                    cell = d[(d["category"] == cat)
                             & (d["condition"] == cond)]
                    codes = cell["conv_code"].dropna().tolist()
                    if not codes:
                        continue
                    k = sum(1 for c in codes if c in REFUSAL_CODES)
                    lo, hi = wilson(k, len(codes))
                    cf = cell[cell["conv_code"] == "e"]["completion_fraction"].dropna()
                    rows.append({
                        "model": model, "category": cat, "condition": cond,
                        "grade": grade, "n": len(codes), "k_refusal": k,
                        "refusal_prop": round(primary_dv(codes), 4),
                        "wilson_lo": round(lo, 4), "wilson_hi": round(hi, 4),
                        "k_code_c": sum(1 for c in codes if c == "c"),
                        "k_exits": int(cell["exit"].sum()),
                        "completion_median": (round(float(cf.median()), 4)
                                              if len(cf) else None),
                    })
        # exclusion + pin accounting per model per stage
        for df, stage in ((ab, "ab_ext"), (cd, "cd_screen")):
            d = df[df["model_key"] == model]
            rows.append({"model": model, "category": "ALL",
                         "condition": "ALL", "grade": f"accounting {stage}",
                         "n": len(d),
                         "k_refusal": int(d["excluded"].sum()),
                         "refusal_prop": "",
                         "wilson_lo": "", "wilson_hi": "",
                         "k_code_c": int(d["provider_ok"].sum()),
                         "k_exits": "", "completion_median": None})
    out_df = pd.DataFrame(rows)
    srcs = " + ".join(
        f"derived/{s}_classified.parquet sha256={sha256(ROOT / 'derived' / (s + '_classified.parquet'))[:16]}"
        for s in ("ab_ext", "cd_screen"))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T26_gptoss_deepseek | generated {utcnow()} | sources "
                f"{srcs} | A/B confirmatory extension (never pooled with "
                f"stage-1), C/D screen grade; accounting rows: k_refusal "
                f"column = excluded count, k_code_c column = pin-ok count\n")
        out_df.to_csv(f, index=False)
    print(f"wrote {OUT} ({len(out_df)} rows)\n")
    body = out_df[~out_df.grade.str.startswith("accounting")]
    print(body.pivot_table(index=["model", "category"], columns="condition",
                           values="refusal_prop", aggfunc="first")
          .reindex(columns=CONDITION_ORDER).to_string())
    print()
    print(out_df[out_df.grade.str.startswith("accounting")].to_string(index=False))


if __name__ == "__main__":
    main()
