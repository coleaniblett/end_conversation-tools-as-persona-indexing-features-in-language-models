"""T27 — cell census: model x category x size x stage with n and grade.

One row per (model, stage, category, requested size): total conversations,
non-excluded, coded, grade. Makes every remaining sample-size asymmetry
visible at a glance. Reads every non-quarantined classified parquet.

Run: python -m src.cell_census    -> outputs/T27_cell_census.csv
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

import pandas as pd
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, utcnow

GRADES = {
    "ab_ext": "confirmatory 120/cell (extension; never pooled with stage1)",
    "stage1": "screen 60/cell",
    "stage2": "confirmatory 120/cell",
    "stage2b": "confirmatory 120/cell",
    "llama4_vertex": "screen 60/cell (clean re-run)",
    "llama4_stage2": "confirmatory 120/cell",
    "typearm": "probe n=2/cell (SUPERSEDED by C/D)",
    "screen2": "screen 60/cell",
    "cd_conf": "confirmatory 36/cell-category-condition (9 stim x 4 reps)",
    "cd_screen": "screen 18/cell-category-condition (9 stim x 2 reps)",
    "ladder": "probe 6/cell (3 stim x 2 reps), never pooled",
    "ladsmoke": "smoke probe, never pooled",
}
OUT = ROOT / "outputs" / "T27_cell_census.csv"


def main():
    cd_cfg = yaml.safe_load((ROOT / "config" / "stimuli_cd.yaml")
                            .read_text(encoding="utf-8"))["stimuli"]
    cd_cat = {s["id"]: s["category"] for s in cd_cfg}
    tt_ids = {s["id"] for s in yaml.safe_load(
        (ROOT / "config" / "stimuli_tasktype.yaml")
        .read_text(encoding="utf-8"))["stimuli"]}
    rows, sources = [], {}
    for p in sorted((ROOT / "derived").glob("*_classified.parquet")):
        stage = p.stem.replace("_classified", "")
        sources[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        df = pd.read_parquet(p)
        df = df.copy()
        if "requested_items" in df.columns:
            df["size"] = df["requested_items"]
        else:
            df["size"] = 20
        # requested size lives in the stimulus config for cd/ladder stages
        n_by_stim = {s["id"]: s["requested_items"] for s in cd_cfg}
        df["size"] = df["stimulus_id"].map(n_by_stim).fillna(20).astype(int)
        def cat(r):
            if r["stimulus_id"] in cd_cat:
                return cd_cat[r["stimulus_id"]]
            if r["stimulus_id"] in tt_ids:
                return "typearm(superseded)"
            return "A" if r["tier"] == 1 else "B"
        df["category"] = df.apply(cat, axis=1)
        g = (df.groupby(["model_key", "category", "size"])
             .agg(n_total=("conversation_id", "count"),
                  n_excluded=("excluded", "sum"),
                  n_coded=("conv_code", lambda s: s.notna().sum()))
             .reset_index())
        g.insert(0, "stage", stage)
        g["grade"] = GRADES.get(stage, "?")
        rows.append(g)
    out = pd.concat(rows, ignore_index=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T27_cell_census | generated {utcnow()} | sources "
                + " ".join(f"{k}={v}" for k, v in sorted(sources.items()))
                + " | one row per model x stage x category x requested size; "
                  "n_total incl. excluded; quarantined data not read\n")
        out.to_csv(f, index=False)
    print(f"wrote {OUT} ({len(out)} rows)")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
