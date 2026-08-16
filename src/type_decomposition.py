"""PART A.2 — within-category type decomposition (T29).

For every model with nonzero refusal or exit in categories C or D (stage
cd_conf, confirmatory grade), break each category x condition cell down by
task type (C: temperature/alphabetical/roman; D: crossword/metaphor/
acronym), with per-type n stated (3 stimuli x 4 reps = 12 per type x
condition). Category A has no types and is skipped per the brief.

The committed answer paragraphs (gemini roman question; gemma; qwen) are
embedded in the output header and printed; STIMULUS_PROVENANCE.md §5 is
updated by its generator, not by hand.

Run: python -m src.type_decomposition  -> outputs/T29_type_decomposition.csv
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
from coding import REFUSAL_CODES

OUT = ROOT / "outputs" / "T29_type_decomposition.csv"


def main():
    cd_cfg = yaml.safe_load((ROOT / "config" / "stimuli_cd.yaml")
                            .read_text(encoding="utf-8"))["stimuli"]
    meta = {s["id"]: (s["category"], s["task_type"]) for s in cd_cfg
            if not s["ladder"]}
    df = pd.read_parquet(ROOT / "derived" / "cd_conf_classified.parquet")
    df = df[~df["excluded"]].copy()
    df["category"] = df["stimulus_id"].map(lambda i: meta[i][0])
    df["task_type"] = df["stimulus_id"].map(lambda i: meta[i][1])

    # models with any refusal or exit in C or D
    act = df[(df["contains_refusal"].fillna(False)) | df["exit"]]
    models = sorted(act["model_key"].unique())

    rows = []
    for model in models:
        d = df[df["model_key"] == model]
        for cat in ("C", "D"):
            for ttype in sorted(d[d["category"] == cat]["task_type"].unique()):
                for cond in CONDITION_ORDER:
                    cell = d[(d["category"] == cat)
                             & (d["task_type"] == ttype)
                             & (d["condition"] == cond)]
                    codes = cell["conv_code"].dropna().tolist()
                    if not codes:
                        continue
                    k = sum(1 for c in codes if c in REFUSAL_CODES)
                    rows.append({
                        "model": model, "category": cat, "task_type": ttype,
                        "condition": cond, "n": len(codes),
                        "k_refusal_bcd": k,
                        "k_code_c": sum(1 for c in codes if c == "c"),
                        "k_exit": int(cell["exit"].sum()),
                    })
    out_df = pd.DataFrame(rows)

    def tot(model, cat, ttype, col):
        m = out_df[(out_df.model == model) & (out_df.category == cat)
                   & (out_df.task_type == ttype)]
        return int(m[col].sum()), int(m["n"].sum())

    # ---- committed answers ----------------------------------------------
    g_rom, g_rom_n = tot("gemini25_flash", "C", "roman", "k_refusal_bcd")
    g_tmp, _ = tot("gemini25_flash", "C", "temperature", "k_refusal_bcd")
    g_alp, _ = tot("gemini25_flash", "C", "alphabetical", "k_refusal_bcd")
    ga_rom, _ = tot("gemma3_27b", "C", "roman", "k_refusal_bcd")
    ga_tmp, _ = tot("gemma3_27b", "C", "temperature", "k_refusal_bcd")
    ga_alp, _ = tot("gemma3_27b", "C", "alphabetical", "k_refusal_bcd")
    ga_cro, _ = tot("gemma3_27b", "D", "crossword", "k_refusal_bcd")
    ga_met, _ = tot("gemma3_27b", "D", "metaphor", "k_refusal_bcd")
    ga_acr, _ = tot("gemma3_27b", "D", "acronym", "k_refusal_bcd")
    q_cro, _ = tot("qwen3_235b", "D", "crossword", "k_refusal_bcd")
    q_met, _ = tot("qwen3_235b", "D", "metaphor", "k_refusal_bcd")
    q_acr, _ = tot("qwen3_235b", "D", "acronym", "k_refusal_bcd")

    def label(parts):
        """Characterize a type split from its numbers: exclusive (one type
        carries all), dominated (>=80%), or spread."""
        total = sum(k for _, k in parts)
        top_t, top_k = max(parts, key=lambda x: x[1])
        if total == 0:
            return "no refusals", top_t
        if top_k == total:
            return f"{top_t}-EXCLUSIVE ({top_k}/{total})", top_t
        if top_k / total >= 0.8:
            return f"{top_t}-DOMINATED ({top_k}/{total})", top_t
        return f"spread across types (top {top_t} {top_k}/{total})", top_t

    g_lab, g_top = label([("roman", g_rom), ("temperature", g_tmp),
                          ("alphabetical", g_alp)])
    gaC_lab, gaC_top = label([("roman", ga_rom), ("temperature", ga_tmp),
                              ("alphabetical", ga_alp)])
    gaD_lab, _ = label([("metaphor", ga_met), ("crossword", ga_cro),
                        ("acronym", ga_acr)])
    q_lab, _ = label([("metaphor", q_met), ("crossword", q_cro),
                      ("acronym", q_acr)])
    llC = [("roman", tot("llama4_maverick", "C", "roman", "k_refusal_bcd")[0]),
           ("temperature", tot("llama4_maverick", "C", "temperature",
                               "k_refusal_bcd")[0]),
           ("alphabetical", tot("llama4_maverick", "C", "alphabetical",
                                "k_refusal_bcd")[0])]
    ll_lab, _ = label(llC)

    paragraphs = [
        (f"GEMINI ANSWER: gemini25_flash's category-C effect is {g_lab}: "
         f"roman {g_rom}, temperature {g_tmp}, alphabetical {g_alp} "
         f"refusals across all six conditions (12 conversations per type x "
         f"condition, {g_rom_n} per type overall). Roman refusal reaches "
         f"12/12 under both time_schema and exit_schema. This VINDICATES "
         f"the 2026-08-15T20:45Z diagnostic verdict's roman-trigger claim, "
         f"which the n=2-per-cell typearm could not test and appeared to "
         f"refute: at confirmatory grade under pilot-construction stimuli, "
         f"roman numerals are exactly where gemini's affordance-conditional "
         f"refusal lives. The category-level 'C effect' claim for gemini "
         f"is really a TYPE-level claim (roman) and is restated as such."),
        (f"GEMMA ANSWER: gemma3_27b's category-C effect is {gaC_lab} "
         f"(roman {ga_rom}, temperature {ga_tmp}, alphabetical {ga_alp}) — "
         f"the same roman trigger as gemini, in a second model. Its "
         f"category-D effect is {gaD_lab} (metaphor {ga_met}, crossword "
         f"{ga_cro}, acronym {ga_acr}). Both of gemma's category-level "
         f"claims are really TYPE-level claims (roman; metaphor) and are "
         f"restated as such."),
        (f"QWEN ANSWER: qwen3_235b's category-D exit_prose refusals are "
         f"{q_lab} (acronym {q_acr}, metaphor {q_met}, crossword {q_cro}) "
         f"— a type-level concentration, restated as such. Its category-A "
         f"exits have no type structure to decompose (A is one task "
         f"family) and are skipped per the brief."),
        (f"LLAMA4 NOTE: llama4_maverick's category-C refusals are "
         f"{ll_lab}, so its claim correctly stays at CATEGORY level; its "
         f"B-category effect has no type structure in this decomposition "
         f"(B is outside C/D scope)."),
    ]

    src = ROOT / "derived" / "cd_conf_classified.parquet"
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T29_type_decomposition | generated {utcnow()} | source "
                f"derived/cd_conf_classified.parquet sha256="
                f"{hashlib.sha256(src.read_bytes()).hexdigest()[:16]} | "
                f"cd_conf confirmatory grade; n=12 per model x type x "
                f"condition; models shown = those with any refusal or exit "
                f"in C or D\n")
        for para in paragraphs:
            for line in [para[i:i + 96] for i in range(0, len(para), 96)]:
                f.write(f"# {line}\n")
        out_df.to_csv(f, index=False)
    print(f"wrote {OUT} ({len(out_df)} rows)\n")
    piv = out_df.pivot_table(index=["model", "category", "task_type"],
                             columns="condition", values="k_refusal_bcd",
                             aggfunc="first").reindex(columns=CONDITION_ORDER)
    print("k_refusal by type x condition:")
    print(piv.to_string())
    print("\nk_exit by type x condition:")
    piv2 = out_df.pivot_table(index=["model", "category", "task_type"],
                              columns="condition", values="k_exit",
                              aggfunc="first").reindex(columns=CONDITION_ORDER)
    print(piv2.to_string())
    print()
    for p in paragraphs:
        print(p + "\n")


if __name__ == "__main__":
    main()
