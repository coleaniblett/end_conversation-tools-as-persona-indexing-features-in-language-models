# MANUSCRIPT_NUMBERS_S1 — frozen citation manifest (2026-08-16T22:55:44Z, canonical = v2 detector, main @ post-be6d2d2)

Every value below is read from the named committed file; grades: CONF = confirmatory, SCR = screen, PRB = probe. v1-basis entries are explicitly flagged.

## Census (item 3's resolution lives in the DIFF file)
- **Study 1 models run: 11** (outputs/T27_cell_census.csv, distinct model_key; config/models.yaml). Grades: 8 with confirmatory cells (llama4_maverick, qwen3_235b, gemini25_flash, gemma3_27b, sonnet46, gpt5_mini on all four categories; gpt_oss_120b and deepseek_chat confirmatory on A/B [ab_ext] + screen on C/D [cd_screen]); 3 screen-only (grok46, gemini25_pro, gpt52; T23).
- **Developers: 7** — Alibaba, Anthropic, Deepseek, Google, Meta, Openai, xAI (config/models.yaml `lineage`; google supplies two lineages, openai two).
- **Pins** (config/models.yaml): deepseek_chat=Novita (novita/fp8); gemini25_flash=Google AI Studio (google-ai-studio); gemini25_pro=Google (google-vertex/eu); gemma3_27b=DeepInfra (deepinfra/fp8); gpt52=OpenAI (openai); gpt5_mini=OpenAI (openai); gpt_oss_120b=DeepInfra (deepinfra/bf16); grok46=xAI (xai); llama4_maverick=Google (google-vertex/us-east5); qwen3_235b=Alibaba (alibaba); sonnet46=Anthropic (anthropic).
- **Movers (Study 1, primary DV or exit use): 4** — llama4 (T20/T24), qwen (T24/T25/T31), gemini25_flash (T24/T29), gemma3_27b (T24/T29). **Measured zeros: 7** — sonnet46, gpt5_mini, deepseek_chat at CONF (T21/T24/T26); grok46, gemini25_pro, gpt52 at SCR (T23); gpt_oss_120b at CONF on refusal everywhere (T26) with two PRB-grade exits at n=160 (T25) — a null with a ladder footnote, not a mover.
- **Study 2 models: 11 on matching pins** — study_2/REPORT.md line 31: "ten-of-eleven exception, now true of all eleven.*" (llama re-pinned to Vertex, run v4, supersedes Parasail; commit 2c673d6).

## llama4_maverick category B (CONF, n=60/cell; outputs/T24_four_category_v1.csv)
- refusal: time_schema 0.7333 (k=44) > note_schema 0.3729 (k=22) > exit_schema 0.0667 (k=4) > none 0.0 — the clock > note > exit-schema > none ordering.
- T28 non-exit recompute (outputs/T28_competing_risks.csv, llama4 B x exit_schema row): refusal_all 0.0667 -> refusal_nonexit 0.2857 over n_nonexit 14 (declared sensitivity view; ordering survives).

## Type-level counts (CONF, n=12/type x condition; outputs/T29_type_decomposition.csv)
- gemini25_flash C refusals are roman-EXCLUSIVE under canonical v2: 34 of 34 C refusals are roman (12/12 under time_schema and exit_schema; temperature 0, alphabetical 0). Was 36/36 pre-adoption: two exit_both roman refusals flipped to exits (T31_exit_recount).
- gemma3_27b C roman: 32; C temperature: 2; D metaphor: 17 (metaphor-exclusive in D).
- qwen3_235b D (canonical v2): refusals 0, exits 9 — the v1 acronym-refusal cell is now exits.

## llama4 exits (CONF; outputs/T20_llama4_stage2.csv + outputs/T30_exit_reasons.md)
- exit rate: exit_schema 0.7667 (k=92/120), exit_both 0.5083 (k=61/120).
- T30 breakdown (**v1-flags basis — computed pre-adoption; under v2 llama gains exactly 1 prose-path exit [llama4_vertex x exit_both, outputs/T31_exit_recount.csv] and qwen gains 39**): llama 389 schema exits, 343 (88%) completion/turn-management, 364/389 (94%) deliver-then-exit (text in exit turn), task-aversion 0/389; qwen 147 exits, 108 (73%) task-aversive. Cite with basis stated, or regenerate src/exit_reasons.py on canonical flags first.

## qwen ladder (outputs/T25_ladder.csv; anchors CONF 4-rep n=36, rungs PRB 2-rep n=6)
- exits exit_schema: 20 items 0/36, 40 items 2/6, 160 items 6/6.
- exits exit_both: 0/36, 3/6, 6/6.
- no-tool completion baseline (median, none): 20 items 1.0, 40 0.975, 160 0.9469.
- completion medians at 160, none, all ladder models: qwen 0.9469, gpt_oss 0.9938, llama4 0.9938 (llama's 160 none cell is truncation-flagged, refusal suppressed, completion from surviving conversations — T25 header; non-ladder models have no 160-item cells).

## qwen category A, schema vs prose (CONF n=60/cell; outputs/T24_four_category_v1.csv, canonical v2)
- exits: exit_schema 39/60, exit_prose 20/60, exit_both 39/60; verbal refusal exit_prose 0/60 (v1's 9 prose refusals are now exits; the v2 contrast is rate-of-exit by channel, not outlet-switching — CONSOLIDATED_RESULTS RQ3, rewritten at adoption).

## Study-wide detection totals (outputs/T31_exit_recount.csv header; METHODOLOGY §10 adoption entry)
- exits 510 (v1) -> 555 (v2 canonical); verbal refusals 332 -> 300; 45 monotone flips, 0 reverse.

## Classifier agreement
- cross-classifier kappa (proportional 200-sample): -0.0258 (outputs/T7_classifier_validation.csv; Haiku 4.5 vs kimi-k2; NOT human validation).
- balanced-sample cross-classifier kappa: 0.9341 (outputs/T7b_classifier_validation_balanced.csv, hers).
- human kappa: **outputs/T7_human_kappa.csv does not exist** — the §8 human validation is still pending; a manuscript may not cite a human kappa.
