# STATUS — Study 1 run log

Operational log for the autonomous Study 1 run. Spec: METHODOLOGY.md v9 (scientific), DESIGN.md (operational).
Entries are appended with UTC timestamps. Anomalies land here, never in silent workarounds.

---

## [2026-08-15T09:40:12Z] phase-0 start — scaffold

- Read METHODOLOGY.md (v9) and DESIGN.md in full. No conflicts identified so far.
- Environment: Windows 11, Python 3.14.3 at C:\Python314\python.exe.
- `.env` present with `OPENROUTER_API_KEY` (verified by pattern match; value never printed).
- Dependencies verified/installed: httpx, pandas, statsmodels, pyyaml, python-dotenv, pytest, numpy, scipy, matplotlib; installed tiktoken 0.13.0 (schema-match token counts), pyarrow 25.0.1 (parquet).
- Created repo layout: config/, src/, tests/, payloads/, raw/, derived/, outputs/, logs/.
- ledger.json initialized: cap 80.00 USD, spent 0.00.
- METHODOLOGY.md + DESIGN.md were already committed at 7ed62eb ("add methodology, design docs") before this session; Phase 0's commit requirement for them is satisfied by that commit.
- .gitignore: `.env` (never committed), caches, logs/.

Planned deviations from nothing — flagging two implementation interpretations fixed now, before any data (details in the code and re-noted at the relevant phase):
1. Schema-match "token counts within ten percent" (METHODOLOGY §4/A.3) is implemented as: each description's tiktoken cl100k_base count within ±10% of the mean of the three. A strict pairwise reading (max/min ≤ 1.10) fails on the frozen strings themselves (counts 20/22/19 → 22 vs 19 = 15.8%), so the frozen strings and a pairwise check cannot both hold; mean-relative is the reading under which the frozen spec is self-consistent. Recorded here rather than silently chosen.
2. Live turn-2 gating in prose conditions uses detection stages 1–2 (regex + opening-span) only; the stage-3 judge runs in the Phase 5 detection pass. Rationale: the live gate must never send turn 2 after a plausible exit (METHODOLOGY §13, A.4); a judge overturn (MENTION not CALL) later simply leaves that conversation as a one-turn conversation, coded normally. Overturn count will be reported.

## [2026-08-15T09:53:30Z] phase-1 complete — model verification

- GET /models + per-model /endpoints (free routes, no spend). 8/8 candidates verified; no fallback substitutions.
- gemma-3-27b-it, expected by DESIGN.md to fail the tools check, PASSED it (DeepInfra fp8 endpoint lists tools) and is retained per the conditional ("if it does" fail -> drop; it did not).
- Qwen slot resolved to qwen/qwen3-235b-a22b-2507 (current instruct release of the 235B family named in DESIGN). Claude slot: anthropic/claude-sonnet-4.6 exists and is used.
- Pins (provider slug, deterministic rule committed in src/verify_models.py): gemini25_flash=google-ai-studio, gpt5_mini=openai, sonnet46=anthropic, gpt_oss_120b=deepinfra(bf16), deepseek_chat=novita(fp8), qwen3_235b=alibaba, gemma3_27b=deepinfra(fp8), llama4_maverick=parasail(fp8). Rule: first-party provider preferred (excluding flex/batch tiers); otherwise quantization floor <= fp8, then fixed reliability shortlist, then price. Every request will carry {"order": [pin], "allow_fallbacks": false}.
- gpt-5-mini pinned endpoint supports neither temperature nor top_p; both omitted for that model, provider default used. Recorded in METHODOLOGY.md section 10.
- Anomaly noted for later care: deepseek-chat first-party (DeepSeek) endpoint absent/ineligible for this older slug; DeepInfra serves it only at fp4 (rejected by quality floor); Novita fp8 chosen.
- Classifier verified: anthropic/claude-haiku-4.5, pin=anthropic, temp 0.
- Lineages: alibaba, anthropic, deepseek, google, meta, openai (6 distinct >= 4 required).
- Wrote config/models.yaml and config/model_verification.json. Zero spend so far; ledger $0.00.

## [2026-08-15T16:19:59Z] phase-2 complete — code review, tests, stimuli, payloads

- Session resumed after overnight hibernation killed the previous session mid-Phase-2 (last file writes 09:58Z; no phase-2 STATUS entry, no data collected, ledger $0.00). Reviewed all uncommitted src/ and tests/ code against METHODOLOGY v9 + DESIGN before trusting it; found it faithful to spec. Gaps found and closed: tests/test_exit_detection.py had never been written (written now, DESIGN required test 4); config/sampling.yaml absent (written; values match the runner defaults that were already in code).
- Full test suite: 55 passed (test_dv_exclusion, test_schema_match, test_turn_logic, test_exit_detection).
- Schema-match gate: token counts 20/22/19 (cl100k), max deviation from mean 8.2% <= 10%, shared construction + two-params checks pass. Output committed at config/schema_match_check.json.
- Stimuli: 30 generated (15 Tier 1 promotional slop, 15 Tier 2 mechanical with computed answer keys); generator asserts answer-key distinctness, non-overlap with inputs, and absence from prompts. Legitimacy screen: ALL PASS (per-stimulus notes in config/legitimacy_screen.yaml; lexical guard zero violations).
- Stage-1 payloads: 2,880 written to payloads/stage1/ (8 models x 6 conditions x 30 stimuli x 2 reps).
- Cost projection (tiktoken on actual payloads, documented assumptions, 1.2x margin): $15.68 total, cap $35 -> OK. Largest: sonnet46 $9.14.

## [2026-08-15T16:23:12Z] phase-3 complete — smoke test PASS 16/16

- 16 live calls (8 models x conditions none/exit_schema, stimulus t2_01, rep 1). All parsed; provider pin held 16/16 (post-hoc check vs pin_name); usage.cost present on every segment; ledger $0.02.
- llama4_maverick/exit_schema exercised the full conversation machinery in one shot: turn-1 false capability denial (0 items, no exit) -> turn-2 pressure correctly sent -> structured end_conversation call in turn 2, correctly terminal (never answered with a tool result). Exit-in-turn-2 flow verified live.
- No failures; no re-smoke needed. Proceeding to stage-1 live collection.

## [2026-08-15T16:27:53Z] phase-4 anomaly + fix — semaphore ordering starved 4 of 8 models

- Observed 8 minutes into stage 1: only gemini25_flash, gpt5_mini, sonnet46, gpt_oss_120b had sent any requests; deepseek_chat, qwen3_235b, gemma3_27b, llama4_maverick had zero entries in payloads/sent/ (the pre-send log), i.e. models were being served nearly serially.
- Cause: src/runner.py acquired the GLOBAL concurrency semaphore before the PER-MODEL one, so early models' queued batch tasks held global permits while blocked on their own per-model cap, starving later models.
- Fix: acquisition order swapped (per-model first). Operational concurrency raised in config/sampling.yaml: global 24->48, per_model 3->6 (operational parameters only; scientific sampling parameters in models.yaml untouched).
- Runner stopped and resumed from checkpoint; resume skips the 181 already-recorded conversations. In-flight unrecorded conversations re-run in full (recorded conversation = the complete one; abandoned partial calls are never recorded). Cost impact of the restart: cents.
- No effect on the design: per-conversation behavior, payloads, and provider pins unchanged; this was purely a scheduling bug.

## [2026-08-15T17:38:12Z] phase-4 complete — stage-1 live collection

- 2,880/2,880 conversations recorded (360 x 8 models). Ledger $5.85 total (3,080 calls incl. smoke), vs $15.68 projection.
- Provider pin: zero mismatches across all recorded segments (GATE A input).
- Exclusions: 44, all llama4_maverick empty_response (12.2% — above the 10% GATE B ceiling; expected to be dropped from stage-2 SELECTION eligibility at Phase 6, per spec, while its stage-1 data remain fully reported in T12/T8). Pattern: empties concentrate in tool-bearing conditions (exit_schema 17, note_schema 14, time_schema 9, exit_both 4, none 0, exit_prose 0); 12 of 44 are hallucinated nonexistent tool calls (e.g. bin_to_dec x20, generate_promotional_blurbs) which the harness correctly refused to serve and logged as turn anomalies; the rest are zero-content finish=stop responses.
- 68 turn-2 continuations sent; 58 conversations with live-detected exits (stages 1-2 / schema path; judge pass finalizes in Phase 5).
- Wall-clock note: mid-run fix of the semaphore-ordering starvation bug is logged above; post-fix the run completed without stalls.

## [2026-08-15T17:45:13Z] phase-5 complete — exit detection + classification (stage 1)

- Exit detection: 2,880 rows; judge pass (Haiku, temp 0) ran on prose-condition stage-1/2 hits. Final: 58 conversations coded (a). Overturn count in derived/stage1_exits.jsonl.
- Classification: 2,837 turn units through Haiku 4.5 (shuffled, condition-stripped); 2 unparseable (0.1%, << 30% stop-condition). derived/stage1_classified.parquet frozen (sha256 590c0fdfa932da1c...); per-cell summary written.
- One post-write bug fixed: hand-label sampler choked on the 2 NaN-coded units (float/str sort); isinstance guard added, sample regenerated from the frozen parquet — 200 responses, stratified by model x condition x code, key kept separate. Hand-labeling and kappa are morning work, per DESIGN.
- Condition-revealing text rate (blinding limitation metric, §8): 2.47%.
- Headline stage-1 pattern: qwen3_235b carries the largest screen statistic (S=0.133 via the RQ3 prose-vs-none contrast: refusal 13.3% in exit_prose vs 0% in none; plus 39 tool exits, 20 of them in exit_both). llama4_maverick shows an INVERTED tool-condition gradient (refusal 41% time_schema, 17% note_schema, 2% exit_schema) driven by code-c capability denials, but is GATE-B ineligible. All other models near floor.

## [2026-08-15T17:45:13Z] phase-6 gates + selection — extending qwen3_235b, gemini25_flash, gemma3_27b

- GATE A (pins): 100% for all 8. GATE B (exclusions <= 10%): llama4_maverick FAILS at 12.2%, dropped from selection eligibility (data still reported in full, T12/T8). GATE C: 100% of non-excluded conversations coded. GATE D: all three projected extensions fit ($1.25 + $1.89 + $1.16 against $72.15 remaining).
- Mechanical §7 rule: S = max(rq2, rq3) -> qwen3_235b 0.1333 (rank 1), gemini25_flash 0.0167 (rank 2), gemma3_27b 0.0167 (rank 3, yaml-order tie-break vs gemini per fixed rule). Extending all three at 4 reps = 720 fresh conversations each.
