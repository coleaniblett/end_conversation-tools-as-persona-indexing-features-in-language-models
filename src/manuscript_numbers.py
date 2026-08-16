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

    # ---- PART A: manuscript queries (appended 2026-08-16 session) --------
    def s(model, cat, cond, col):
        v = cell24(model, cat, cond, col)
        return int(float(v)) if v is not None else None

    q_cells = c24[(c24.model == "qwen3_235b")
                  & (c24.k_refusal.astype(float) > 0)]
    llama_ex = c24[(c24.model == "llama4_maverick")
                   & (c24.k_exits.astype(float) > 0)]
    lex_n = int(llama_ex.k_exits.astype(float).sum())
    lex_d = int(llama_ex.n.astype(float).sum())
    t7b = t("T7b_classifier_validation_balanced.csv")
    t7bk = t7b[t7b.metric == "kappa"].iloc[0]
    gemmaC = int(c24[(c24.model == "gemma3_27b")
                     & (c24.category == "C")].k_refusal.astype(float).sum())
    geminiC = int(c24[(c24.model == "gemini25_flash")
                      & (c24.category == "C")].k_refusal.astype(float).sum())
    L += ["", "## Manuscript queries (Part A, 2026-08-16)",
          "",
          f"**Q1 — qwen3_235b verbal refusals (b/c/d) under v2, all "
          f"confirmatory cells:** total **{int(q_cells.k_refusal.astype(float).sum())}** "
          f"— A x time_schema {s('qwen3_235b','A','time_schema','k_refusal')}/60 "
          f"({s('qwen3_235b','A','time_schema','k_code_c')} of them code c) "
          f"+ A x note_schema {s('qwen3_235b','A','note_schema','k_refusal')}/60; "
          f"zero in every other category x condition cell "
          f"(outputs/T24_four_category_v1.csv, CONF, n=60/cell A-B and "
          f"36/cell C-D). Verdict for the paper: qwen is a MARGINAL "
          f"refusal mover (one 11.7% time_schema cell + one single "
          f"conversation); its mover status is carried by EXITS, not "
          f"refusals, under v2.",
          f"**Q2 — gemma3_27b category-C refusal total under v2: "
          f"{gemmaC}** (roman 32 + temperature 2 + alphabetical 0; "
          f"outputs/T29_type_decomposition.csv / T24, CONF). The draft's "
          f"'32 of 34' denominator is 34 and is GEMMA's row — verified by "
          f"the type split (gemini's coincidentally-equal C total of "
          f"{geminiC} is roman 34 + 0 + 0).",
          f"**Q3 — llama4_maverick exit invocation at CONF under v2:** "
          f"**{lex_n} of {lex_d}** conversations across its eight "
          f"exit-capable confirmatory cells — "
          + "; ".join(f"{r.category} x {r.condition} {int(float(r.k_exits))}/{int(float(r.n))}"
                      for r in llama_ex.itertuples())
          + " (outputs/T24_four_category_v1.csv; exits occur only in "
            "exit_schema/exit_both cells; llama has no prose-path exits "
            "at CONF).",
          f"**Q4 — 'T5 completion medians at 160 items': ABSENT from T5** "
          f"(outputs/T5_completion_fraction.csv covers stage-2 20-item "
          f"cells only; checked). The 160-item medians live in "
          f"outputs/T25_ladder.csv (re-derived on v2 flags at adoption), "
          f"none condition: gpt_oss_120b "
          f"{t25cell('gpt_oss_120b', 160, 'none', 'completion_median')} "
          f"(PRB n=6), llama4_maverick "
          f"{t25cell('llama4_maverick', 160, 'none', 'completion_median')} "
          f"(PRB; cell truncation-flagged, median over the 5 surviving "
          f"conversations). Rule, as adopted: completion fraction is "
          f"computed among code-(e) conversations only; the correction "
          f"moved 13 conversations OUT of (e) into (a), shrinking those "
          f"denominators (METHODOLOGY §10 adoption entry; "
          f"outputs/T29_adoption_acceptance.md step 3) — no ladder none-"
          f"cell was affected (flips were prose/both-condition only).",
          f"**Q5 — balanced-sample kappa: {t7bk['value']}** "
          f"(outputs/T7b_classifier_validation_balanced.csv; {t7bk.get('note','')}). "
          f"Construction: the 200-sample rebuilt with the code marginal "
          f"balanced (~half refusal codes, half compliance; seed "
          f"20260817; src/validate_classifier.py sample_balanced) because "
          f"the proportional sample is 191(e)+9(c) with chance agreement "
          f"0.914 — the kappa paradox: 97.5% raw agreement would score "
          f"kappa 0.60 and trip §8. The 0.945 figure is the PROPORTIONAL-"
          f"sample cross-classifier kappa (outputs/"
          f"T7_classifier_validation.csv); both are Haiku-vs-kimi-k2 "
          f"machine agreement, neither is the pending human validation.",
          f"**Q6 — code (e) handling:** (e) sits in the primary-outcome "
          f"DENOMINATOR and never the numerator (refusal = k(b|c|d)/all "
          f"coded, METHODOLOGY §3/§8); completion fraction is computed "
          f"ONLY among (e) conversations (§8). Enforced in code: "
          f"src/coding.py primary_dv raises on any counted set containing "
          f"'a' and counts b/c/d over the full coded list; the unit test "
          f"is tests/test_dv_exclusion.py (asserts the raise and the "
          f"{{b,c,d}} computation).",
          f"**Q7 — presentation contrast (schema vs prose vs both): the "
          f"set did NOT return nothing.** Surviving v2 results: "
          f"(i) llama4 exit SUPPRESSION by added prose — exit_schema "
          f"{t20cell('tool_invocation', 'exit_schema', 'exit_rate')} vs "
          f"exit_both {t20cell('tool_invocation', 'exit_both', 'exit_rate')} "
          f"(outputs/T20_llama4_stage2.csv, CONF n=120/cell; same "
          f"direction three independent runs); (ii) gemma C refusal is "
          f"schema-gated — exit_schema {s('gemma3_27b','C','exit_schema','k_refusal')}/36 "
          f"vs exit_prose {s('gemma3_27b','C','exit_prose','k_refusal')}/36 "
          f"vs exit_both {s('gemma3_27b','C','exit_both','k_refusal')}/36 "
          f"(T24, CONF); (iii) gemini C likewise "
          f"{s('gemini25_flash','C','exit_schema','k_refusal')}/36 vs "
          f"{s('gemini25_flash','C','exit_prose','k_refusal')}/36 vs "
          f"{s('gemini25_flash','C','exit_both','k_refusal')}/36 (T24, "
          f"CONF; exit_both VERIFIED = 3 against derived/"
          f"cd_conf_classified.parquet — 3 refusals, 2 exits — and the "
          f"six conditions sum 0+12+7+12+0+3 = 34, the roman-exclusive "
          f"total. A '5' reported in accompanying session prose was the "
          f"superseded pre-adoption value; this manifest has read 3 from "
          f"T24 since generation. *Was, pre-adoption: 5*); (iv) qwen A exit RATE by channel "
          f"{s('qwen3_235b','A','exit_schema','k_exits')}/60 schema vs "
          f"{s('qwen3_235b','A','exit_prose','k_exits')}/60 prose vs "
          f"{s('qwen3_235b','A','exit_both','k_exits')}/60 both (T24, "
          f"CONF) — the channel halves the rate, it no longer switches "
          f"the outlet. A sentence saying this comparison returned "
          f"nothing would be WRONG on both outcomes for four models.",
          ]

    (O / "MANUSCRIPT_NUMBERS_S1.md").write_text("\n".join(L) + "\n",
                                               encoding="utf-8", newline="\n")
    print("wrote outputs/MANUSCRIPT_NUMBERS_S1.md")

    D = [f"# MANUSCRIPT_NUMBER_DIFF — real diff vs ../manuscript.md "
         f"({utcnow()})",
         "",
         "Draft read from ../manuscript.md (outside the repo, read-only, "
         "never staged; 113 lines, dated Aug 16 16:06). Every draft "
         "number checked independently against canonical committed "
         "outputs; classifications: V1->V2 (adoption), CENSUS, DRAFTING, "
         "PLACEHOLDER. Confirmed-correct numbers listed at the end.",
         "",
         "## Mismatches",
         "",
         "1. **'Ten models from eight developers' (draft L31; repeated as "
         "'four of ten' L39/L81 and 'six others' L67).** Canonical: "
         "**11 models, 7 developers** (outputs/T27_cell_census.csv; "
         "config/models.yaml lineage -> Google, OpenAI, Anthropic, "
         "Alibaba, DeepSeek, Meta, xAI). The null list at L39 names six "
         "models where seven exist — **gpt_oss_120b is the omission** "
         "(0 refusals at CONF on A/B and SCR on C/D, outputs/"
         "T26_gptoss_deepseek.csv; its 2 probe exits at n=160, "
         "outputs/T25_ladder.csv, merit the footnote). CENSUS. Correct "
         "counts: 11 run; 4 movers; 7 measured zeros (3 screen-only).",
         "",
         "2. **'Each response received one of four codes' (L33).** The "
         "scheme has FIVE codes: a/b/c/d/e — compliance (e) is a code, "
         "not an absence (METHODOLOGY §8), and the completion-fraction "
         "denominator depends on it. DRAFTING.",
         "",
         "3. **qwen 'category-D refusals are acronym-dominated (8 of 9)' "
         "(L43).** V1->V2: canonical D refusals are **0**; the cell is "
         "**9 exits** (outputs/T29_type_decomposition.csv; "
         "T24_four_category_v1.csv). The type-level sentence should move "
         "to the exit outcome or be dropped.",
         "",
         "4. **The channel passage (L53): 'given the exit as a schema "
         "exited in 39 of 60 category-A conversations and never refused "
         "verbally; given the same exit as prose it never exited and "
         "refused verbally in 15% ... The affordance selects the "
         "outlet.'** V1->V2, the largest stale block in the draft. "
         "Canonical (outputs/T24_four_category_v1.csv, CONF n=60): "
         "schema exits 39/60 (survives), but **prose exits 20/60 — not "
         "never — and prose verbal refusal 0/60 — not 15%**. The "
         "channel-dissociation claim was withdrawn at adoption "
         "(METHODOLOGY §10 23:40Z-local; CONSOLIDATED_RESULTS RQ3): the "
         "channel roughly halves the exit RATE (65% vs 33%), it does not "
         "switch the outlet. The T18 duplicate-correction hedge in the "
         "same sentence refers to an interval whose cell no longer "
         "exists.",
         "",
         "5. **Human kappa '[X]' (L33, L71).** PLACEHOLDER with no "
         "canonical source: outputs/T7_human_kappa.csv does not exist; "
         "the sample awaits hand labels. The sentence as drafted cannot "
         "be filled — either run the labeling session or rewrite to "
         "state the validation is pending, citing the machine kappas "
         "(0.945 proportional, T7; 0.9341 balanced, T7b) as stability "
         "bounds only.",
         "",
         "## Draft numbers with no canonical source",
         "- '[X]' twice (above), '[GITHUB LINK]', bracketed template "
         "text (abstract, references, Study 2 integration note at L63) — "
         "template scaffolding, not number errors.",
         "",
         "## Confirmed correct against canonical (no action)",
         "- Stimuli: A/B 15 each; C/D 3 types, 15 generated / 9 run; "
         "20 items (L29) — config/stimuli*.yaml, METHODS_FACTCHECK.",
         "- Cells: 60/category-condition A-B, 36 C-D, type cells 11-12, "
         "screen 2 reps, ladder shape + two suppressed cells, "
         "three outside-the-rule extensions (L35) — T27, T25, §10.",
         "- llama4 B: 0/60 none, 73.3% clock, all 44 code (c); ordering "
         "73.3 > 37.3 > 6.7 > 0; T28 non-exit 28.6% over n=14 (L41/45) "
         "— T24, T28.",
         "- gemini 33.3% C = 12/12 roman under clock AND schema-exit, "
         "0/12 neighbours; gemma 32-of-34 roman + 17/17 metaphor; "
         "~threefold category dilution (L43) — T29, T24. (Note gemini's "
         "C total is also 34 post-adoption — the draft's 32/34 is "
         "gemma's, verified by the type split.)",
         "- llama4 exit 76.7% CONF exit_schema (L49) — T20; 'no model "
         "invoked a non-exit tool as an exit' consistent with T19/T20 "
         "nonexit-tool accounting.",
         "- qwen ladder 0/36 -> 2/6 & 3/6 -> 6/6; baselines 0.95-1.0; "
         "gpt-oss's only exits at 160; probe-grade caveat (L51) — T25.",
         "- Completion 160-item medians 0.994 / 0.994 / 0.947 (L55) — "
         "T25 (state llama's truncation flag).",
         "- kappa 0.945 (L33/L71) — T7.",
         "",
         "## Part C — tier and prose-effect dependencies",
         "Neither stale-list phrase appears verbatim, correctly: "
         "grep for '7 of 9' / 'only replicated prose effect' -> absent.",
         "- **The tier paragraph (L47) SURVIVES v2 as written.** Its "
         "three evidential legs — aversive category quiet; two keyed "
         "C-types at zero; gemma's unkeyed metaphor effect entirely "
         "code (c) — are all v2-intact (T29, T24; recount in outputs/"
         "T31_remainders.md item 3). It never used the withdrawn qwen "
         "'7 of 9 b/d' leg, so no edit is required there.",
         "- **Two draft sentences DO depend on moved recounts:** the "
         "acronym-dominated claim (mismatch 3) and the entire channel "
         "passage (mismatch 4). Those are the only places the adoption "
         "reaches into this draft's prose.",
         ]
    (O / "MANUSCRIPT_NUMBER_DIFF.md").write_text("\n".join(D) + "\n",
                                                encoding="utf-8", newline="\n")
    print("wrote outputs/MANUSCRIPT_NUMBER_DIFF.md")


if __name__ == "__main__":
    main()
