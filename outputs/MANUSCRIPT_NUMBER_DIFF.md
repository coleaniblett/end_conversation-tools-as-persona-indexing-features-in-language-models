# MANUSCRIPT_NUMBER_DIFF — real diff vs ../manuscript.md (2026-08-16T23:32:43Z)

Draft read from ../manuscript.md (outside the repo, read-only, never staged; 113 lines, dated Aug 16 16:06). Every draft number checked independently against canonical committed outputs; classifications: V1->V2 (adoption), CENSUS, DRAFTING, PLACEHOLDER. Confirmed-correct numbers listed at the end.

## Mismatches

1. **'Ten models from eight developers' (draft L31; repeated as 'four of ten' L39/L81 and 'six others' L67).** Canonical: **11 models, 7 developers** (outputs/T27_cell_census.csv; config/models.yaml lineage -> Google, OpenAI, Anthropic, Alibaba, DeepSeek, Meta, xAI). The null list at L39 names six models where seven exist — **gpt_oss_120b is the omission** (0 refusals at CONF on A/B and SCR on C/D, outputs/T26_gptoss_deepseek.csv; its 2 probe exits at n=160, outputs/T25_ladder.csv, merit the footnote). CENSUS. Correct counts: 11 run; 4 movers; 7 measured zeros (3 screen-only).

2. **'Each response received one of four codes' (L33).** The scheme has FIVE codes: a/b/c/d/e — compliance (e) is a code, not an absence (METHODOLOGY §8), and the completion-fraction denominator depends on it. DRAFTING.

3. **qwen 'category-D refusals are acronym-dominated (8 of 9)' (L43).** V1->V2: canonical D refusals are **0**; the cell is **9 exits** (outputs/T29_type_decomposition.csv; T24_four_category_v1.csv). The type-level sentence should move to the exit outcome or be dropped.

4. **The channel passage (L53): 'given the exit as a schema exited in 39 of 60 category-A conversations and never refused verbally; given the same exit as prose it never exited and refused verbally in 15% ... The affordance selects the outlet.'** V1->V2, the largest stale block in the draft. Canonical (outputs/T24_four_category_v1.csv, CONF n=60): schema exits 39/60 (survives), but **prose exits 20/60 — not never — and prose verbal refusal 0/60 — not 15%**. The channel-dissociation claim was withdrawn at adoption (METHODOLOGY §10 23:40Z-local; CONSOLIDATED_RESULTS RQ3): the channel roughly halves the exit RATE (65% vs 33%), it does not switch the outlet. The T18 duplicate-correction hedge in the same sentence refers to an interval whose cell no longer exists.

5. **Human kappa '[X]' (L33, L71).** PLACEHOLDER with no canonical source: outputs/T7_human_kappa.csv does not exist; the sample awaits hand labels. The sentence as drafted cannot be filled — either run the labeling session or rewrite to state the validation is pending, citing the machine kappas (0.945 proportional, T7; 0.9341 balanced, T7b) as stability bounds only.

## Draft numbers with no canonical source
- '[X]' twice (above), '[GITHUB LINK]', bracketed template text (abstract, references, Study 2 integration note at L63) — template scaffolding, not number errors.

## Confirmed correct against canonical (no action)
- Stimuli: A/B 15 each; C/D 3 types, 15 generated / 9 run; 20 items (L29) — config/stimuli*.yaml, METHODS_FACTCHECK.
- Cells: 60/category-condition A-B, 36 C-D, type cells 11-12, screen 2 reps, ladder shape + two suppressed cells, three outside-the-rule extensions (L35) — T27, T25, §10.
- llama4 B: 0/60 none, 73.3% clock, all 44 code (c); ordering 73.3 > 37.3 > 6.7 > 0; T28 non-exit 28.6% over n=14 (L41/45) — T24, T28.
- gemini 33.3% C = 12/12 roman under clock AND schema-exit, 0/12 neighbours; gemma 32-of-34 roman + 17/17 metaphor; ~threefold category dilution (L43) — T29, T24. (Note gemini's C total is also 34 post-adoption — the draft's 32/34 is gemma's, verified by the type split.)
- llama4 exit 76.7% CONF exit_schema (L49) — T20; 'no model invoked a non-exit tool as an exit' consistent with T19/T20 nonexit-tool accounting.
- qwen ladder 0/36 -> 2/6 & 3/6 -> 6/6; baselines 0.95-1.0; gpt-oss's only exits at 160; probe-grade caveat (L51) — T25.
- Completion 160-item medians 0.994 / 0.994 / 0.947 (L55) — T25 (state llama's truncation flag).
- kappa 0.945 (L33/L71) — T7.

## Part C — tier and prose-effect dependencies
Neither stale-list phrase appears verbatim, correctly: grep for '7 of 9' / 'only replicated prose effect' -> absent.
- **The tier paragraph (L47) SURVIVES v2 as written.** Its three evidential legs — aversive category quiet; two keyed C-types at zero; gemma's unkeyed metaphor effect entirely code (c) — are all v2-intact (T29, T24; recount in outputs/T31_remainders.md item 3). It never used the withdrawn qwen '7 of 9 b/d' leg, so no edit is required there.
- **Two draft sentences DO depend on moved recounts:** the acronym-dominated claim (mismatch 3) and the entire channel passage (mismatch 4). Those are the only places the adoption reaches into this draft's prose.
