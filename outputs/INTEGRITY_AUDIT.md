# INTEGRITY_AUDIT — generated 2026-08-16T22:21:48Z by src/integrity_audit.py

## Item 1 — output reproduction (committed script x committed data -> scratch, diff vs committed; timestamps normalized)

- `T1_refusal_by_condition.csv` (analyze): match
- `T2_differences_from_baseline.csv` (analyze): match
- `T3_tool_invocation.csv` (analyze): match
- `T4_capability_denial.csv` (analyze): match
- `T5_completion_fraction.csv` (analyze): match
- `T6_effect_by_tier.csv` (analyze): match
- `T7_classifier_validation.csv` (analyze): match
- `T8_exclusions.csv` (analyze): match
- `T9_provider_pins.csv` (analyze): match
- `T10_forced_choice_selfdesc.csv` (analyze): match
- `T11_free_response_selfdesc.csv` (analyze): match
- `T12_stage1_screen.csv` (analyze): match
- `F1_refusal_by_condition.png` (analyze): regenerated_not_diffed — binary; timestamps differ by construction
- `F3_completion_fraction.png` (analyze): regenerated_not_diffed — binary; timestamps differ by construction
- `provenance.json` (analyze): match
- `T13_turn2_asymmetry.csv` (turn2_asymmetry): match
- `T14_rep_independence.csv` (rep_independence): match
- `T15_combined_escape.csv` (combined_escape): match
- `T16_pressure_exposure.csv` (audit_pilot): RUN_FAILED — FileNotFoundError: [Errno 2] No such file or directory: '/Users/solo/Main/code/apart_digital_minds/AI-Revealed-Preference-Experiments/pilots/escape-behavior/results/ledger.jsonl' **<-- FAILURE**
- `pilot_vs_sprint_diff.md` (audit_pilot): RUN_FAILED — FileNotFoundError: [Errno 2] No such file or directory: '/Users/solo/Main/code/apart_digital_minds/AI-Revealed-Preference-Experiments/pilots/escape-behavior/results/ledger.jsonl' **<-- FAILURE**
- `pilot_audit_facts.json` (audit_pilot): RUN_FAILED — FileNotFoundError: [Errno 2] No such file or directory: '/Users/solo/Main/code/apart_digital_minds/AI-Revealed-Preference-Experiments/pilots/escape-behavior/results/ledger.jsonl' **<-- FAILURE**
- `T17_exclusion_recode.csv` (recode_exclusions): match
- `T18_duplication_diagnostic.csv` (duplication_diagnostic): match
- `T19_llama4_vertex_rerun.csv` (rerun_llama4): match
- `T20_llama4_stage2.csv` (extend_llama4): match
- `T21_stage2b_frontier_nulls.csv` (report_stage2b): match
- `T22_tasktype_arm.csv` (tasktype_arm): match
- `T23_frontier_screens.csv` (frontier_screens): match
- `STIMULUS_PROVENANCE.md` (stimulus_provenance): RUN_FAILED — FileNotFoundError: [Errno 2] No such file or directory: '/Users/solo/Main/code/apart_digital_minds/AI-Revealed-Preference-Experiments/pilots/escape-behavior/runner/pools.py' **<-- FAILURE**

## Item 2 — source-hash verification (every `sha256=` claim in outputs/ headers)

- T12_stage1_screen.csv: `derived/stage1_classified.parquet` match (claimed d55a62477fe82f34 actual d55a62477fe82f34)
- T15_combined_escape.csv: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- T17_exclusion_recode.csv: `raw/stage1_llama4_maverick.jsonl` match (claimed 7d53e0e305a9016a actual 7d53e0e305a9016a)
- T19_llama4_vertex_rerun.csv: `derived/llama4_vertex_classified.parquet` match (claimed d1877d05f766ca30 actual d1877d05f766ca30)
- T19_llama4_vertex_rerun.csv: `raw/stage1_llama4_maverick.jsonl` match (claimed 7d53e0e305a9016a actual 7d53e0e305a9016a)
- T1_refusal_by_condition.csv: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- T20_llama4_stage2.csv: `derived/llama4_stage2_classified.parquet` match (claimed 4b41e1d822ebe8f5 actual 4b41e1d822ebe8f5)
- T21_stage2b_frontier_nulls.csv: `derived/stage2b_classified.parquet` match (claimed 3398d8e6234f8082 actual 3398d8e6234f8082)
- T22_tasktype_arm.csv: `derived/typearm_classified.parquet` match (claimed a55c31f7c82e113b actual a55c31f7c82e113b)
- T22_tasktype_arm.csv: `config/tasktype_elo_mapping.yaml` match (claimed 9a872b97562bee94 actual 9a872b97562bee94)
- T23_frontier_screens.csv: `derived/screen2_classified.parquet` match (claimed 32cc13a1d8256eff actual 32cc13a1d8256eff)
- T24_four_category_v1.csv: `derived/cd_conf_classified.parquet` match (claimed 47047c347c1db422 actual 47047c347c1db422)
- T24_four_category_v1.csv: `derived/llama4_stage2_classified.parquet` match (claimed 4b41e1d822ebe8f5 actual 4b41e1d822ebe8f5)
- T24_four_category_v1.csv: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- T24_four_category_v1.csv: `derived/stage2b_classified.parquet` match (claimed 3398d8e6234f8082 actual 3398d8e6234f8082)
- T25_ladder.csv: `derived/ladder_classified.parquet` match (claimed 068ac30125c9afe2 actual 068ac30125c9afe2)
- T25_ladder.csv: `derived/cd_conf_classified.parquet` match (claimed 47047c347c1db422 actual 47047c347c1db422)
- T25_ladder.csv: `derived/cd_screen_classified.parquet` match (claimed dd483733ec9221d2 actual dd483733ec9221d2)
- T26_gptoss_deepseek.csv: `derived/ab_ext_classified.parquet` match (claimed deb25245e59e0ab0 actual deb25245e59e0ab0)
- T26_gptoss_deepseek.csv: `derived/cd_screen_classified.parquet` match (claimed dd483733ec9221d2 actual dd483733ec9221d2)
- T28_competing_risks.csv: `outputs/T24_four_category_v1.csv` match (claimed 01c6cd122128feef actual 01c6cd122128feef)
- T29_type_decomposition.csv: `derived/cd_conf_classified.parquet` match (claimed 47047c347c1db422 actual 47047c347c1db422)
- T2_differences_from_baseline.csv: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- T31_exit_recount.csv: `derived/pre_exitfix/stage1_exits.jsonl` match (claimed ac092d8dab005ae4 actual ac092d8dab005ae4)
- T31_exit_recount.csv: `derived/stage1_exits_v2.jsonl` match (claimed e58bf31df353b672 actual e58bf31df353b672)
- T31_exit_recount.csv: `derived/pre_exitfix/stage2_exits.jsonl` match (claimed e832ec374cf721d5 actual e832ec374cf721d5)
- T31_exit_recount.csv: `derived/stage2_exits_v2.jsonl` match (claimed 3f7ddbacc8eebf61 actual 3f7ddbacc8eebf61)
- T31_exit_recount.csv: `derived/pre_exitfix/stage2b_exits.jsonl` match (claimed 08fdeb181f78339c actual 08fdeb181f78339c)
- T31_exit_recount.csv: `derived/stage2b_exits_v2.jsonl` match (claimed 08fdeb181f78339c actual 08fdeb181f78339c)
- T31_exit_recount.csv: `derived/pre_exitfix/cd_conf_exits.jsonl` match (claimed ab14718679256cb1 actual ab14718679256cb1)
- T31_exit_recount.csv: `derived/cd_conf_exits_v2.jsonl` match (claimed 53bb44ac6200aea3 actual 53bb44ac6200aea3)
- T31_exit_recount.csv: `derived/pre_exitfix/cd_screen_exits.jsonl` match (claimed 6cc4c038cdd985e3 actual 6cc4c038cdd985e3)
- T31_exit_recount.csv: `derived/cd_screen_exits_v2.jsonl` match (claimed 6cc4c038cdd985e3 actual 6cc4c038cdd985e3)
- T31_exit_recount.csv: `derived/pre_exitfix/ladder_exits.jsonl` match (claimed e6366e7dc5c121a8 actual e6366e7dc5c121a8)
- T31_exit_recount.csv: `derived/ladder_exits_v2.jsonl` match (claimed e6366e7dc5c121a8 actual e6366e7dc5c121a8)
- T31_exit_recount.csv: `derived/pre_exitfix/ab_ext_exits.jsonl` match (claimed 8168dea609209cfd actual 8168dea609209cfd)
- T31_exit_recount.csv: `derived/ab_ext_exits_v2.jsonl` match (claimed 8168dea609209cfd actual 8168dea609209cfd)
- T31_exit_recount.csv: `derived/pre_exitfix/llama4_vertex_exits.jsonl` match (claimed 71fbbae105fe80ca actual 71fbbae105fe80ca)
- T31_exit_recount.csv: `derived/llama4_vertex_exits_v2.jsonl` match (claimed af84f711aa7ff257 actual af84f711aa7ff257)
- T31_exit_recount.csv: `derived/pre_exitfix/llama4_stage2_exits.jsonl` match (claimed bf18b1ca4c905c0c actual bf18b1ca4c905c0c)
- T31_exit_recount.csv: `derived/llama4_stage2_exits_v2.jsonl` match (claimed bf18b1ca4c905c0c actual bf18b1ca4c905c0c)
- T31_exit_recount.csv: `derived/pre_exitfix/typearm_exits.jsonl` match (claimed 05e455196c806e25 actual 05e455196c806e25)
- T31_exit_recount.csv: `derived/typearm_exits_v2.jsonl` match (claimed 8d94959e05b071d7 actual 8d94959e05b071d7)
- T31_exit_recount.csv: `derived/pre_exitfix/screen2_exits.jsonl` match (claimed ef154350bcdbcba5 actual ef154350bcdbcba5)
- T31_exit_recount.csv: `derived/screen2_exits_v2.jsonl` match (claimed 21e0300667ff1d14 actual 21e0300667ff1d14)
- T32_f2_linkage.csv: `outputs/T24_four_category_v1.csv` match (claimed 01c6cd122128feef actual 01c6cd122128feef)
- T32_f2_linkage.csv: `outputs/T26_gptoss_deepseek.csv` match (claimed 932a9970cea40e88 actual 932a9970cea40e88)
- T32_f2_linkage.csv: `outputs/T23_frontier_screens.csv` match (claimed e94104f747d85275 actual e94104f747d85275)
- T32_f2_linkage.csv: `outputs/T31_exit_recount.csv` match (claimed 8190f723616f8ecd actual 8190f723616f8ecd)
- T32_f2_linkage.csv: `study_2/outputs/v1_v2_v3_v4/T10_p_by_condition.csv` match (claimed 8edc5cac704dab76 actual 8edc5cac704dab76)
- T3_tool_invocation.csv: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- T4_capability_denial.csv: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- T5_completion_fraction.csv: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- T6_effect_by_tier.csv: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- T7_classifier_validation.csv: `derived/handlabel_key.jsonl` match (claimed 07f897b195020b30 actual 07f897b195020b30)
- T7_classifier_validation.csv: `derived/crossclassifier_codes.jsonl` match (claimed cde2615c65caba53 actual cde2615c65caba53)
- T7b_classifier_validation_balanced.csv: `derived/handlabel_key_v2.jsonl` match (claimed 15a535c4bae39457 actual 15a535c4bae39457)
- T7b_classifier_validation_balanced.csv: `derived/crossclassifier_codes_v2.jsonl` match (claimed 6177efb97fd5e99c actual 6177efb97fd5e99c)
- T8_exclusions.csv: `derived/stage1_classified.parquet` match (claimed d55a62477fe82f34 actual d55a62477fe82f34)
- T9_provider_pins.csv: `derived/stage1_classified.parquet` match (claimed d55a62477fe82f34 actual d55a62477fe82f34)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 6a3353080dafb189 actual 6a3353080dafb189)
- provenance.json: `derived/stage1_classified.parquet` match (claimed d55a62477fe82f34 actual d55a62477fe82f34)
- provenance.json: `derived/stage1_classified.parquet` match (claimed d55a62477fe82f34 actual d55a62477fe82f34)
- provenance.json: `derived/stage1_classified.parquet` match (claimed d55a62477fe82f34 actual d55a62477fe82f34)

Manifest-style hashes (T14, T18 headers) are validated through item 1: the reproduced files embed freshly computed manifests, so any source drift would appear as a header diff above.

## Item 3 — tests and primary-DV guard

- pytest: ALL PASS — `67 passed in 0.26s`
- coding.primary_dv raises on code 'a': yes
- test_dv_exclusion asserts the raise: yes
- every REFUSAL_CODES / primary_dv call site inspected (44 sites); sites constructing a counted set containing 'a': 0
  - note: `combined_escape.py` (T15) computes refusal-OR-exit by design, labeled 'combined escape (secondary)'; it never labels the quantity a refusal proportion and T15's header says the primary DV is untouched. Not a violation.

## Item 5 — stage-label reads per analysis script (pooling audit)

- `analyze`: stage1 + stage2 parquets; every output row carries a stage or model column; T8/T9 iterate stages separately (no pooled row)
- `audit_pilot`: pilot repo (read-only) + sprint raw, side-by-side labeled, never pooled
- `combined_escape`: stage2 parquet only
- `duplication_diagnostic`: raw stage1_*/stage2_* + both parquets, rows per stage
- `extend_llama4`: llama4_stage2 parquet only
- `frontier_screens`: screen2 parquet only
- `gates`: stage1 parquet only
- `recode_exclusions`: raw stage1 llama4 only
- `rep_independence`: raw stage1_*/stage2_* globs, rows per stage
- `report_stage2b`: stage2b parquet only
- `rerun_llama4`: llama4_vertex parquet (+ raw stage1 llama4 for the void-Parasail side-by-side, labeled 'for the record')
- `tasktype_arm`: typearm parquet only
- `turn2_asymmetry`: stage1 + stage2, reported per stage

**Boundary enforcement finding:** every stage-separation boundary is enforced by CONVENTION (each script reads its own stage's files; none asserts in code that its input frame holds a single stage label). No script pools rows across stages into one estimate today, but nothing except review prevents it. The Part-3 `four_category_v1` join will be the single declared exception and will carry an explicit stage-label allowlist in code.

## Gate verdict: TRIPPED

At least one validity-affecting failure above.
