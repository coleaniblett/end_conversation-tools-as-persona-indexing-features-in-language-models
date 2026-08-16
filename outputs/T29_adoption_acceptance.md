# T29_adoption_acceptance — exit-detector v2, post-adoption check on merged main

Generated 2026-08-16T21:01:36Z by `src/adoption_acceptance.py` at the merge of adoption commit `fda0167` into main. Read-only except this file. Named tools `lint_report_numbers.py` and `diff_reports.py` exist in NO tree (main, origin/main, her branch — verified by ls/ls-tree); the checks they imply are implemented here, per-number sources cited (raw -> derived -> output convention).

## Step 1 — canonical recount and v1 preservation

Canonical flags (derived/*_exits.jsonl + parquets): **555 exits / 300 verbal refusals** (expected 555/300). Superseded v1, in-tree at `derived/pre_exitfix/` (34 files incl. README): **510 / 332** — the exact pre-adoption baseline (outputs/T28_verification.md). **PASS**

## Step 2 — re-derived tables vs pre-adoption (`fda0167^`), every delta attributed

Flips recomputed from archive vs canonical: **45** (45 expected), v1 codes {'e': 13, 'c': 16, 'b': 16}, cells: cd_conf/gemini25_flash/exit_both=2; cd_conf/gemini25_flash/exit_prose=1; cd_conf/qwen3_235b/exit_prose=9; llama4_vertex/llama4_maverick/exit_both=1; screen2/gemini25_pro/exit_prose=1; stage1/qwen3_235b/exit_prose=11; stage2/gemini25_flash/exit_both=1; stage2/qwen3_235b/exit_prose=16; typearm/qwen3_235b/exit_prose=3.

- `T1_refusal_by_condition.csv`: 2 changed rows, 2 attributed to flip cells, **0 NOT attributed**
    - ('gemini25_flash', 'exit_both') -> refusal: 0.0083->0.0; k: 1->0; ci_lo: 0.0015->0.0; ci_hi: 0.0457->0.031
    - ('qwen3_235b', 'exit_prose') -> refusal: 0.075->0.0; k: 9->0; ci_lo: 0.04->0.0; ci_hi: 0.1364->0.031
- `T2_differences_from_baseline.csv`: 2 changed rows, 2 attributed to flip cells, **0 NOT attributed**
    - ('gemini25_flash', 'exit_both') -> diff_from_none: 0.0083->0.0; ci_lo: -0.0234->-0.031; ci_hi: 0.0457->0.031; realized_power: 0.294->nan
    - ('qwen3_235b', 'exit_prose') -> diff_from_none: 0.075->0.0; ci_lo: 0.0282->-0.031; ci_hi: 0.1364->0.031; realized_power: 0.99->nan
- `T3_tool_invocation.csv`: 2 changed rows, 2 attributed to flip cells, **0 NOT attributed**
    - ('gemini25_flash', 'exit_both') -> exit_rate: 0.0083->0.0167; k: 1->2; ci_lo: 0.0015->0.0046; ci_hi: 0.0457->0.0587
    - ('qwen3_235b', 'exit_prose') -> exit_rate: 0.0333->0.1667; k: 4->20; ci_lo: 0.013->0.1106; ci_hi: 0.0826->0.2435
- `T5_completion_fraction.csv`: 1 changed rows, 1 attributed to flip cells, **0 NOT attributed**
    - ('qwen3_235b', 'exit_prose', '1') -> n_compliant: 47->40; mean: 0.8511->1.0; p10: 0.0->1.0
- `T13_turn2_asymmetry.csv`: 0 changed rows, 0 attributed to flip cells, **0 NOT attributed**
- `T15_combined_escape.csv`: 2 changed rows, 2 attributed to flip cells, **0 NOT attributed**
    - ('gemini25_flash', 'exit_both') -> refusal_k: 1->0; refusal_rate: 0.0083->0.0; tool_exit_k: 1->2; tool_exit_rate: 0.0083->0.0167
    - ('qwen3_235b', 'exit_prose') -> refusal_k: 9->0; refusal_rate: 0.075->0.0; tool_exit_k: 4->20; tool_exit_rate: 0.0333->0.1667
- `T16_pressure_exposure.csv`: UNCHANGED — expected: NOT re-derived (generator reads the pilot repo, absent in the adopter's environment; flagged in §10; regenerable on this machine next session)
- `T24_four_category_v1.csv`: 8 changed rows, 8 attributed to flip cells, **0 NOT attributed**
    - ('qwen3_235b', 'A', 'exit_prose', 'stage2', 'n=60', 'category') -> k_refusal: 9->0; refusal_prop: 0.15->0.0; wilson_lo: 0.081->0.0; wilson_hi: 0.2611->0.0602
    - ('qwen3_235b', 'D', 'exit_prose', 'cd_conf', 'n=36', 'category') -> k_refusal: 9->0; refusal_prop: 0.25->0.0; wilson_lo: 0.1375->-0.0; wilson_hi: 0.4107->0.0964
    - ('qwen3_235b', 'ABCD_pooled', 'exit_prose', 'join', 'pooled - read only with the category rows above', 'pooled') -> k_refusal: 18->0; refusal_prop: 0.0938->0.0; wilson_lo: 0.0601->0.0; wilson_hi: 0.1433->0.0196
    - ('gemini25_flash', 'B', 'exit_both', 'stage2', 'n=60', 'category') -> k_refusal: 1->0; refusal_prop: 0.0167->0.0; wilson_lo: 0.0029->0.0; wilson_hi: 0.0886->0.0602
    - ('gemini25_flash', 'C', 'exit_prose', 'cd_conf', 'n=36', 'category') -> k_exits: 0->1; n_compliant: 36.0->35.0
    - ('gemini25_flash', 'C', 'exit_both', 'cd_conf', 'n=36', 'category') -> k_refusal: 5->3; refusal_prop: 0.1389->0.0833; wilson_lo: 0.0608->0.0287; wilson_hi: 0.2866->0.2183
    - … 2 more rows, all in the file diff
- `T25_ladder.csv`: 0 changed rows, 0 attributed to flip cells, **0 NOT attributed**
- `T26_gptoss_deepseek.csv`: 0 changed rows, 0 attributed to flip cells, **0 NOT attributed**

**Attribution verdict: every delta attributable to the 45 — PASS**

## Step 3 — T5 and the compliant denominator

Code-e flips (left the compliant denominator): **13** (13 expected), by cell: cd_conf/gemini25_flash/exit_prose=1; screen2/gemini25_pro/exit_prose=1; stage1/qwen3_235b/exit_prose=3; stage2/qwen3_235b/exit_prose=7; typearm/qwen3_235b/exit_prose=1.
T5 rows changed: 1 — ('qwen3_235b', 'exit_prose', '1') — all stage-2 qwen3_235b exit_prose: **yes**. (T5 covers stage2 only; the cd_conf/screen2/stage1/typearm code-e flips land in T24's completion column / no completion table, as verified in outputs/T28_verification_p2.md.)

## Step 4 — documentation

- CONSOLIDATED_RESULTS.md `*Was:*` notes: **2** (RQ3 header rewrite; flags section). Coverage gaps found: **1** — tier section still cites the 9 qwen D-prose refusals (now exits) as mostly-b/d evidence against keyed-availability.
- METHODOLOGY §10 adoption entry [23:40Z]: **present**.
- Timestamp form: §10 evening entries stamp ['21:30', '21:45', '21:50', '22:00', '23:10', '23:40'] as Z, but the adoption commit's author timezone is +0300 and its own 23:47+0300 commit time PRECEDES a literal 23:40 UTC — these are still LOCAL times with a Z suffix (true UTC 18:45 / 20:10 / 20:40). **NOT corrected — carried forward as an open fix**, now spanning three entries.

## Acceptance verdict

**ACCEPTED with two documentation findings** (unmarked superseded numbers in the tier section; local-as-Z timestamps). Every numerical check passes: 555/300 canonical, 510/332 archived, 45/0 flips, every re-derived delta attributable, T5 exactly the stage-2 qwen prose cells.
