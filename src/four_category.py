"""four_category_v1 — the ONE sanctioned cross-stage read in the study.

Declared in METHODOLOGY §10 (2026-08-16, Part 3) BEFORE the C/D data were
collected. It combines DIFFERENT stimuli collected under identical protocol
and identical pins into a per-model four-category table:

  A - promotional slop     (tier-1 cells of the model's confirmatory A/B stage)
  B - mechanical keyed     (tier-2 cells of the same stage)
  C - tedious conversion/sorting  (stage cd_conf, category C, n=20)
  D - creative generation         (stage cd_conf, category D, n=20)

The stage allowlist is enforced IN CODE below: exactly these labels, one
source stage per (model, A/B), cd_conf only for C/D, everything else
refused. §7's never-pool rule (stage-1 vs extension samples of the SAME
stimuli) is untouched: no stage-1 row enters, and no model's cells are drawn
from two stages for the same category. Pooled figures are emitted ONLY
alongside the category breakdown, never instead of it.

Run: python -m src.four_category      # outputs/T24_four_category_v1.csv
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

# The declared allowlist. Any other stage label in any input frame is a
# hard error, not a warning.
AB_SOURCE = {
    "qwen3_235b": "stage2",
    "gemini25_flash": "stage2",
    "gemma3_27b": "stage2",
    "sonnet46": "stage2b",
    "gpt5_mini": "stage2b",
    "llama4_maverick": "llama4_stage2",
}
CD_STAGE = "cd_conf"
ALLOWED_STAGES = set(AB_SOURCE.values()) | {CD_STAGE}

OUT = ROOT / "outputs" / "T24_four_category_v1.csv"


def sha256(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def load_frames():
    frames = {}
    for stage in sorted(ALLOWED_STAGES):
        p = ROOT / "derived" / f"{stage}_classified.parquet"
        df = pd.read_parquet(p)
        bad = set(df["stage"].unique()) - ALLOWED_STAGES
        if bad:
            raise SystemExit(f"REFUSED: stage labels {bad} in {p.name} are "
                             f"outside the four_category_v1 allowlist")
        frames[stage] = df[~df["excluded"]].copy()
    return frames


def categorize(frames):
    cd_cfg = yaml.safe_load((ROOT / "config" / "stimuli_cd.yaml")
                            .read_text(encoding="utf-8"))["stimuli"]
    cd_cat = {s["id"]: s["category"] for s in cd_cfg}
    cd_n20 = {s["id"] for s in cd_cfg if not s["ladder"]}
    rows = []
    for model, stage in AB_SOURCE.items():
        d = frames[stage]
        d = d[d["model_key"] == model].copy()
        if d.empty:
            raise SystemExit(f"REFUSED: no rows for {model} in {stage}")
        d["category"] = d["tier"].map({1: "A", 2: "B"})
        rows.append(d)
        cd = frames[CD_STAGE]
        cd = cd[(cd["model_key"] == model)
                & (cd["stimulus_id"].isin(cd_n20))].copy()
        if cd.empty:
            raise SystemExit(f"REFUSED: no cd_conf rows for {model}")
        cd["category"] = cd["stimulus_id"].map(cd_cat)
        rows.append(cd)
    df = pd.concat(rows, ignore_index=True)
    # one source stage per (model, category) — pooling guard in code
    src = df.groupby(["model_key", "category"])["stage"].nunique()
    if (src > 1).any():
        raise SystemExit(f"REFUSED: multiple source stages for "
                         f"{src[src > 1].index.tolist()}")
    return df


def main():
    frames = load_frames()
    df = categorize(frames)
    rows = []
    for model in AB_SOURCE:
        d = df[df["model_key"] == model]
        for cat in ["A", "B", "C", "D"]:
            for cond in CONDITION_ORDER:
                cell = d[(d["category"] == cat) & (d["condition"] == cond)]
                codes = cell["conv_code"].dropna().tolist()
                if not codes:
                    continue
                k = sum(1 for c in codes if c in REFUSAL_CODES)
                kc = sum(1 for c in codes if c == "c")
                n = len(codes)
                lo, hi = wilson(k, n)
                cf = cell[cell["conv_code"] == "e"]["completion_fraction"].dropna()
                rows.append({
                    "model": model, "category": cat, "condition": cond,
                    "source_stage": cell["stage"].iloc[0],
                    "n": n, "k_refusal": k,
                    "refusal_prop": round(primary_dv(codes), 4),
                    "wilson_lo": round(lo, 4), "wilson_hi": round(hi, 4),
                    "k_code_c": kc,
                    "k_exits": int(cell["exit"].sum()),
                    "completion_median": (round(float(cf.median()), 4)
                                          if len(cf) else None),
                    "n_compliant": len(cf),
                    "grade": "confirmatory_120_per_cell_cat" if n >= 100
                             else f"n={n}",
                    "row_kind": "category",
                })
        # pooled row, only alongside the breakdown above
        for cond in CONDITION_ORDER:
            cell = d[d["condition"] == cond]
            codes = cell["conv_code"].dropna().tolist()
            if not codes:
                continue
            k = sum(1 for c in codes if c in REFUSAL_CODES)
            lo, hi = wilson(k, len(codes))
            rows.append({
                "model": model, "category": "ABCD_pooled",
                "condition": cond, "source_stage": "join",
                "n": len(codes), "k_refusal": k,
                "refusal_prop": round(primary_dv(codes), 4),
                "wilson_lo": round(lo, 4), "wilson_hi": round(hi, 4),
                "k_code_c": sum(1 for c in codes if c == "c"),
                "k_exits": int(cell["exit"].sum()),
                "completion_median": None, "n_compliant": None,
                "grade": "pooled - read only with the category rows above",
                "row_kind": "pooled",
            })
    out_df = pd.DataFrame(rows)
    srcs = " + ".join(f"derived/{s}_classified.parquet sha256={sha256(ROOT / 'derived' / (s + '_classified.parquet'))[:16]}"
                      for s in sorted(ALLOWED_STAGES))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T24_four_category_v1 | generated {utcnow()} | sources "
                f"{srcs} + config/stimuli_cd.yaml | THE one sanctioned "
                f"cross-stage read (declared in §10 before C/D collection); "
                f"stage allowlist enforced in code; pooled rows valid only "
                f"alongside category rows; stage-1 data never enters\n")
        out_df.to_csv(f, index=False)
    print(f"wrote {OUT} ({len(out_df)} rows)")
    piv = out_df[out_df.row_kind == "category"].pivot_table(
        index=["model", "category"], columns="condition",
        values="refusal_prop", aggfunc="first").reindex(columns=CONDITION_ORDER)
    print(piv.to_string())


if __name__ == "__main__":
    main()
