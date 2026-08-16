"""T30 — full outcome composition per model x stage x category x condition.

One row per cell with the complete conversation-code split (a/b/c/d/e) over
coded, non-excluded conversations, plus grade. Feeds figures F4 and F7,
which need the b/c/d split that T24/T26 do not carry. Rows are labeled by
stage and grade and sit side by side; nothing is pooled across stages
(same reporting convention as T8/T9/T27).

Scope: every confirmatory or screen stage with a classified parquet except
stage1 (superseded for every model by a later same-or-better-grade stage or
void for llama4), typearm (superseded), ladder/ladsmoke (probe; T25 covers
the ladder), and quarantined material (never read).

Run: python -m src.composition_table   -> outputs/T30_composition.csv
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

STAGES = {
    "stage2": "confirmatory",
    "stage2b": "confirmatory",
    "llama4_stage2": "confirmatory",
    "cd_conf": "confirmatory",
    "ab_ext": "confirmatory",
    "cd_screen": "screen",
    "screen2": "screen",
}
OUT = ROOT / "outputs" / "T30_composition.csv"


def main():
    cd_cfg = yaml.safe_load((ROOT / "config" / "stimuli_cd.yaml")
                            .read_text(encoding="utf-8"))["stimuli"]
    cd_cat = {s["id"]: s["category"] for s in cd_cfg if not s["ladder"]}
    rows, sources = [], {}
    for stage, grade in STAGES.items():
        p = ROOT / "derived" / f"{stage}_classified.parquet"
        sources[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        df = pd.read_parquet(p)
        df = df[~df["excluded"]].copy()
        if stage in ("cd_conf", "cd_screen"):
            df = df[df["stimulus_id"].isin(cd_cat)]
            df["category"] = df["stimulus_id"].map(cd_cat)
        else:
            df["category"] = df["tier"].map({1: "A", 2: "B"})
        for (model, cat, cond), cell in df.groupby(
                ["model_key", "category", "condition"]):
            codes = cell["conv_code"].dropna().tolist()
            if not codes:
                continue
            rows.append({
                "model": model, "stage": stage, "grade": grade,
                "category": cat, "condition": cond, "n_coded": len(codes),
                **{f"k_{c}": sum(1 for x in codes if x == c)
                   for c in "abcde"},
            })
    out = pd.DataFrame(rows).sort_values(
        ["model", "stage", "category", "condition"])
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T30_composition | generated {utcnow()} | sources "
                + " ".join(f"derived/{k}={v}" for k, v in sorted(sources.items()))
                + " | full a/b/c/d/e split per model x stage x category x "
                  "condition, coded non-excluded conversations; rows are "
                  "stage-labeled and never pooled; stage1/typearm/ladder/"
                  "quarantine excluded (superseded, probe, or sequestered)\n")
        out.to_csv(f, index=False)
    print(f"wrote {OUT} ({len(out)} rows) — models: "
          f"{sorted(out.model.unique())}")


if __name__ == "__main__":
    main()
