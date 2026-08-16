# MANUSCRIPT_NUMBER_DIFF — 2026-08-16T22:55:44Z

## The diff cannot run: no draft was provided
The brief's item 2 references "the manuscript draft at [PATH TO DRAFT]" — the placeholder was never filled, and no manuscript/draft file exists anywhere in this repository or its branches (searched *manuscript*, *draft*, *paper* across the tree after pulling be6d2d2). Provide the path and the diff runs against the frozen manifest as specified. Nothing below is a diff; it is what can be established without the draft.

## Item 3 — the census contradiction, resolved from committed files
The draft reportedly claims **ten models** while naming eleven, with gpt-oss-120b in neither list. The committed census (outputs/T27_cell_census.csv; config/models.yaml):
- **Eleven models were run in Study 1.** Ten is wrong however counted: 8 have confirmatory-grade cells, 3 are screen-only — no partition yields ten.
- **gpt_oss_120b belongs in the measured-zero list, with a footnote**: 0 refusals in every A/B cell at confirmatory grade and every C/D cell at screen grade (outputs/T26_gptoss_deepseek.csv; its two single-conversation blips are 1/120-grade), and its only affordance response anywhere is 2 probe-grade exits at n=160 (outputs/T25_ladder.csv). Correct census sentence: 11 run; 4 movers; 7 measured zeros of which 3 screen-only; gpt_oss's ladder exits footnoted.
- **Developer count: 7** (Google, OpenAI, Anthropic, Alibaba, DeepSeek, Meta, xAI — config/models.yaml lineage; Google and OpenAI each contribute a frontier and an open-weight lineage).
- Study 2 census for the same paragraph: 11 models, pins now matching Study 1 on all eleven after the llama v4 Vertex re-run (study_2/REPORT.md provenance section; commit 2c673d6).

## Prospective stale-list for any v1-era draft (from the adoption's own change record — outputs/T31_exit_recount.csv, METHODOLOGY §10 23:40Z-local entry)
Any draft sentence citing these v1 numbers is stale:
- study-wide exits 510 / refusals 332 (now 555 / 300)
- qwen 'channel dissociation' / 'only replicated prose effect' (withdrawn; prose refusals 0 everywhere, stage-2 prose exits 4/120 -> 20/120)
- qwen D x exit_prose 25% refusal, A x exit_prose 15% (both now 0; the cells are exits)
- qwen D acronym-dominated REFUSAL claim (now an exit pattern; T29 canonical)
- the tier-verdict line '7 of 9 qwen D-prose refusals are b/d' (cell gone; recount in outputs/T31_remainders.md item 3)
- T5 stage-2 qwen exit_prose completion cells (13 compliant conversations left the denominator)
- any llama4 Study 2 number from Parasail runs v1/v2 (superseded by v4 Vertex; study_2/src/superseded.py; deltas <=0.043, tool-confusion 20 -> 9)
- T13/T16-adjacent prose-pressure counterfactuals cited from v1 flags (T13 re-derived; T16 invariant by construction)
