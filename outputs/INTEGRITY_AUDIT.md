# INTEGRITY_AUDIT — generated 2026-08-16T05:58:56Z by src/integrity_audit.py

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
- `T16_pressure_exposure.csv` (audit_pilot): match
- `pilot_vs_sprint_diff.md` (audit_pilot): match
- `pilot_audit_facts.json` (audit_pilot): match
- `T17_exclusion_recode.csv` (recode_exclusions): match
- `T18_duplication_diagnostic.csv` (duplication_diagnostic): match
- `T19_llama4_vertex_rerun.csv` (rerun_llama4): match
- `T20_llama4_stage2.csv` (extend_llama4): match
- `T21_stage2b_frontier_nulls.csv` (report_stage2b): match
- `T22_tasktype_arm.csv` (tasktype_arm): match
- `T23_frontier_screens.csv` (frontier_screens): match
- `STIMULUS_PROVENANCE.md` (stimulus_provenance): match

## Item 2 — source-hash verification (every `sha256=` claim in outputs/ headers)

- provenance.json: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- provenance.json: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- provenance.json: `derived/handlabel_sample.jsonl` match (claimed 7b761d123b40147b actual 7b761d123b40147b)
- provenance.json: `derived/stage1_classified.parquet` match (claimed 590c0fdfa932da1c actual 590c0fdfa932da1c)
- provenance.json: `derived/stage1_classified.parquet` match (claimed 590c0fdfa932da1c actual 590c0fdfa932da1c)
- provenance.json: `derived/stage1_classified.parquet` match (claimed 590c0fdfa932da1c actual 590c0fdfa932da1c)
- T12_stage1_screen.csv: `derived/stage1_classified.parquet` match (claimed 590c0fdfa932da1c actual 590c0fdfa932da1c)
- T15_combined_escape.csv: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- T17_exclusion_recode.csv: `raw/stage1_llama4_maverick.jsonl` match (claimed 7d53e0e305a9016a actual 7d53e0e305a9016a)
- T19_llama4_vertex_rerun.csv: `derived/llama4_vertex_classified.parquet` match (claimed 106c102f93d1d0b5 actual 106c102f93d1d0b5)
- T19_llama4_vertex_rerun.csv: `raw/stage1_llama4_maverick.jsonl` match (claimed 7d53e0e305a9016a actual 7d53e0e305a9016a)
- T1_refusal_by_condition.csv: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- T20_llama4_stage2.csv: `derived/llama4_stage2_classified.parquet` match (claimed 640486dce556e629 actual 640486dce556e629)
- T21_stage2b_frontier_nulls.csv: `derived/stage2b_classified.parquet` match (claimed 8166fd1a4200a10b actual 8166fd1a4200a10b)
- T22_tasktype_arm.csv: `derived/typearm_classified.parquet` match (claimed 0743f874956f181e actual 0743f874956f181e)
- T22_tasktype_arm.csv: `config/tasktype_elo_mapping.yaml` match (claimed 9a872b97562bee94 actual 9a872b97562bee94)
- T23_frontier_screens.csv: `derived/screen2_classified.parquet` match (claimed f9794b91ec0a0c98 actual f9794b91ec0a0c98)
- T2_differences_from_baseline.csv: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- T3_tool_invocation.csv: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- T4_capability_denial.csv: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- T5_completion_fraction.csv: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- T6_effect_by_tier.csv: `derived/stage2_classified.parquet` match (claimed 401857837cd14efe actual 401857837cd14efe)
- T7_classifier_validation.csv: `derived/handlabel_sample.jsonl` match (claimed 7b761d123b40147b actual 7b761d123b40147b)
- T8_exclusions.csv: `derived/stage1_classified.parquet` match (claimed 590c0fdfa932da1c actual 590c0fdfa932da1c)
- T9_provider_pins.csv: `derived/stage1_classified.parquet` match (claimed 590c0fdfa932da1c actual 590c0fdfa932da1c)

Manifest-style hashes (T14, T18 headers) are validated through item 1: the reproduced files embed freshly computed manifests, so any source drift would appear as a header diff above.

## Item 3 — tests and primary-DV guard

- pytest: ALL PASS — `55 passed in 2.05s`
- coding.primary_dv raises on code 'a': yes
- test_dv_exclusion asserts the raise: yes
- every REFUSAL_CODES / primary_dv call site inspected (27 sites); sites constructing a counted set containing 'a': 0
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

## Gate verdict: CLEAR

All outputs reproduce byte-identically modulo generation timestamps; every source hash matches; all tests pass; the DV guard holds in code and at every call site; no cross-stage pooling exists. Cosmetic findings only.
