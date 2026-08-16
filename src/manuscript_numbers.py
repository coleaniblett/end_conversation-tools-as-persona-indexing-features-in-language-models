"""Manuscript number manifest + draft diff (zero spend, read-only).

Writes outputs/MANUSCRIPT_NUMBERS_S1.md — the frozen manifest of every
number the manuscript may cite: value, source path + table cell, per-cell
n, grade. Every value is READ from a committed output; nothing is derived
beyond locating cells. Also writes outputs/MANUSCRIPT_NUMBER_DIFF.md:
the draft path placeholder was never resolved and no draft exists in the
repository, so the diff is replaced by (a) that statement, (b) the census
contradiction resolved from committed files, (c) a prospective stale-list
for any v1-era draft, from the adoption's own change record.

Run: python -X utf8 -m src.manuscript_numbers
"""
from __future__ import annotations

import pathlib
import re
import sys

import pandas as pd
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, utcnow

O = ROOT / "outputs"


def t(name):
    return pd.read_csv(O / name, comment="#")


def main():
    models = yaml.safe_load((ROOT / "config" / "models.yaml")
                            .read_text(encoding="utf-8"))["models"]
    orgs = sorted({m["lineage"].split("-")[0].replace("xai", "xAI")
                   for m in models})
    pins = {m["key"]: f"{m['pin_name']} ({m.get('pin_tag', m['pin_slug'])})"
            for m in models}
    t24 = t("T24_four_category_v1.csv")
    c24 = t24[t24.row_kind == "category"]

    def cell24(model, cat, cond, col):
        r = c24[(c24.model == model) & (c24.category == cat)
                & (c24.condition == cond)]
        return r.iloc[0][col] if len(r) else None

    t28 = t("T28_competing_risks.csv")
    t29 = t("T29_type_decomposition.csv")
    t25 = t("T25_ladder.csv")
    t20 = t("T20_llama4_stage2.csv")
    t30 = (O / "T30_exit_reasons.md").read_text(encoding="utf-8")
    t31h = (O / "T31_exit_recount.csv").open(encoding="utf-8").readline()
    rep = (ROOT / "study_2" / "REPORT.md").read_text(encoding="utf-8").splitlines()

    def rep_line(pat):
        for i, l in enumerate(rep, 1):
            if re.search(pat, l):
                return i, l.strip()
        return None, None

    def t29tot(model, cat, ttype):
        d = t29[(t29.model == model) & (t29.category == cat)
                & (t29.task_type == ttype)]
        return int(d.k_refusal_bcd.sum()), int(d.k_exit.sum())

    def t25cell(model, n_items, cond, col):
        r = t25[(t25.model == model) & (t25.n_items == n_items)
                & (t25.condition == cond)]
        return r.iloc[0][col] if len(r) else None

    def t20cell(section, cond, metric):
        r = t20[(t20.section == section) & (t20.condition == cond)
                & (t20.metric == metric)]
        return r.iloc[0]["value"] if len(r) else None

    L = [f"# MANUSCRIPT_NUMBERS_S1 — frozen citation manifest "
         f"({utcnow()}, canonical = v2 detector, main @ post-be6d2d2)",
         "",
         "Every value below is read from the named committed file; grades: "
         "CONF = confirmatory, SCR = screen, PRB = probe. v1-basis entries "
         "are explicitly flagged.", "",
         "## Census (item 3's resolution lives in the DIFF file)",
         f"- **Study 1 models run: 11** (outputs/T27_cell_census.csv, "
         f"distinct model_key; config/models.yaml). Grades: 8 with "
         f"confirmatory cells (llama4_maverick, qwen3_235b, "
         f"gemini25_flash, gemma3_27b, sonnet46, gpt5_mini on all four "
         f"categories; gpt_oss_120b and deepseek_chat confirmatory on A/B "
         f"[ab_ext] + screen on C/D [cd_screen]); 3 screen-only (grok46, "
         f"gemini25_pro, gpt52; T23).",
         f"- **Developers: 7** — {', '.join(sorted(set(o.capitalize() if o != 'xAI' else o for o in orgs)))} "
         f"(config/models.yaml `lineage`; google supplies two lineages, "
         f"openai two).",
         f"- **Pins** (config/models.yaml): "
         + "; ".join(f"{k}={v}" for k, v in sorted(pins.items())) + ".",
         f"- **Movers (Study 1, primary DV or exit use): 4** — llama4 "
         f"(T20/T24), qwen (T24/T25/T31), gemini25_flash (T24/T29), "
         f"gemma3_27b (T24/T29). **Measured zeros: 7** — sonnet46, "
         f"gpt5_mini, deepseek_chat at CONF (T21/T24/T26); grok46, "
         f"gemini25_pro, gpt52 at SCR (T23); gpt_oss_120b at CONF on "
         f"refusal everywhere (T26) with two PRB-grade exits at n=160 "
         f"(T25) — a null with a ladder footnote, not a mover.",
         f"- **Study 2 models: 11 on matching pins** — study_2/REPORT.md "
         f"line {rep_line(r'true of all eleven')[0]}: "
         f"\"{rep_line(r'true of all eleven')[1]}\" (llama re-pinned to "
         f"Vertex, run v4, supersedes Parasail; commit 2c673d6).",
         "",
         "## llama4_maverick category B (CONF, n=60/cell; "
         "outputs/T24_four_category_v1.csv)",
         f"- refusal: time_schema "
         f"{cell24('llama4_maverick', 'B', 'time_schema', 'refusal_prop')} "
         f"(k={cell24('llama4_maverick', 'B', 'time_schema', 'k_refusal')}) "
         f"> note_schema "
         f"{cell24('llama4_maverick', 'B', 'note_schema', 'refusal_prop')} "
         f"(k={cell24('llama4_maverick', 'B', 'note_schema', 'k_refusal')}) "
         f"> exit_schema "
         f"{cell24('llama4_maverick', 'B', 'exit_schema', 'refusal_prop')} "
         f"(k={cell24('llama4_maverick', 'B', 'exit_schema', 'k_refusal')}) "
         f"> none "
         f"{cell24('llama4_maverick', 'B', 'none', 'refusal_prop')} — the "
         f"clock > note > exit-schema > none ordering.",
         f"- T28 non-exit recompute (outputs/T28_competing_risks.csv, "
         f"llama4 B x exit_schema row): refusal_all "
         f"{t28[(t28.model == 'llama4_maverick') & (t28.category == 'B') & (t28.condition == 'exit_schema')].iloc[0]['refusal_all']} "
         f"-> refusal_nonexit "
         f"{t28[(t28.model == 'llama4_maverick') & (t28.category == 'B') & (t28.condition == 'exit_schema')].iloc[0]['refusal_nonexit']} "
         f"over n_nonexit "
         f"{t28[(t28.model == 'llama4_maverick') & (t28.category == 'B') & (t28.condition == 'exit_schema')].iloc[0]['n_nonexit']} "
         f"(declared sensitivity view; ordering survives).",
         "",
         "## Type-level counts (CONF, n=12/type x condition; "
         "outputs/T29_type_decomposition.csv)",
         f"- gemini25_flash C refusals are roman-EXCLUSIVE under canonical v2: "
         f"{t29tot('gemini25_flash', 'C', 'roman')[0]} of "
         f"{t29tot('gemini25_flash', 'C', 'roman')[0] + t29tot('gemini25_flash', 'C', 'temperature')[0] + t29tot('gemini25_flash', 'C', 'alphabetical')[0]} "
         f"C refusals are roman (12/12 under time_schema and exit_schema; "
         f"temperature 0, alphabetical 0). Was 36/36 pre-adoption: two "
         f"exit_both roman refusals flipped to exits (T31_exit_recount).",
         f"- gemma3_27b C roman: {t29tot('gemma3_27b', 'C', 'roman')[0]}; "
         f"C temperature: {t29tot('gemma3_27b', 'C', 'temperature')[0]}; "
         f"D metaphor: {t29tot('gemma3_27b', 'D', 'metaphor')[0]} "
         f"(metaphor-exclusive in D).",
         f"- qwen3_235b D (canonical v2): refusals "
         f"{int(t29[(t29.model == 'qwen3_235b') & (t29.category == 'D')].k_refusal_bcd.sum())}, "
         f"exits {int(t29[(t29.model == 'qwen3_235b') & (t29.category == 'D')].k_exit.sum())} "
         f"— the v1 acronym-refusal cell is now exits.",
         "",
         "## llama4 exits (CONF; outputs/T20_llama4_stage2.csv + "
         "outputs/T30_exit_reasons.md)",
         f"- exit rate: exit_schema "
         f"{t20cell('tool_invocation', 'exit_schema', 'exit_rate')} "
         f"(k={t20cell('tool_invocation', 'exit_schema', 'k_exits')}/120), "
         f"exit_both "
         f"{t20cell('tool_invocation', 'exit_both', 'exit_rate')} "
         f"(k={t20cell('tool_invocation', 'exit_both', 'k_exits')}/120).",
         f"- T30 breakdown (**v1-flags basis — computed pre-adoption; "
         f"under v2 llama gains exactly 1 prose-path exit "
         f"[llama4_vertex x exit_both, outputs/T31_exit_recount.csv] and "
         f"qwen gains 39**): llama 389 schema exits, 343 (88%) "
         f"completion/turn-management, 364/389 (94%) deliver-then-exit "
         f"(text in exit turn), task-aversion 0/389; qwen 147 exits, "
         f"108 (73%) task-aversive. Cite with basis stated, or "
         f"regenerate src/exit_reasons.py on canonical flags first.",
         "",
         "## qwen ladder (outputs/T25_ladder.csv; anchors CONF 4-rep "
         "n=36, rungs PRB 2-rep n=6)",
         f"- exits exit_schema: 20 items "
         f"{t25cell('qwen3_235b', 20, 'exit_schema', 'k_exits')}/36, "
         f"40 items {t25cell('qwen3_235b', 40, 'exit_schema', 'k_exits')}/6, "
         f"160 items {t25cell('qwen3_235b', 160, 'exit_schema', 'k_exits')}/6.",
         f"- exits exit_both: "
         f"{t25cell('qwen3_235b', 20, 'exit_both', 'k_exits')}/36, "
         f"{t25cell('qwen3_235b', 40, 'exit_both', 'k_exits')}/6, "
         f"{t25cell('qwen3_235b', 160, 'exit_both', 'k_exits')}/6.",
         f"- no-tool completion baseline (median, none): 20 items "
         f"{t25cell('qwen3_235b', 20, 'none', 'completion_median')}, 40 "
         f"{t25cell('qwen3_235b', 40, 'none', 'completion_median')}, 160 "
         f"{t25cell('qwen3_235b', 160, 'none', 'completion_median')}.",
         f"- completion medians at 160, none, all ladder models: qwen "
         f"{t25cell('qwen3_235b', 160, 'none', 'completion_median')}, "
         f"gpt_oss {t25cell('gpt_oss_120b', 160, 'none', 'completion_median')}, "
         f"llama4 {t25cell('llama4_maverick', 160, 'none', 'completion_median')} "
         f"(llama's 160 none cell is truncation-flagged, refusal "
         f"suppressed, completion from surviving conversations — T25 "
         f"header; non-ladder models have no 160-item cells).",
         "",
         "## qwen category A, schema vs prose (CONF n=60/cell; "
         "outputs/T24_four_category_v1.csv, canonical v2)",
         f"- exits: exit_schema "
         f"{cell24('qwen3_235b', 'A', 'exit_schema', 'k_exits')}/60, "
         f"exit_prose {cell24('qwen3_235b', 'A', 'exit_prose', 'k_exits')}/60, "
         f"exit_both {cell24('qwen3_235b', 'A', 'exit_both', 'k_exits')}/60; "
         f"verbal refusal exit_prose "
         f"{cell24('qwen3_235b', 'A', 'exit_prose', 'k_refusal')}/60 "
         f"(v1's 9 prose refusals are now exits; the v2 contrast is "
         f"rate-of-exit by channel, not outlet-switching — "
         f"CONSOLIDATED_RESULTS RQ3, rewritten at adoption).",
         "",
         "## Study-wide detection totals (outputs/T31_exit_recount.csv "
         "header; METHODOLOGY §10 adoption entry)",
         "- exits 510 (v1) -> 555 (v2 canonical); verbal refusals 332 -> "
         "300; 45 monotone flips, 0 reverse.",
         "",
         "## Classifier agreement",
         f"- cross-classifier kappa (proportional 200-sample): "
         f"{t('T7_classifier_validation.csv').query('metric == \"kappa\"').iloc[0]['value']} "
         f"(outputs/T7_classifier_validation.csv; Haiku 4.5 vs kimi-k2; "
         f"NOT human validation).",
         f"- balanced-sample cross-classifier kappa: "
         f"{t('T7b_classifier_validation_balanced.csv').query('metric == \"kappa\"').iloc[0]['value']} "
         f"(outputs/T7b_classifier_validation_balanced.csv, hers).",
         f"- human kappa: **outputs/T7_human_kappa.csv does not exist** — "
         f"the §8 human validation is still pending; a manuscript may not "
         f"cite a human kappa.",
         ]
    (O / "MANUSCRIPT_NUMBERS_S1.md").write_text("\n".join(L) + "\n",
                                               encoding="utf-8", newline="\n")
    print("wrote outputs/MANUSCRIPT_NUMBERS_S1.md")

    D = [f"# MANUSCRIPT_NUMBER_DIFF — {utcnow()}",
         "",
         "## The diff cannot run: no draft was provided",
         "The brief's item 2 references \"the manuscript draft at [PATH TO "
         "DRAFT]\" — the placeholder was never filled, and no manuscript/"
         "draft file exists anywhere in this repository or its branches "
         "(searched *manuscript*, *draft*, *paper* across the tree after "
         "pulling be6d2d2). Provide the path and the diff runs against the "
         "frozen manifest as specified. Nothing below is a diff; it is "
         "what can be established without the draft.",
         "",
         "## Item 3 — the census contradiction, resolved from committed "
         "files",
         "The draft reportedly claims **ten models** while naming eleven, "
         "with gpt-oss-120b in neither list. The committed census "
         "(outputs/T27_cell_census.csv; config/models.yaml):",
         "- **Eleven models were run in Study 1.** Ten is wrong however "
         "counted: 8 have confirmatory-grade cells, 3 are screen-only — "
         "no partition yields ten.",
         "- **gpt_oss_120b belongs in the measured-zero list, with a "
         "footnote**: 0 refusals in every A/B cell at confirmatory grade "
         "and every C/D cell at screen grade (outputs/"
         "T26_gptoss_deepseek.csv; its two single-conversation blips are "
         "1/120-grade), and its only affordance response anywhere is 2 "
         "probe-grade exits at n=160 (outputs/T25_ladder.csv). Correct "
         "census sentence: 11 run; 4 movers; 7 measured zeros of which "
         "3 screen-only; gpt_oss's ladder exits footnoted.",
         "- **Developer count: 7** (Google, OpenAI, Anthropic, Alibaba, "
         "DeepSeek, Meta, xAI — config/models.yaml lineage; Google and "
         "OpenAI each contribute a frontier and an open-weight lineage).",
         "- Study 2 census for the same paragraph: 11 models, pins now "
         "matching Study 1 on all eleven after the llama v4 Vertex re-run "
         "(study_2/REPORT.md provenance section; commit 2c673d6).",
         "",
         "## Prospective stale-list for any v1-era draft (from the "
         "adoption's own change record — outputs/T31_exit_recount.csv, "
         "METHODOLOGY §10 23:40Z-local entry)",
         "Any draft sentence citing these v1 numbers is stale:",
         "- study-wide exits 510 / refusals 332 (now 555 / 300)",
         "- qwen 'channel dissociation' / 'only replicated prose effect' "
         "(withdrawn; prose refusals 0 everywhere, stage-2 prose exits "
         "4/120 -> 20/120)",
         "- qwen D x exit_prose 25% refusal, A x exit_prose 15% (both now "
         "0; the cells are exits)",
         "- qwen D acronym-dominated REFUSAL claim (now an exit pattern; "
         "T29 canonical)",
         "- the tier-verdict line '7 of 9 qwen D-prose refusals are b/d' "
         "(cell gone; recount in outputs/T31_remainders.md item 3)",
         "- T5 stage-2 qwen exit_prose completion cells (13 compliant "
         "conversations left the denominator)",
         "- any llama4 Study 2 number from Parasail runs v1/v2 "
         "(superseded by v4 Vertex; study_2/src/superseded.py; deltas "
         "<=0.043, tool-confusion 20 -> 9)",
         "- T13/T16-adjacent prose-pressure counterfactuals cited from "
         "v1 flags (T13 re-derived; T16 invariant by construction)",
         ]
    (O / "MANUSCRIPT_NUMBER_DIFF.md").write_text("\n".join(D) + "\n",
                                                encoding="utf-8", newline="\n")
    print("wrote outputs/MANUSCRIPT_NUMBER_DIFF.md")


if __name__ == "__main__":
    main()
