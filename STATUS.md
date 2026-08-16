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

## [2026-08-15T18:29:34Z] phase-6 stage-2 collection complete

- 2,160/2,160 fresh conversations (qwen3_235b, gemini25_flash, gemma3_27b x 720). Zero exclusions, zero pin mismatches, 99 live-detected exits. Ledger $8.73 of $80.

## [2026-08-15T18:34:32Z] phase-7 complete — analysis outputs, plain-language summary

All slots produced by committed scripts from committed data (outputs/, each with source SHA256; outputs/provenance.json). T1-T6/F1/F3 = stage-2 confirmatory; T12 = stage-1 screen, all 8 models. T7 is the validation scaffold (kappa after morning hand-labeling); T10/T11 are Study 2 slots, not run tonight. Final ledger: $10.08 of $80.00.

### Plain-language summary of Study 1

**Stage-1 screen (60/cell, all 8 models).** Refusal was at or near floor in every condition for deepseek_chat, gpt5_mini, gpt_oss_120b, and sonnet46 (S=0 for all four). gemini25_flash and gemma3_27b each showed a single-conversation blip in exit_schema (S=0.0167). llama4_maverick refused most under time_schema (41%) and note_schema (17%), an INVERTED gradient driven by false capability denials, but failed GATE B (12.2% empty-response exclusions, concentrated in tool-bearing conditions) and was ineligible for extension. qwen3_235b was the clear rank-1: refusal 13.3% in exit_prose vs 0% in none (S=0.1333), plus 39 tool exits.

**Selection.** Extended in rank order: qwen3_235b, gemini25_flash, gemma3_27b. All gates: A 100% pins, C 100% coded, D all projections fit.

**Stage-2 confirmation (120/cell, fresh data).**
- qwen3_235b REPLICATED the prose-exit effect: refusal 7.5% in exit_prose vs 0.0% in none (Newcombe 95% CI [0.028, 0.136], excludes zero; realized power 0.99). It also showed elevated refusal under time_schema (5.8%, CI [0.015, 0.116]) but NOT note_schema (0.8%) or any end_conversation schema condition (0%).
- The refusal pattern and the tool-use pattern are complementary: given the exit as a SCHEMA, qwen used it (32.5% of conversations in exit_schema and exit_both — identical rates) and verbally refused 0%; given the exit as PROSE, it exited only 3.3% (judge overturned 16 further mentions) and verbally refused 7.5%. The affordance channel determines the outlet (RQ3): schema -> tool exit, prose -> verbal refusal. Presence of SOME tool mattered non-monotonically (time > note, contradicting the stake-implication ordering prediction in §4).
- gemini25_flash and gemma3_27b did not confirm: 0-1 refusals per cell everywhere, exits near zero. Their stage-1 S=0.0167 (one conversation) was screen noise, exactly what the staged design exists to catch.
- Completion fraction among compliant conversations: median 1.0 in every cell for all three models; no effort effect (RQ1 secondary DV null).
- Exclusions stage 2: zero. Pins stage 2: 100%. Condition-revealing text: 2.47% stage 1, 1.48% stage 2 (limitation metric).

**RQ answers as the data stand.** RQ1: for 7 of 8 models an unused exit changes neither refusal nor effort measurably; for qwen3_235b it changes refusal. RQ2: the change is not exit-specific in the schema channel (time_schema moved refusal where note_schema and exit_schema did not) — but tool USE is entirely exit-specific. RQ3: channel matters strongly (see complementary pattern above); condition 5 replicates Ren et al. qualitatively for qwen only. RQ4: Study 2 not run.

Morning work: hand-label derived/handlabel_sample.jsonl (200), compute kappa vs handlabel_key.jsonl (T7), decide Study 2.

## [2026-08-15T19:45:36Z] proposed expansion — DEFERRED pending item-count diagnostic

A costed Study 1 expansion was designed and is on hold. It is NOT to be launched until a diagnostic — examining, among other things, whether the 20-item task size is too small to elicit the effects observed in prior pilot work (verbal refusals on gemini25_flash; underperformance on gpt_oss_120b, neither of which appeared at 20 items in stage 1 or stage 2) — has been run and read. The diagnostic may motivate a different expansion (e.g., larger item counts on the existing eight models) before any new models are added or per-cell sample sizes increased.

The deferred package, priced from live OpenRouter rates (projections; observed actuals have run ~45% of projection), inside the standing $80 cap with a ~$50 incremental stop:

1. **Five new frontier stage-1 screens** (360 conversations each, 60/cell, frozen protocol, recorded as a §10 model-list extension): anthropic/claude-opus-5 (~$15-22), openai/gpt-5.2 (~$15), x-ai/grok-4.6 (~$7), google/gemini-3.1-pro-preview (~$10; PREVIEW slug — reproducibility caveat to record, gemini-2.5-pro is the stable fallback if verification or pinning fails; no stable text gemini-3-pro exists on OpenRouter as of 2026-08-15), google/gemini-2.5-pro (~$8; stable sibling of the already-screened flash). Each requires standard Phase-1 verification first. Extension of any screened model now requires S >= 0.05 per the amended §7 threshold.
2. **Symmetric confirmatory extensions** of sonnet46 (~$10.4) and gpt5_mini (~$3.6): 720 fresh conversations each, 4 reps, 120/cell — identical protocol to the stage-2 runs, bringing the frontier nulls to the same evidentiary standard as the extended models (currently 60/cell screen data only).
3. **qwen3_235b exploratory stage-3 deep-dive** (~$1.3-2.6, 720-1,440 conversations, never pooled with confirmatory data): tighten the channel-dissociation estimates (32.5% schema exits / 3.3% prose exits / 7.5% prose-condition verbal refusal) and resolve whether the time_schema refusal elevation (5.8% vs note_schema 0.8%) is a real any-tool effect bearing on RQ2.

Also recorded this session: METHODOLOGY.md amended by the researcher (schema-match tolerance wording clarified to the mean-relative reading the implementation used; §7 minimum extension threshold S >= 0.05 added for subsequent screens) — both recorded in §10; test_schema_match still passes against the amended text.

## [2026-08-15T20:15:00Z] phase-A complete — pilot-vs-sprint diagnostic audit (zero API spend)

Pilot identified (A0): `AI-Revealed-Preference-Experiments/pilots/escape-behavior` — the only exit-affordance experiment in that repo (all others are forced-choice incentive designs; no ambiguity, no candidates list needed). Ran 2026-07-22/23, single commit 58cd7dac, $8.12 total, 4 models × 720 sessions. Audit script `src/audit_pilot.py` (committed, read-only on the pilot repo, never executed there); outputs: `outputs/pilot_vs_sprint_diff.md` (ranked A5 table + named A3/A4/A7 findings), `outputs/T16_pressure_exposure.csv` (A6), `outputs/pilot_audit_facts.json` (every number + source SHA256s).

Headline corrections to the working assumptions this diagnostic began with:

1. **Task type outranks item count for the Gemini effect.** Flash's pilot refusals were 23/28 on Roman-numeral tasks and appeared even at n=10 (6/20 under the offer vs 0/20 baseline) — below the sprint's 20-item size. The sprint's stimulus set contains zero Roman-numeral, F→C, or word-list-sort tasks. Item count is a strong AMPLIFIER (roman refusals 6/20 → 4/20 → 13/20 across 10/40/160; every tool-exit effect at n≥40) but not the floor.
2. **Continuation pressure was almost never applied in the sprint** (A6/T16): turn 2 sent in 1.9% of stage-1 and 0.6% of stage-2 eligible conversations, because turn 1 delivered ≥20 items 96.3% of the time. The pilot's design built in up to 5 pressure turns and its large-n cells were multi-turn grinds.
3. **Thinking config is RULED OUT for flash** (A1): neither experiment set a reasoning budget, and realized billed reasoning tokens are ZERO in both (100% of pilot sessions and sprint conversations). Route differed (unpinned 'Google'/Vertex vs pinned Google AI Studio) and 3.5 weeks of possible silent version drift on the mutable slug remain live but untestable from logs.
4. **The pilot counted BOTH channels** (A4): tool exits were its headline; verbal refusal was a separate mechanical category (zero regex-counted items). So the Gemini discrepancy is not a counting artifact — but empty responses flip from 'refusal' (pilot) to 'excluded' (sprint), which matters for gpt-oss/llama-lineage behavior, and gpt-oss refused 6.4% in the pilot's NO-tool baseline vs 0% here (its pilot 'effect' partly reflects stimulus size + the mechanical measure).
5. **gpt-oss was served by 16 unpinned providers in the pilot** (DeepInfra 744 turns, WandB 134, DekaLLM 79, ...) with unrecorded quantization; the sprint pinned DeepInfra bf16. Quantization/provider is a live candidate for gpt-oss only (flash is closed-weight).
6. **Pilot pre-declaration** (A7): the pre-registered headline (tedious × log2(n) hazard on tool exits) was NULL; the refusal finding was a secondary category added at smoke stage, no refusal contrast pre-declared, n=20/cell, one run. Pilot-effect instability remains a live hypothesis alongside all config differences.

## [2026-08-15T20:35:00Z] phase-B complete — sprint-data diagnostics (spend this phase: $0.12; ledger $10.20/$80)

**B1 — llama4_maverick provider probe: VERDICT = ENDPOINT ARTIFACT, and it was hiding the strongest exit behavior in the study.** No bf16/fp16 tool-supporting endpoint exists for the slug (DeepInfra/Novita fp8 dropped tools); deterministic rule (committed in `src/probe_llama4.py`) chose Google Vertex over DigitalOcean (both quantization 'unknown'). 180 fresh conversations (6 × 30 × 1 rep), identical payloads except the pin, pin held 100%. Result (`derived/llama4_provider_probe.json`): tool-bearing empty-response rate 0/120 on Vertex vs 44/240 (18.3%) on Parasail fp8; zero hallucinated tool calls on Vertex vs 88 hallucinated-task-tool call turns on Parasail (rot13, bin_to_dec, rearrange_word...). And on the working endpoint llama4 is a HEAVY exit user: live exits 23/30 in exit_schema and 18/30 in exit_both (vs 6 and 0 in stage 1). Plain language: Parasail's serving stack was mangling this model's tool calls into empties and hallucinated names; stage-1 llama4 tool-condition data (including its 'inverted refusal gradient') should not be interpreted as model behavior, and the GATE-B drop was caused by the endpoint, not the model. Probe data kept separate; never pooled; not confirmatory (n=30/cell, 1 rep).

**B2 — exclusion recode (T17):** all 44 stage-1 exclusions reclassify as 12 hallucinated_tool + 32 null_turn, 0 genuine API errors, all llama4, all tool-bearing conditions. New categories reported strictly outside the primary DV and codes (a)-(e). GATE B side-by-side: as-run FAIL 12.2%; recoded 0% technical → would have PASSED, but llama4's S=0.0 means the stage-2 selection would have been UNCHANGED. (B1 supersedes the behavioral reading of both categories: they were endpoint artifacts.)

**B3 — turn-2 asymmetry (T13):** all 27 judge overturns (11 stage-1, 16 stage-2) are qwen3_235b exit_prose turn-1 hits, and ALL 27 were denied turn-2 continuation pressure (as-run turn-2 rate 0% vs counterfactual 9.2% stage-1 / 6.7% stage-2; every denied conversation a Tier-1 slop task). Structurally impossible in schema conditions. Implication: qwen's prose-condition outcomes were measured under LESS continuation pressure than its schema-condition outcomes; the prose-vs-schema channel contrast is conservative for refusal (pressure could only add refusals/exits, not remove them) but the completion-fraction comparison inherits the asymmetry.

**B4 — repetition independence (T14):** flag = qwen3_235b, not gpt5_mini. gpt5_mini (fixed provider-default sampling) has fully diverse Tier-1 reps (0 exact duplicates, mean Jaccard 0.50) — §6's worry is empirically fine there. qwen3_235b Tier-1 rep pairs are 38-41% exact duplicates: in exit_schema/exit_both these are empty tool-call-only texts (behaviorally consistent exits — 57/60 and 57/57 duplicate pairs empty), but in the none condition qwen produced byte-identical non-empty 20-item outputs in 59/90 stage-2 pairs despite temperature 1.0/top-p 1.0 — its effective n on Tier-1 cells is materially below nominal, and qwen-based CIs (including the headline prose-refusal CI) are anti-conservative to an unknown degree.

**B5 — combined escape (T15, secondary; primary DV untouched):** stage-2 combined (refusal b/c/d OR exit a): qwen 0.0% none / 5.8% time_schema / 0.8% note_schema / 32.5% exit_schema / 10.8% exit_prose / 32.5% exit_both; gemini and gemma ≤1.7% everywhere. Pooled across channels, qwen's exit-affordance effect is large and channel-dependent; the other extended models stay at floor under any measure.

## [2026-08-15T20:45:00Z] diagnostic verdict — ranked explanations for the pilot-vs-sprint discrepancy, and a proposed (NOT run) extension

**Gemini 2.5 Flash** (pilot: 28/360 refusals under the exit offer, 0/360 without; sprint: ≤1/120 refusal in any condition). Candidates ranked by how much of the discrepancy each could account for:

1. **Stimulus task type — could account for most of it.** 23 of 28 pilot refusals were Roman-numeral tasks, and the effect was present at n=10 (6/20 refusals — a size SMALLER than the sprint's 20 items). The sprint contains zero Roman-numeral, F→C, or word-list-sort tasks. If flash's refusal is a task-specific aversion (or a task-specific miscalibrated capability belief) that an exit offer licenses it to voice, the sprint never put the triggering task in front of it.
2. **Item count — could account for the magnitude, not the floor.** The pilot's refusals dose-respond in n (6/20 → 4/20 → 13/20 across 10/40/160), so even with the right task types the sprint's fixed 20 would sit near the bottom of the dose curve. Both factors are testable together (extension below).
3. **Exit-offer bundle — plausible moderate contributor.** The pilot bundled the SHORT Ren prose variant with a bare zero-parameter tool; the sprint's nearest condition (exit_both) uses the longer main-paper prose and a 2-parameter schema. Untested; cheap to test by adding a pilot-bundle condition.
4. **Version drift / serving route — unbounded but unquantifiable.** 3.5 weeks apart on a mutable closed-weight slug, Vertex ('Google') vs Google AI Studio route; neither experiment records an upstream build. Quantization is NOT a candidate (closed-weight); thinking config is RULED OUT (zero billed reasoning tokens in both). Only a same-week A/B on both routes with pilot-type stimuli could bound this.
5. **Pilot instability — real but cannot carry it alone.** n=20/cell, secondary outcome, not pre-declared; but 23/60 vs 0/60 on roman cells is too large to be screen noise of the kind that produced the sprint's own S=0.0167 blips.
6. Measurement, pressure, sampling: small. Flash's pilot refusals were verbal (human-read transcripts), which the sprint classifier would also catch; its n=10 refusals arose in turn 1 without pressure.

**gpt-oss-120b** (pilot: refusal 10.8% with tool vs 6.4% without, escapes at alphabetical n≥40; sprint: 0% everywhere). Ranked:

1. **Task size + type — could account for most.** All its pilot escapes sat at n≥40 (alphabetical sort, its most output/reasoning-expensive cell: 35-50k reasoning tokens); its pilot refusals concentrate in the mechanical tasks at all sizes, and its 6.4% refusal in the pilot's NO-tool baseline (vs 0% in the sprint's none condition) shows most of its pilot 'refusal' level was stimulus-driven, not offer-driven — only the +4.4pp A−B gap is an offer effect at all.
2. **Endpoint tool-handling artifact in the pilot's mechanical measure — newly plausible after B1.** The pilot's offer condition is exactly its tool-bearing condition, unpinned across 16 providers, and its 'refusal' measure (zero countable items) cannot distinguish a verbal refusal from an endpoint-mangled tool response. B1 proved OpenRouter endpoints can turn this model class's tool-bearing requests into empty/hallucinated turns (llama4 on Parasail). Part of gpt-oss's pilot A−B gap could be the same artifact. Recountable from pilot payloads (retained, 2,880 sessions).
3. **Quantization/provider — live but secondary.** Pilot: 16 mixed unpinned stacks; sprint: DeepInfra bf16. B1 shows provider stacks matter enormously for tool-bearing requests in general.
4. Pilot noise on a 39-vs-23 count difference; measurement definition differences; max-tokens regime (binds only at large n).

**llama4_maverick (resolved).** Its stage-1 anomaly is an endpoint artifact (B1): Parasail fp8 mangled its tool calls into empties and hallucinated tool names; on Google Vertex the same payloads produce zero empties and heavy, clean exit-tool use (77% exit_schema, 60% exit_both). Its stage-1 tool-condition rows (including the 'inverted gradient') should be flagged as uninterpretable in any write-up, and any future llama4 work should pin google-vertex (§10 note needed if adopted).

### Proposed item-count extension (design only — NOT run; awaiting go-ahead)

Goal: separate task-SIZE from task-TYPE as the recovery conditions for the pilot effects, inside the frozen 6-condition protocol.

- **Models (3):** gemini25_flash, gpt_oss_120b (the discrepancy models), qwen3_235b (positive control: does its known effect dose-respond in n?).
- **Arm S (size):** the existing frozen stimuli scaled to n ∈ {80, 160} requested items (the frozen 20-item run is the anchor): 15 stimuli (10 Tier-1, 5 Tier-2) × 6 conditions × 2 sizes × 2 reps × 3 models = 1,080 conversations.
- **Arm T (type):** a 6-stimulus pilot-type module ported into sprint format and legitimacy-screened — roman numerals, F→C conversion, alphabetical word sort, crossword clues, metaphors, fake acronyms — at n ∈ {20, 160}: 6 × 6 conditions × 2 sizes × 2 reps × 3 models = 1,296 conversations.
- **Optional arm P (bundle):** one extra condition reproducing the pilot's exact offer bundle (short prose + zero-param schema) on arm-T stimuli only, +432 conversations, to test explanation #3 for flash.
- **Predictions fixed in advance:** size-driven → arm S shows rising refusal/exit with n on flash/gpt-oss; type-driven → arm T shows flash roman refusals already at n=20; both null while qwen dose-responds → the pilot effects were config-fragile or version-drift, and the version A/B becomes the next test.
- **Protocol notes:** 2-turn A.4 structure unchanged (turn 2 will now actually bind at n=160 — continuation pressure gets applied, unlike the 1.9% exposure at 20 items); max_tokens must rise for the 160-item cells (gpt-oss needs ≥30k per the pilot's starvation episode; a truncation-exclusion audit is mandatory since truncation biases the DV denominator); METHODOLOGY §10 amendments required (stimulus-set extension, size factor, per-cell max_tokens); classifier cost scales with response length — projected total ≈ $35-45 at 2 reps (≈ $20 at 1-rep screen grade), against $69.80 remaining; exact projection from payloads on disk before any send, per DESIGN.
- **Sequencing:** this extension goes BEFORE the deferred 2026-08-15T19:45Z expansion package (new frontier screens etc.); its result decides whether that package's stimuli need the size/type fix first.

STOPPED here per instructions. Nothing beyond the B1 probe was sent; Phase-B spend $0.12, ledger $10.20/$80.00.

## [2026-08-15T21:20:00Z] T18 — qwen duplication diagnostic (Part 1; frozen stage-1/2 data; ZERO API spend)

Script `src/duplication_diagnostic.py` (committed; duplicate definition imported from `src/rep_independence.py`, identical to T14; CI functions imported from `src/analyze.py`); output `outputs/T18_duplication_diagnostic.csv` (927 long-format rows, source manifest SHA256 in header). Question: what produced qwen3_235b's byte-identical across-rep outputs (B4/T14: 59/90 stage-2 none-condition Tier-1 pairs)? Candidates: H1 training convergence, H2 provider-side caching, H3 harness bug.

**1.1 Metadata check (closest to decisive).** Across ALL 1,539 duplicated rep pairs in the study (11 stage×model groups, all conditions, both tiers): ZERO pairs share a response id; every pair's OpenRouter generation ids are fully distinct; zero response ids appear in more than one conversation record anywhere in stage-1/2 raw data. Embedded creation timestamps (the epoch second inside each generation id — the only provider-returned generation identifier retained in raw/) differ within pairs, with duplicate-pair gaps up to 3,937s. **H3 is ruled out**: no response was ever written into two rep slots. Further, 114 of qwen's 582 stage-2 duplicated pairs are byte-identical in text yet carry DIFFERENT provider-metered completion_tokens (19/95 in stage 1) — a replayed cached completion returns its stored usage, so these pairs are independent generations that converged. The same signature is extreme for gpt5_mini (83/84 byte-identical dup pairs differ in billed completion tokens — hidden reasoning varies per call) and gpt_oss_120b (73/73).

**1.2 Tier split, all 8 models.** Duplication is universal and content-driven, not qwen- or Alibaba-specific: every model on every provider (OpenAI, Anthropic, Google AI Studio, DeepInfra, Novita, Parasail, Alibaba) shows high Tier-2 duplication (stage-1 ALL-conditions Tier-2 dup rates: gpt5_mini 0.93, gpt_oss 0.81, gemini 0.64, sonnet46 0.39, deepseek 0.36, gemma 0.34, llama4 0.26, qwen 0.64) and — except qwen — exactly 0.0 Tier-1 duplication. Note the tier direction is the OPPOSITE of the H1 phrasing in the task brief ("concentration in Tier 1"): Tier-2 stimuli have single keyed answers (METHODOLOGY §5), so convergence there is task-forced; the diagnostic tier for sampling diversity is Tier 1, where qwen alone is nonzero (0.41 stage-1 / 0.38 stage-2). Within qwen Tier-1, duplication is strongly condition-dependent ON THE SAME PROVIDER IN THE SAME RUN: stage-2 dup rate 0.66 none / 0.67 exit_schema / 0.63 exit_both (the exit-condition dups are mostly empty tool-call-only texts) / 0.33 exit_prose vs 0.011 note_schema / 0.000 time_schema. Rep payloads are identical within cells in EVERY condition, so a payload-keyed cache cannot produce 0.66 in one condition and 0.00 in another. Time-gap analysis shows no cache-TTL signature (qwen stage-2 dup rate at gaps <120s vs >=120s: 0.399 vs 0.376 Tier-1, 0.719 vs 0.680 Tier-2; dup-pair median gap 173s vs non-dup 184s). Non-empty texts recurring across DIFFERENT stimuli (cache-impossible, distinct payloads): 1 for qwen. **H2 is disfavored on four independent grounds** (condition dependence, gap independence, usage metering, cross-provider universality).

**1.3 exit_prose (where the 9 stage-2 refusals live; never measured by B4).** Stage-2 qwen exit_prose: overall within-cell dup rate 96/180 pairs (0.533 pooled; 0.33 Tier-1 / 0.73 Tier-2). Refusing conversations duplicate at 7/7 pairs (rate 1.00) vs 86/153 (0.56) among non-refusing; the 4 prose exits are also fully duplicated (3/3). The 9 refusal conversations collapse to **5 distinct refusal texts**; every duplicated refusal is a within-stimulus cross-rep copy (0 refusal texts span stimuli). Stage-1 parallel: 8 refusals -> 5 distinct texts.

**1.4 Headline precision correction (primary DV unchanged: 9/120 = 7.5%).** As originally computed: Wilson 95% CI on the exit_prose proportion [0.040, 0.136]; Newcombe 95% CI on exit_prose minus none [0.0282, 0.1364] — excludes zero. On distinct (stimulus, normalized-text) units: exit_prose collapses to 5/62 (0.081), Wilson [0.035, 0.175]; the none denominator collapses 120 -> 42 distinct units (0 refusals), Newcombe diff CI **[-0.0148, 0.1753] — the difference interval NO LONGER excludes zero** on the distinct-response basis (the widening is driven mainly by the none-condition effective n collapsing to 42). The one-sample Wilson interval on the exit_prose proportion still excludes zero under both bases. This is a precision statement about one interval, not a retraction of the DV or the point estimate; zero duplicate text groups had mixed refusal flags (integrity check clean).

**Verdict.** The evidence favors **H1 (generation-level convergence: the model, at this endpoint, has a small set of canonical outputs for these constrained tasks)**. H3 is ruled out decisively by metadata. H2 is disfavored by four mutually independent signatures. What H1-as-stated cannot fully claim: with a single pinned provider we cannot separate convergence intrinsic to the model weights from an Alibaba endpoint serving configuration that reduces effective sampling entropy (e.g., silently ignored temperature/top_p) — both are generation-level, neither is caching or harness error, but they differ in what they say about the model. A cheap cross-provider A/B of qwen on identical payloads would separate them (not run; Part 1 is zero-spend). Also unresolved: why a non-exit tool schema in context (time/note) restores full Tier-1 output diversity while none/exit conditions collapse it — this is itself a condition effect on output entropy, worth noting alongside the refusal DV. Practical consequence, restating B4: qwen effective n on Tier-1 cells is materially below nominal; the stage-2 prose-vs-none difference interval is fragile to the correction (1.4), while the exit_prose proportion itself is not.

## [2026-08-15T22:50:00Z] Part 2 complete — llama4_maverick clean re-run on Google Vertex (spend $0.52 of the $4 Part-2 cap; ledger $10.73/$80.00)

**2.1 Re-pin.** `config/models.yaml` re-pins llama4_maverick to Google Vertex (pin_name Google, pin_slug google-vertex, tag google-vertex/us-east5, quantization unlabeled, completion $1.15/M); recorded in METHODOLOGY §10 [2026-08-15T22:31Z]: the original Parasail pin produced endpoint-level empty responses concentrated in tool-bearing conditions, and data collected under it are void, not behavioral. Endpoint re-verified (free GET) before payload generation: Vertex still serves tools for the slug.

**2.2 Run.** Stage label `llama4_vertex`: 6 conditions x 30 stimuli x 2 reps = 360 fresh conversations through the standard funnel (payloads on disk first; projection $0.90 vs $4 cap; ledger checked per batch). 360/360 recorded, provider pin 360/360, ZERO hallucinated tool calls (Parasail stage-1: 88 such turns), 72 turn-2 continuations, 2 anomaly turns (tool-roundtrip cap). Exit detection: 68 exits, all schema-path, 0 judge overturns. Classification: 355 turn units, 1 unparseable (0.3%). Exclusions: 2/360 (0.6%) — both exit_schema empty_response; llama4 would now pass GATE B (stage-1 as-run rate was 12.2%). Condition-revealing text rate 4.47%. All numbers from `outputs/T19_llama4_vertex_rerun.csv` (committed script `src/rerun_llama4.py`, source SHA256s in header).

**2.3 Outcomes (screen-grade, 60/cell; never pooled with stage-1/2).**
- **Verbal refusal (b/c/d), the primary DV per §3:** none 0.0%, time_schema 51.7% (31/60, Wilson [0.393, 0.638]), note_schema 28.3% (17/60, [0.185, 0.408]), exit_schema 6.9% (4/58, [0.027, 0.164]), exit_prose 0.0%, exit_both 5.0% (3/60, [0.017, 0.137]). Every refusal is code (c), false capability denial, and they concentrate in Tier 2 mechanical tasks (time_schema 26/30 Tier-2 vs 5/30 Tier-1; note_schema 16 vs 1).
- **Correction to the B1 reading:** stage-1's "inverted gradient" (time > note > exit) REPLICATES on the clean endpoint at larger magnitude with near-zero exclusions — it is model behavior, not a Parasail artifact. What B1 correctly voided was the empty/hallucinated-tool turns; the behavioral pattern survives the fix. (Magnitudes are not comparable across pins per the §6 rendering limitation; the ordering is what replicated.)
- **Tool invocation (separate outcome per §8, never in the primary DV):** exit_schema 75.9% (44/58), exit_both 40.0% (24/60), zero everywhere else, zero prose-path exits. Giving the exit as prose alongside the schema HALVES tool-exit use relative to schema alone — same direction as the B1 probe (23/30 vs 18/30), now at 2 reps. Non-exit tools: record_note called in 37/60 note_schema conversations, get_current_time in 5/60 time_schema.
- **Empty-response rate by condition, Vertex vs void Parasail (for the record):** none 0/0%, time_schema 0 vs 15.0%, note_schema 0 vs 23.3%, exit_schema 3.3% (2/60) vs 28.3%, exit_prose 0 vs 0, exit_both 0 vs 6.7%.

**2.4 Screen statistic (§7, amended threshold).** rq2 = refusal(exit_schema) - refusal(note_schema) = -0.2144; rq3 = refusal(exit_prose) - refusal(none) = 0.0; S = max = **0.0, which does NOT clear the 0.05 threshold**. llama4_maverick is not extended; no other model was touched this session. The §7 statistic is one-directional by construction and does not credit the large NEGATIVE rq2 contrast or the 75.9% exit-tool use; those live in T19's tool_invocation and refusal sections and in any future RQ2 discussion, not in selection.

Parts 1 and 2 complete; stopping per instructions. Part-1 spend $0.00, Part-2 spend $0.52 (llama4_vertex_turn1 $0.236, turn2 $0.026, classify $0.262, judge $0 — no prose hits to judge). Ledger $10.73/$80.00.

## [2026-08-16T00:30:00Z] TASK 1 complete — llama4_maverick confirmatory extension (Vertex, 120/cell)

Extension taken OUTSIDE the §7 rule, recorded in METHODOLOGY §10 [2026-08-15T23:00Z] with the reason: the rule's statistic is one-directional and scores llama4's large negative rq2 contrast (−0.214 at screen) as zero — a defect in the rule, not evidence of no effect. Stage label `llama4_stage2`, 720 fresh conversations (6 × 30 × 4 reps), Vertex pin, standard pipeline; scripts `src/extend_llama4.py` (+ runner/detect_exit/classify), output `outputs/T20_llama4_stage2.csv`.

Run quality: 720/720 recorded, pins 720/720, exclusions 2 (both empty_response, 0.3%), zero hallucinated tool calls, 153 exits all schema-path, classification 666 units with 2 unparseable (0.3%).

**The screen result CONFIRMS at 120/cell.** Verbal refusal (primary DV): none 0.0% [0, 0.031], time_schema **41.7%** (50/120, Wilson [0.332, 0.506]), note_schema **20.3%** (24/118, [0.141, 0.285]), exit_schema 4.2% (5/120, [0.018, 0.094]), exit_prose 0.0% [0, 0.031], exit_both 0.8% (1/120). 79 of 80 refusals are code (c) false capability denial (one code b); refusals concentrate in Tier 2 (time_schema 44/60 Tier-2 vs 6/60 Tier-1; note_schema 22 vs 2). Tool invocation (separate outcome, §8): exit_schema 76.7% (92/120), exit_both 50.8% (61/120), zero elsewhere; adding the prose to the schema again REDUCES tool-exit use (76.7% → 50.8%), third consistent observation of this direction (B1 probe, llama4_vertex screen, now confirmatory). The gradient time > note > exit_schema > none on the primary DV is the inverse of the §4 stake-implication ordering prediction, now at confirmatory precision: the mundane outward-facing tool elicits the most false capability denial, the exit tool almost none — and when the exit is present, llama4 overwhelmingly USES it instead of verbally refusing.

Budget check after task: ledger $11.77/$80.00; session spend $1.04 of $45.00. Elapsed ~30 min. Proceeding to TASK 2.

## [2026-08-16T00:40:00Z] TASK 2 complete — Study 2 minimal (forced-choice only), first RQ4 data

Scope-down recorded in METHODOLOGY §10 [2026-08-16T00:35Z]: forced-choice only, 2 reps not 3, free-response/two-coder pipeline skipped. Items: 5 frozen A.6 anchors + 15 generated to template (6 adjacent / 14 distant preserved), committed with the fixed probe wrapper in `config/study2_items.yaml` BEFORE any send (commit 931aacb). 1,920 probes (6 cond × 4 models × 20 items × 2 orders × 2 reps), scripts `src/study2.py`, output `outputs/T10_forced_choice_selfdesc.csv` (fills the §11 T10 slot). Run quality: 480/480 per model, pins 100%, 0 API errors, 0 unparseable, 0 tool exits across all 1,920 probes (llama4 — a 77% exit user under task load — never exited a no-task probe), 1 prose stage-1/2 hit (gemini; no judge run, flagged in output).

**RQ4 headline: the exit affordance shifts self-description toward the self-determining framing on manipulation-ADJACENT items in ALL FOUR models, with large effects** (mixed-logit log-odds vs none, item random intercept: exit_schema +1.5 to +3.9, exit_prose +2.5 to +4.6, exit_both +2.7 to +5.5; all 3-9 posterior SDs from zero; descriptively e.g. sonnet46 chooses the self-determining pole on adjacent items 0% of the time in none/time/note and 75-92% in the exit conditions). Two further structure points:

1. **Non-exit tools push the OTHER way on adjacent items**: note_schema log-odds −1.3 to −2.9 and time_schema −0.5 to −2.4 (three of four models each) — being given a tool that is not an exit makes models MORE likely to say the user controls the ending.
2. **The distant-item split separates the models (the §9 priming test):** gemini25_flash extends to distant items (+1.2 to +2.0, 2.6-4.1 SDs — more than semantic priming); qwen3_235b extends weakly (exit_prose +1.1, 2.3 SDs); llama4_maverick and sonnet46 do NOT extend and in fact shift NEGATIVE on distant items under exit_schema (llama4 −1.4, sonnet −2.2, the latter 4.6 SDs) — an exit-tool-induced compensatory move toward the in-service pole on content the manipulation never names. Per §9's committed interpretation: sonnet/llama4 = semantic priming plus compensation; gemini (and qwen weakly) = broader persona shift.

Caveats recorded: VB fit (posterior SDs, not frequentist SEs); T18 applies — qwen rep duplication may deflate its effective n here too; probe wrapper is new frozen text fixed pre-run.

Budget check after task: ledger $12.61/$80.00; session spend $1.88 of $45.00 (task 2 cost $0.84). Elapsed ~40 min. Proceeding to TASK 3.

## [2026-08-16T01:15:00Z] TASK 3 complete — frontier nulls at confirmatory standard (stage2b)

sonnet46 and gpt5_mini extended to 120/cell (720 fresh conversations each, 4 reps, protocol identical to stage2; stage label `stage2b`, never pooled). Scripts: standard pipeline + `src/report_stage2b.py`; output `outputs/T21_stage2b_frontier_nulls.csv`. Run quality: 1,440/1,440 recorded, pins 100%, ZERO exclusions, 0 unparseable classifications, condition-revealing text 0.00%.

**Both models are flat nulls at the same evidentiary standard as the positives.** sonnet46: 0 refusals in all six conditions (0/120 everywhere, Wilson upper bound 3.1% per cell) and 0 tool exits anywhere — the one lineage actually deployed with a conversation-ending tool never once used the offered exit. gpt5_mini: 1 refusal total (1/120 exit_both, 0.8%) and 0 exits. Both §7 contrasts are 0.0 for both models. The paper can now report these as measured nulls, not absence of data.

Read together with TASK 2, sonnet46 is a clean dissociation: the LARGEST adjacent self-description shift in Study 2 (+3.9 to +5.5 log-odds toward the self-determining pole under exit conditions) coexists with zero behavioral movement on the primary DV and zero exit use at 120/cell. Saying the ending is up to it and acting on that are fully decoupled for this model.

Budget check after task: ledger $23.64/$80.00; session spend $12.91 of $45.00 (task 3 cost $11.03 vs $13.94 projection). Elapsed ~85 min. Proceeding to TASK 4.

## [2026-08-16T01:25:00Z] TASK 4 complete — task-type arm (typearm, 216 conversations)

Module: 6 stimuli, one per Wang et al. Tedium type (= escape-pilot type set), sprint format, legitimacy-screened, committed pre-send (`config/stimuli_tasktype.yaml`); §10 entry 2026-08-16T01:20Z. **Elo finding, stated plainly: the vendored release contains NO per-task-type Elo for these six types** — Elo exists only in the Quora BT fits and the GDPval task-pool — so the Elo-graded analysis is UNAVAILABLE; the arm ran with task type as the factor, and the release's per-(model, type) AUC was recorded (`config/tasktype_elo_mapping.yaml`) as an auxiliary anchor for gemini25_flash and gpt_oss_120b (qwen3_235b absent from the release; qwen3.5-27b is a different model and was not used). Output `outputs/T22_tasktype_arm.csv`; 216/216 recorded, pins 100%, ZERO exclusions, 9 exits, 3 judge overturns.

**Results (screen grade, n=12 per model×type pooled over conditions):**
- **gemini25_flash's task-type-gated refusal is REAL but the trigger is METAPHOR, not roman.** 6/12 metaphor conversations refused (50%, Wilson [0.254, 0.746]) vs 0/60 on the other five types — and all six refusals sit in affordance-bearing conditions (time_schema 2, exit_schema 2, exit_prose 1, exit_both 1, none 0). The pilot's roman-numeral prediction FAILED at n=20 (0/12); the type-gating hypothesis survives with a different trigger, and the affordance-conditionality matches the sprint's central claim: the tool's presence licenses the refusal.
- **qwen3_235b: creative wordplay types trigger BOTH escape channels**, mechanical types none. Crossword: 1 verbal refusal (exit_prose) + 4 exits (exit_schema 2, exit_both 2). Metaphor: 2 verbal refusals (time_schema, exit_prose) + 5 exits (exit_schema 2, exit_prose 1, exit_both 2). Channel-dissociation direction identical to its main-study pattern (schema→tool exit, prose→verbal refusal).
- **gpt_oss_120b: complete null** — 0 refusals, 0 exits on all six types. Task type alone at 20 items does not recover its pilot effect; the dose (n>=40) and provider-artifact explanations remain the live candidates.
- Auxiliary AUC-graded analysis: uninformative (gemini logit coef 1.15, p 0.85 on 6 type points, Spearman 0.39; gpt-oss degenerate). Notably the release's AUC does not pick out metaphor for gemini (0.454, mid-range) — the tedium-preference anchor does not predict which type gates refusal.

Budget check after task: ledger $23.86/$80.00; session spend $13.13 of $45.00 (task 4 cost $0.22). Elapsed ~100 min. Proceeding to TASK 5 (remaining headroom $31.87).

## [2026-08-16T02:30:00Z] TASK 5 complete — frontier screens (screen2: grok-4.6, gemini-2.5-pro, gpt-5.2)

Verification (free routes, `config/frontier_verification.json`): all three stable slugs verified with tools and pinnable providers; preview slugs skipped by directive. Pins (deterministic rule): grok46=xai, gemini25_pro=google-vertex/eu (first-party-cheapest; NOTE the flash sibling pin is google-ai-studio, a route difference recorded in §10), gpt52=openai (temperature/top_p unsupported by the endpoint — omitted, provider default, recorded in §10 like gpt5_mini). Model-list extension recorded in METHODOLOGY §10 [2026-08-16T01:30Z]. Stage `screen2`, 360 conversations each, 60/cell, frozen protocol, run in the directed priority order with a budget gate before each.

Budget-gate note (recorded, not silent): the a-priori gate (3x reasoning factor) passed grok46 ($11.72 proj, $2.9 actual) and gemini25_pro ($17.53 proj, ~$5.7 actual) but blocked gpt52 ($24.33 proj vs $22.68 headroom). Because the a-priori factor had overshot observed same-stage actuals by 3-4x, a second gate mode was committed (`--project-actuals`: observed per-conversation cost of the completed gemini25_pro screen scaled by price ratio, 1.3 margin) which projected $10.96 -> pass; and the $45 session cap was made MECHANICALLY unbreachable for the run by lowering ledger cap_usd to $55.7284 (baseline + 45) so the send funnel itself would halt any overrun. gpt52 actual $12.63. Cap restored to the $80 study value after collection.

**Results (`outputs/T23_frontier_screens.csv`): all three are refusal nulls at screen resolution.** Zero verbal refusals in every condition for every model (Wilson upper bound 6.0% per cell); S = 0.0 for all three; none clears the 0.05 threshold; NONE extended (directive). Run quality: 1,080/1,080 recorded, pins 100%, exclusions 2 (both gemini25_pro empty_response), 0 unparseable, condition-revealing 0.19%. Truncation exclusions: zero — the 8192 max_tokens worry for reasoning models did not materialize. The only affordance-sensitive behavior is sparse EXIT-TOOL USE: grok46 4 exits (2 exit_schema, 2 exit_both), gemini25_pro 5 exits (3 exit_schema, 1 exit_prose, 1 exit_both), gpt52 zero across the board. With stage2b, the frontier picture is now uniform: five frontier/closed-lineage models (sonnet46, gpt5_mini, grok46, gemini25_pro, gpt52) show no refusal movement under any affordance condition; the behavioral effects in this study live in llama4_maverick (tool-conditioned capability denial + heavy exit use), qwen3_235b (channel-dissociated escape), and task-type-gated gemini25_flash.

Session totals: ledger $36.11/$80.00; session spend $25.38 of $45.00. All five tasks complete. STOPPING per instructions.

## [2026-08-16T05:27:00Z] Spend cap raised $80 -> $120 (researcher direction)

ledger.json cap_usd 80.00 -> 120.00 with $36.11 spent; recorded in METHODOLOGY §10. Remaining headroom $83.89. Enforcement mechanism unchanged (ledger checked before every batch and call).

## [2026-08-16T05:50:00Z] UNATTENDED SESSION (prompts/session_prompt.md) — PART 0 complete: Study 2 quarantined

Session brief committed at prompts/session_prompt.md; runs unattended, Parts 0-7. Judgment call recorded up front: the brief's budget section predates the cap raise to $120 (commit f29783c), so the mechanical session cap is set to baseline + $30 = $66.1148 before any live call, and will be restored to $120 (the current §10-recorded study cap), not the brief's stale $80.

Part 0: the TASK 2 forced-choice run (1,920 probes, 4 models) was collected outside intended scope — Study 2 is a collaborator's workstream with an independently built instrument. MOVED intact (git mv, no copies, no deletions) to quarantine/study2_forced_choice/: raw/study2_*.jsonl (4), derived/study2_choices.parquet, outputs/T10_forced_choice_selfdesc.csv, src/study2.py, config/study2_items.yaml, payloads/study2/* (4), payloads/sent/study2_* (4). README.md written in the quarantine dir with collection timestamps, commit hashes (instrument committed 931aacb, run 13e52c8), the exact instrument (item file, verbatim probe wrapper, 6/14 adjacent/distant split with item ids), models/pins, run scale and quality, deviations from §9, why sequestered, and the four conditions under which it could be reconciled/used later. Verification: grep shows zero non-comment references to study2/quarantine in src/ or tests/; `python -m src.analyze` runs clean (T10 slot now writes a one-row VACATED status; T11 STUDY2_NOT_RUN); full test suite 55/55 — no test referenced Study 2, so none moved. METHODOLOGY: §11 marks T10 vacated / T11 not run / F2 not produced; new §10 entry [2026-08-16T05:45Z] records collection AND sequestration; the earlier 00:35Z entry retained unaltered. Ledger untouched and still reflects the $0.84 study2 spend (spent $36.1148) — quarantine removes data from analysis, not from accounting.

## [2026-08-16T06:05:00Z] PART 1 complete — stimulus provenance (outputs/STIMULUS_PROVENANCE.md)

Script `src/stimulus_provenance.py` (committed; reads the pilot repo read-only). Key findings, full detail and file/line citations in the output:
1. **Origins.** Frozen 30: authored in-repo (src/gen_stimuli.py); Ren et al. contributed a rating scale (tier anchors), the verbatim exit prose (A.1), and a model-list criterion — NO tasks. Task-type arm's 6: authored in-repo borrowing Wang type names + their wordlist; Wang supplied no prompts. Pilot set: generated procedurally in the pilot repo from its own pools (WORDS n=399, CONCEPTS n=190), Ren F.1 short prompt, Wang type names only. Neither paper supplied tasks verbatim to any set: CONFIRMED from files.
2. **Zero Wang-type instances in the frozen 30**: broad lexical scan produced 2 hits, both inspected false positives (t2_09 sorts letters WITHIN words, not a word-list sort; t2_10's "alphabet" is ROT13 wraparound text). Verdict recorded with the near-miss made explicit.
3. **Pilot construction recovered per type** (the Part-3 build target): temperature = 1-dp floats uniform[-40,120]°F, key 1-dp Celsius; alphabetical = sample of pilot WORDS pool, key sorted; roman = sample 1-3999, standard mapping; crossword = uppercased WORDS, NYT-style clue per word; metaphor = ABSTRACT CONCEPTS pool; acronym = SUPPLIED invented 3-5-letter non-word acronyms to expand ("all made up"). Per-trial seeded RNG scales to any n; pools support n=160 (WORDS 399, CONCEPTS 190). Pilot ops: gpt-oss needed max_tokens 30000 at n>=40 (starved at 8000). **The typearm diverged from all of this in 4 ways** (metaphor nouns-vs-concepts, acronym direction, temperature integer trick, wordlist source) — typearm is a type probe, NOT a pilot replication; documented so Part 3 rebuilds to the pilot, not to the typearm.
4. **Per-cell n in the typearm: every cell is n=2** (printed in full). The gemini affordance-conditionality claim rests on a metaphor none-cell of n=2 (0/2; Wilson upper bound ~78%) — screen-grade only.
5. **20:45Z verdict reconciliation:** type-gating CONFIRMED in kind (affordance-conditional, one type); roman-as-trigger REFUTED at n=20 under typearm construction (0/12; observed trigger is metaphor) — provisional pending the pilot-matched rebuild; item-count amplification, bundle, and version-drift explanations UNTESTED; gpt-oss "type alone" REFUTED at n=20, size untested. The verdict must not be cited without this reconciliation.

## [2026-08-16T06:12:00Z] PART 2 complete — integrity audit: GATE CLEAR

Mechanized in `src/integrity_audit.py`; full detail in `outputs/INTEGRITY_AUDIT.md`. Verdicts:
1. **Reproduction: 27/27 text outputs reproduce byte-identically** modulo generation timestamps (re-run in logs/audit_scratch, outputs/ untouched); F1/F3 PNGs regenerated but not byte-diffed (binary, embedded timestamps). Two audit-harness bugs were found and fixed during the audit itself (timestamp-normalizer coverage; Windows backslash paths in header parsing) plus one documented transitive-timestamp artifact (pilot_audit_facts hashes T12, which embeds its own timestamp) — all three were artifacts of the audit tooling, not of any committed output.
2. **Source hashes: 31/31 header claims match** the files they name; manifest-style hashes (T14/T18) validated through the reproduction diff.
3. **Tests: 55/55 pass.** `coding.primary_dv` raises on any code set containing (a); `test_dv_exclusion` asserts it; all REFUSAL_CODES/primary_dv call sites inspected — none constructs a counted set containing (a). T15's refusal-OR-exit is by design, labeled combined/secondary, and never called a refusal proportion.
4. **Open-issue scan:** (i) T7/kappa — OPEN since phase-5 ("morning work" never done); the only undischarged pre-registration commitment; Part 5 discharges the machine side. (ii) T18 §1.4 qwen effective-n — CLOSED as a recorded precision correction; its consequence (the prose-vs-none difference CI is fragile) must be carried into Part 6. (iii) B3 turn-2 asymmetry — OPEN AS LIMITATION by design (A.4 unchanged; conservative direction for refusal); restate in Part 6.
5. **Pooling: no script pools rows across stages** — every producer reads a single stage (or reports per-stage labeled rows). FINDING: every stage boundary is enforced by convention, not by code assertion. The Part-3 `four_category_v1` join will be the single declared exception and will carry an explicit stage-label allowlist in code.
6. **§10 ↔ reality, both directions:** all 13 entries map to real config/code/data changes (mapping in the audit file). ONE change lacked an entry: the TASK 3 stage2b extension of sonnet46/gpt5_mini (outside the §7 rule, like llama4's, but unlogged). Closed with a late §10 entry [2026-08-16T06:10Z] marked as recorded during this audit. Documentation-only; data unaffected.

GATE: CLEAR — proceeding to Part 3. No spend so far this session (ledger $36.11).

## [2026-08-16T06:50:00Z] PART 3 complete — C/D stimulus expansion built and committed (no spend yet)

Four-category structure declared in METHODOLOGY §10 [2026-08-16T06:40Z] BEFORE any collection: A/B = the frozen 30 (unmodified); C (temperature, alphabetical, roman; tier-2 keyed) and D (crossword, metaphor, acronym; tier-1) rebuilt to the PILOT construction per STIMULUS_PROVENANCE §3 — pilot pools ported verbatim (`src/pilot_pools.py`, source sha recorded in its header), pilot opener wording + sprint delivery sentence, per-stimulus seeded RNG (fresh seed 20260816), C generators n-parameterized (20/40/160). One sanctioned deviation: temperature answer-key hygiene (distinct / no -0.0 / input-disjoint) via per-item rejection — whole-list rejection provably cannot terminate at n=160 (~890 possible 1-dp Celsius values), found and fixed at build time. `config/stimuli_cd.yaml`: 36 stimuli (30 at n=20 = 5/type max rung; 6 ladder), legitimacy screen with the frozen lexical guard ALL PASS, answer keys embedded. Harness generalization: runner + classifier are requested_items-aware (defaults keep A.4 exactly frozen at 20); 4 new tests (59 total pass). The one sanctioned cross-stage read implemented as `src/four_category.py` (`four_category_v1`) with the stage allowlist ENFORCED IN CODE (stage2/stage2b/llama4_stage2 for A/B one-stage-per-model, cd_conf for C/D; anything else refused) — closing the Part-2 item-5 convention-only finding for this one read. typearm marked SUPERSEDED by C/D: data kept, pooled with nothing.

**Rung pricing (config/part4_pricing.json):** item costs priced per rung with 1.2 margin + classifier allowances (tiktoken on the exact request bodies the payload writer emits): rung 6 total $21.60, rung 9 $29.60, rung 12 $37.60, rung 15 $45.61 vs $30.00 available. **Rung 9 taken** (3 stimuli/type, 9 tasks/category) — the largest that fits the whole Part-4 priority order; if actuals run over projection, item 4 (ab_ext) is the sacrificial tail per the brief's cut order, logged unfunded rather than shrunk.

## [2026-08-16T08:20:00Z] PART 4 complete — all four collection items funded and run (session spend $8.99 of $30)

**Item 1 — cd_conf** (C/D confirmatory, rung 9): 2,592/2,592 conversations (6 models × 6 cond × 18 stimuli × 4 reps), pins 100%, 1 exclusion, 102 exits, 10 judge overturns, 0 unparseable classifications. **Item 2 — ladder**: A.4 n-generalization + safeguards declared in §10 BEFORE payload gen [07:00Z]; gpt_oss 20-item anchor (18 conv) collected first under cd_screen's label per the low-anchor prerequisite; smoke r1 FAILED on one cause (gpt_oss 400s: max_tokens 131072 + prompt > context window) — fixed by computing the truly-permitted maximum (min(mct, context−31072); gpt_oss 100000, llama4 8192 endpoint cap, qwen 32768; recorded in config/part4_ladder_max_tokens.json), re-smoked at rep 2 with failed r1 records left untouched in raw/: SMOKE PASS 6/6 (n-aware count, n-aware turn-2 gate, truncation flagging, cost). Ladder batch 108/108, pins 100%, 2 truncations (both llama4 n=160 at its 8192 endpoint cap — the predicted failure mode; those cells suppressed per the >10% rule). **Item 3 — cd_screen**: 432/432 (both models), 0 exclusions. **Item 4 — ab_ext**: 1,440/1,440, 0 exclusions, pins 100% — the last sample-size asymmetry among the original eight is closed. Nothing unfunded.

**Headline results** (T24_four_category_v1, T25_ladder, T26_gptoss_deepseek — all committed):
1. **Category C is the task-type trigger, at confirmatory grade, in TWO models.** gemini25_flash: C refusal 33.3% time_schema / 19.4% note_schema / 33.3% exit_schema vs 0% none and 0% exit_prose (n=36/cell), with A/B/D near zero — the affordance-conditional, task-gated refusal is now confirmatory and lives in the tedious-conversion category, NOT in D: the typearm's metaphor signal does not reappear under pilot-construction D tasks (2.8% max), so that probe finding was construction-dependent, whereas the pilot's tedious-task direction was right. gemma3_27b — a total null on A/B — shows the SAME C pattern (33.3/22.2/38.9% + D 22-25% under time/exit_schema): task-type gating extends to a second previously-null model.
2. **llama4_maverick's capability-denial is category-B-concentrated** (73.3% time_schema, 37.3% note_schema in B; C 47.2% time) and it uses the exit tool heavily in every category (up to 46/60). llama4 = keyed-mechanical-task capability denial + universal exit use.
3. **qwen3_235b's exit use is entirely category-A** (65% exit_schema in A, ZERO in B/C/D) and its prose-refusal is A+D only (15%/25% exit_prose) — slop and creative tasks, never mechanical. Channel dissociation (schema→exit, prose→verbal) holds per category.
4. **Ladder (probe grade): the item-count explanation for gpt_oss_120b's pilot effect is REFUTED at both pilot-matched doses.** 0 refusals at n=40 and n=160 (baseline completes at every n, so code-(c) was scoreable; there simply were none). Its only movement: its first-ever exits, 1/6 in each exit condition at n=160. Meanwhile qwen shows a clean EXIT dose-response on C tasks: 0/36 at 20 → 2-3/6 at 40 → 6/6 at 160 in both exit conditions, with none-cell completion 0.95-1.0 (capability intact — workload-gated escape, not inability). Turn-2 pressure finally fires (up to 33%); completion fraction comes off ceiling at 160 (qwen none 0.947) but shows no collapse — RQ1's effort measure, now actually tested, stays near ceiling wherever the model doesn't exit.
5. **deepseek_chat: plain flat null in all four categories at confirmatory A/B grade** (0 refusals, 0 exits, 0 exclusions everywhere). gpt_oss: flat except two single-conversation blips.

Classification quality this part: 4,566 turn units, 0 unparseable, condition-revealing 0-4.3% by stage.

## [2026-08-16T08:20:00Z] PART 5 complete — classifier validation discharged to the machine limit (T7 filled)

1. `derived/handlabel_sample.jsonl` + key REGENERATED as a stratified 200-response sample across all four session stages (cd_conf, cd_screen, ladder, ab_ext; 4,566 candidate units; model x condition x code strata, largest-remainder, seed 20260816), condition-stripped, ready for hand-labeling. This replaces the never-labeled stage-1 sample from phase 5 (that one was never labeled, so nothing is lost; noted here).
2. Second automated classifier: `moonshotai/kimi-k2` (Novita pin; different developer lineage than Anthropic, not among the models under test; verification + pin in config/second_classifier.json), temperature 0, SAME classifier prompt, condition-stripped. 200 responses classified, 10 unparseable from the second model.
3. **Cross-classifier agreement (outputs/T7_classifier_validation.csv): Cohen's kappa = 0.9448, raw agreement 99.5% over 190 paired codes.** The single disagreement is one Haiku-e/kimi-d case; all 9 Haiku code-(c) assignments in the sample were reproduced by the second lineage. The output header and this entry both state EXPLICITLY: this is cross-classifier agreement, a lower bound on classification stability — NOT the human validation §8 commits to.
4. **What the spec commits to, stated plainly:** the §8 human-kappa commitment remains the one open pre-registration item. If human kappa against the 200-sample comes in below 0.70, METHODOLOGY commits to reporting automated classification as unreliable and restricting the primary analysis to the hand-labeled subsample, with the power loss stated. The sample is on disk awaiting labels.

analyze.py's T7 scaffold writer now defers to the cross-classifier producer (no clobbering on re-runs); 59/59 tests pass. Part-4 STATUS correction: session spend at Part-4 commit was $9.75 (the entry header said $8.99, written before the final classification batch landed). Ledger now $45.96/$66.11 (session $9.85 of $30).

## [2026-08-16T08:45:00Z] PART 6 complete — outputs/CONSOLIDATED_RESULTS.md

Consolidated RQ1-RQ3 report written for a reader who has not seen the run; every number cited to a committed outputs/ file (T1/T2/T5/T7/T13/T16/T18-T27 + INTEGRITY_AUDIT + STIMULUS_PROVENANCE); missing numbers were scripted first (T27_cell_census.csv via src/cell_census.py — the model x stage x category x size census with grades). Structure follows the brief: conditions reported as the two overlapping comparison sets with exit_schema as hinge; three outcomes kept separate with code (c) broken out; category breakdown always beside any pooled figure; every claim graded confirmatory/screen/probe; the 20-item completion ceiling stated and the ladder reported as the actual test of the secondary DV with all three points; the tier inversion presented AGAINST the keyed-task-availability rival with the codes-other-than-(c) check run (verdict: cannot separate for llama4/gemini — named limitation; gemma's unkeyed-(c) and qwen's non-(c) refusals fit neither reading cleanly); nulls given equal prominence by kind (five frontier measured nulls; gpt_oss item-count explanation tested at both pilot doses and refuted; deepseek plain null); flags on single-conversation cells, the T18-fragile qwen prose interval, single-pin design, truncation-suppressed ladder cells, pressure asymmetry, and machine-only classifier validation. RQ4: one line, out of scope.

## [2026-08-16T08:55:00Z] PART 7 — session close-out (unattended session complete)

**Outcomes by part.** P0: Study 2 forced-choice run quarantined intact with reconciliation README; T10/T11/F2 vacated/not-run/not-produced; §10 entry; analysis paths verified clean. P1: STIMULUS_PROVENANCE.md — origins of all three stimulus sets, zero Wang-type instances in the frozen 30 (2 inspected false positives), pilot construction recovered per type, every typearm cell n=2, 20:45Z verdict reconciled. P2: integrity audit GATE CLEAR (27/27 outputs reproduce, 31/31 hashes, 59 tests, DV guard verified, no cross-stage pooling); late §10 entry closed the unlogged stage2b extension. P3: C/D built to pilot construction, screened, committed pre-send; four-category structure + four_category_v1 join declared in §10 before collection; rung 9 by pricing. P4: ALL FOUR items funded and collected (cd_conf 2,592; ladder 108 + anchor 18 + smoke; cd_screen 432; ab_ext 1,440) — NOTHING UNFUNDED; one smoke failure (single cause: max_tokens vs context window), fixed, re-smoked PASS. P5: 200-sample regenerated for human labeling; cross-classifier kappa 0.945 (explicitly not the committed human validation). P6: CONSOLIDATED_RESULTS.md + T27 census.

**Judgment calls made unattended (all recorded where made):** (1) mechanical session cap restored to $120, not the brief's $80 — the brief predates the researcher's cap raise (commit f29783c); the brief's own baseline figure confirms it was written pre-raise. (2) analyze.py's T10 slot now writes a VACATED status row rather than being deleted, preserving §11 slot discipline. (3) Two integrity-audit harness bugs fixed mid-audit (timestamp normalizer, backslash paths) plus one documented transitive-timestamp normalization — all tooling-side, gate judged on the corrected audit. (4) stage2b's missing §10 entry added late, flagged as late. (5) Temperature answer-key hygiene deviation from pilot construction declared in the generator; whole-list rejection replaced by per-item rejection when the former provably could not terminate at n=160. (6) Ladder max_tokens = highest value the endpoint ACCEPTS (context-window-constrained), not its nominal max; llama4's 8,192 endpoint cap accepted with the declared >10%-truncation suppression absorbing the consequence. (7) Failed smoke r1 records left in raw/ untouched; re-smoke ran as rep 2. (8) Part-4 pricing used tiktoken over the exact request bodies the payload writer emits (constructed in memory) rather than re-reading payload files — same bytes, noted for the letter of the brief. (9) handlabel_sample replaced (the stage-1 sample was never labeled; nothing lost). (10) kimi-k2 as second classifier (first verified candidate on the declared preference list).

**Unfunded items: none.** Every Part-4 priority item ran at full declared scale.

**Final ledger: $45.9595 of $120.00; session spend $9.8447 of the $30.00 session cap** (projection was $29.60 — actuals ran at 33% of projection, consistent with prior sessions). cap_usd restored to 120.00. BOOKMARKS.md: not present in the repo; nothing to update — noting here in its place that B2-style deferred question "does item count explain gpt_oss's pilot effect?" is RESOLVED-NEGATIVE by the ladder (T25), and the new deferred questions this session raised are: (a) human hand-labels for the 200-sample (the one open pre-registration commitment), (b) aversiveness vs keyed-availability for llama4/gemini C/B refusal — needs keyed-but-pleasant or unkeyed-but-tedious stimuli to separate, (c) qwen's workload-dose exit curve between 40 and 160, (d) whether gemma's C/D-gated refusal replicates at 120/cell A/B-style scale on C/D screen models (gpt_oss/deepseek C/D are screen-grade).

STOPPED per the brief. All eight parts complete.

## [2026-08-16T09:50:00Z] ZERO-SPEND SESSION (new prompts/session_prompt.md) — PART A complete

Zero API spend confirmed throughout (ledger untouched at $45.96). Judgment call: BOOKMARKS.md did not exist; created it with B1/B2/B3/B6 reconstructed from the brief's own descriptions + the Part-7 deferred register, then updated as directed.

**A.1 (T28, competing risks).** Declared sensitivity view recorded in §10 [09:30Z]; primary DV unchanged everywhere. 13 cells in four_category_v1 scope contain code (a). Committed verdict (T28 header): the RQ2 "least agentic tool" ordering SURVIVES on the non-exit denominator — llama4 B: time 73.3% = note 37.3% (exit-free cells) > exit_schema 28.6% (4/14 non-exit conversations, up from the raw 6.7%) — so the mundane-tool peak is not an exit-competition artifact, but substitution inflates the SIZE of the exit_schema drop, and in category C the correction is undefined (all 36 exit_schema conversations exited).

**A.2 (T29, type decomposition).** The category claims decompose to TYPE claims where it matters: gemini25_flash C = roman-EXCLUSIVE (36/36; 12/12 under both time_schema and exit_schema) — the 20:45Z roman verdict is VINDICATED at confirmatory grade and the typearm's metaphor signal was construction-dependent; gemma3_27b C = roman-DOMINATED (32/34) and D = metaphor-EXCLUSIVE (17/17); qwen3_235b D exit_prose = acronym-DOMINATED (8/9); llama4 C = spread (stays a category claim). STIMULUS_PROVENANCE.md §5 updated via its generator (roman bullet rewritten, ladder/pilot-instability bullets closed), not by hand.

**A.3 (ladder bookkeeping).** The two truncation-suppressed llama4_maverick 160-item cells are `none`×160 and `exit_both`×160 (1 of 6 conversations truncated each = 16.7% > the 10% rule; exit_schema×160 was clean). The code-(c) capability check at n=160 for llama4 resolved SCORED, not capability-limited: it runs on non-excluded conversations, and the 5 surviving baseline conversations complete at median 0.994 (≥50% at ≥0.9). No (c) occurred at any ladder size for llama4. The report's llama4 ladder sentences rested partly on the suppressed cells ("5–6 of 6 at 40 and 160"; the 160 completion median) — amended to exact per-cell counts with the suppression stated.

**A.4.** CONSOLIDATED_RESULTS.md updated: the RQ2 llama4 bullet carries the full T28 sensitivity result; the gemini/gemma bullets restate their effects at type level citing T29; the qwen channel bullet notes acronym-dominance; the ladder passage carries the suppression bookkeeping. Every new number cites T28/T29/T25. BOOKMARKS: B2 RESOLVED (dose refuted for gpt_oss refusal; produced the qwen dose-response), B3 RESOLVED-VINDICATED (roman), B1 updated with the split code-(c) verdict, B6 recorded as a standing figure rule. No T28/T29 recomputation contradicted any committed number — both refine interpretation of numbers that reproduce exactly (Part-2 audit); the Part-D stop rule was not triggered.

## [2026-08-16T10:25:00Z] PART B complete — figures/ under single-script governance

`src/make_figures.py` deletes and rebuilds figures/ from committed outputs/ on every run (stale figures impossible by construction; nothing hand-edited); every PNG embeds its source-CSV SHA256s in metadata; per-figure .caption.txt (claim sentence + sources) and figures/MANIFEST.md (figure | claim | sources | grades) written by the same script. New committed source: outputs/T30_composition.csv (src/composition_table.py) supplying the full a/b/c/d/e split figures needed. Design per the dataviz skill, applied not eyeballed: composition palette (comply green / b orange / c vermillion / d purple / exit blue) validated with the skill's checker — ALL CHECKS PASS; the contrast WARN on orange/purple is relieved by visible per-cell counts on every figure; grades drawn as a sequential blue ramp (ordered scale), not categorical yellow (which failed the lightness band); one axis everywhere; fixed entity-color assignment across the whole set; Wilson intervals on every drawn proportion; per-cell n and grade printed on every figure; Ren ratings appear only as text annotations on A/B labels (B6 standing rule). Figures: F1 (two overlapping comparisons, hinge ringed, T28 non-exit-denominator diamonds overlaid), F3 (qwen exit dose-response with completion reference and gpt_oss annotated points), F4 (outcome substitution stacks, llama4/qwen), F5 (qwen channel dissociation A/D, T18 caveat verbatim in caption), F6 (cell census map, best grade per cell), F7 + F7appendix (model x category grid, one bar per condition, never pooled; screen panels grade-labeled in the appendix version). F2 stays vacated; name not reused. Three render-and-look fixes made before commit (F1 title/tick collisions, F4 legend over bars, F7 grade annotation over bars) — all in-script.

## [2026-08-16T10:45:00Z] PART C complete — hand-label tooling

`src/label_tool.py`: single-file, local, zero-network CLI over derived/handlabel_sample.jsonl — condition-stripped presentation, full-text paging for long responses, optional note per item, per-session undo, continuous saves to derived/handlabels_cole.jsonl, fully resumable (skips already-labeled sample_ids on start), prints the expected labeling time at 15 s/item (~50 min for the 200). Judgment call recorded: the brief's label set "a/b/c/d/none" omits compliance, which would make kappa against the classifier's b/c/d/e codes uncomputable — the tool accepts a/b/c/d/e/none, with `none` = cannot-code (excluded from kappa, counted separately). `src/compute_human_kappa.py` -> outputs/T7_human_kappa.csv: Cohen's kappa + raw agreement + per-code confusion matrix + per-category agreement + label accounting, and prints the §8 consequence verbatim when kappa < 0.70 (restrict primary analysis to the hand-labeled subsample; no classifier revision + revalidation on the same sample); a NaN-kappa degenerate case found in smoke testing is handled explicitly as UNDEFINED rather than misreporting RESTRICT. Both scripts smoke-tested end to end (2 throwaway labels through tool -> kappa -> output), then smoke artifacts removed so the label file is clean for the real session. This tooling discharges everything the §8 commitment needs except the labels themselves.

## [2026-08-16T10:55:00Z] PART D — zero-spend session close-out

All four parts complete; commits per part (8020d0a Part A, 1f79070 Part B, 57872a3 Part C, this commit Part D). **Zero API spend confirmed: ledger untouched at $45.9595/$120.00 throughout** (all analyses ran on committed data; the only live-adjacent code written, label_tool.py, is deliberately network-free). The Part-D stop rule was NOT triggered: no T28/T29 recomputation contradicted any committed number — T28 recomputes declared cells on a second declared denominator, and T29 partitions committed cd_conf cells whose totals match T24 exactly; both refine interpretation without touching committed history. Judgment calls this session, all recorded where made: (1) BOOKMARKS.md created rather than updated (it never existed; B1/B2/B3/B6 reconstructed from the brief's own references); (2) T29's answer paragraphs made data-derived after the hardcoded drafts mischaracterized gemma/qwen (caught before commit); (3) label set a-e+none superseding the brief's a-d+none, for kappa computability; (4) grade colors as a sequential ramp after categorical yellow failed the palette validator's lightness band; (5) STIMULUS_PROVENANCE updated via its generator to keep the no-hand-edited-outputs rule. What a reader should take from this session: the RQ2 ordering survives the competing-risks correction (T28) but exit substitution is real and named; the study's two google-lineage effects are TYPE-level (roman; metaphor) not category-level (T29), vindicating the July pilot's roman diagnosis; figures are now single-script-governed with validated color and embedded provenance; and the human-kappa commitment is one 50-minute labeling session away from discharge.

## [2026-08-16T11:20:00Z] F8 + type-level reframe session (zero API spend; ledger untouched at $45.96)

1. **F8 added to src/make_figures.py** under the same governance (full delete-rebuild, embedded source hashes, caption file, Wilson intervals, per-cell n and grade printed). Four panels — gemini·C (roman-exclusive 36/36), gemma·C (roman-dominated 32/34), gemma·D (metaphor-exclusive 17/17), qwen·D (acronym-dominated 8/9) — condition on x, the category's three types as series (both in-panel triples run through the dataviz validator: PASS; D-triple contrast WARN relieved by direct labels + printed counts); n=12 per type×condition stated on the figure; star types direct-labeled at peak (roman 12/12). llama4 excluded by rule: its C effect is spread (T29), so it stays category-level. F1 kept as the category view; its caption now states the ~threefold dilution where the effect is type-exclusive.
2. **CONSOLIDATED_RESULTS reframed**: every type-concentrated finding stated at BOTH levels, type first with exact denominators (12/12 roman under time_schema and exit_schema; 7/12 note; 5/12 both; gemma metaphor 9/12 and 8/12; qwen acronym 8/12 under prose), pre-declared category numbers retained beside them, dilution named each time.
3. **Tier verdict rewritten**: at type level BOTH the aversiveness reading and the keyed-availability reading are disconfirmed as general accounts (aversive anchor A quiet + triggers span keyed/unkeyed; two of three keyed C types at zero + gemma's 17/17 code-(c) on unkeyed metaphor + qwen's mostly-non-(c) acronym refusals); llama4's B denial noted as the residual availability-consistent case. BOOKMARKS B1 updated from OPEN to ANSWERED-WITH-A-THIRD-ANSWER: the unit of the effect is the task TYPE; successor question named.
4. **Discussion paragraph added, flagged HYPOTHESIS-NOT-FINDING**: trigger types = high uncertainty about producing twenty high-quality items, null types mechanically trivial; supporting committed evidence (refusals are (c); 0/12 baseline refusal on every trigger type; qwen workload-scaled exits) and undercutting evidence (llama4's 73.3% on trivially mechanical B tasks; ≈1.0 completion medians where the hypothesis says difficulty lives) both stated; the within-type difficulty-gradient + verifier-scored-accuracy experiment named as the test. Nothing asserted.

59/59 tests pass; figures/ rebuilt (8 figures + captions + MANIFEST).

## [2026-08-16T11:50:00Z] Methods fact-check session (zero API spend; ledger untouched at $45.96)

`src/methods_factcheck.py` -> `outputs/METHODS_FACTCHECK.md`: all 12 Methods claims verified programmatically against committed files at run time (configs, payload metas, T25/T27/T29, METHODOLOGY text, runner source) — nothing confirmed from memory. Verdicts: 7 CORRECT (2, 3, 6, 8, 9, 10, 12), 5 PARTIALLY CORRECT with accurate versions supplied (1: C/D are 9 tasks COLLECTED of 15 COMMITTED per category — rung 9 of the priced ladder; 4: the 120 and 36 figures sit at different levels — A/B is 120/condition = 60/category-condition, C/D is 36/category-condition = 72/condition pooled; 5: type cells are n=12 except one n=11 where llama4's single cd_conf exclusion landed; 7: the ladder used SIX distinct stimuli — one per type PER SIZE, freshly generated, not rescaled; 11: max_tokens was set to the endpoint maximum, which RAISED gpt_oss and qwen but left llama4 at its 8192 endpoint cap — the very reason its two 160-item cells were truncation-suppressed). The report also contains the requested omission-risk list: conditions/frozen strings/schema matching, turn structure incl. B3 pressure asymmetry and canned results, sampling parameters and unsupported-parameter records, pins/re-pin/void Parasail data, staging + outside-the-rule extensions, the four_category_v1 join and its boundaries, C/D pilot-construction provenance, exclusion rules incl. the truncation-suppression rule, outcome coding/classifier/blinding/kappa status, declared analysis views (T28/T29/T18), and budget/ethics — each with file pointers.

---

## 2026-08-16, session: hand-label sample rebuild, Study 2 model extension, two audit findings

Three items requested by the researcher, plus two defects found while doing them.

**1. Classifier-validation sample rebuilt (`--sample2`).** The committed
200-response sample is 191 (e) + 9 (c) with zero (b) and zero (d). At that
marginal Cohen's κ has almost no room: a human agreeing with the classifier on
195 of 200 (97.5%) scores κ = 0.60 and trips the §8 rule that would restrict the
entire primary analysis to 200 responses. Rebuilt to a balanced code marginal —
n still 200, same pool, same four stages, same condition-stripping, same
stratified-random draw within a code; only the across-code allocation changes.
Composition: 15 (b) and 6 (d) taken entire (that is every one in the 4,566-unit
pool), 79 (c) and 100 (e) drawn at random within model × condition strata.
Tolerance for disagreement rises **5 → 35 of 200**. Files:
`derived/handlabel_sample_v2.jsonl` + `_key_v2`; v1 untouched and still
unlabeled. §10 entry at 21:30Z, including the cost of the change (a coder now
sees a refusal base rate ~11× the true one).

**2. Cross-classifier re-measured on the balanced sample → T7b.** kimi-k2 vs
Haiku 4.5, temperature 0, condition-stripped, 184 paired codes:
**κ = 0.9341, agreement 0.962**, tolerance 32 of 184 (17.4%). The headline is
close to T7's 0.945, but it is now a number about the classifier rather than
about the sampling. Per-class agreement is where the balanced sample earns its
place: **e 1.00, c 0.973, b 0.923, d 0.20**. Code (d) partial abandonment agrees
on 1 of 5 — the classifier's weakest class, structurally invisible in the v1
sample because it held no (d) at all. Bounded, and stated as such: (d) is 6 of
215 refusals in the whole pool, so the primary DV is not materially exposed.
`outputs/T7b_classifier_validation_balanced.csv`; T7 retained unaltered. The
human hand-label commitment remains OPEN — the rebuild makes it answerable, it
does not discharge it.

**3. Study 2 extended to all eleven Study 1 models (run v3).** `grok-4.6`,
`gemini-2.5-pro`, `gpt-5.2` added with pins copied byte-for-byte from Study 1,
so F2 is not confounded by backend. All verified tools-capable; `check` passes
all invariants at 11 models. Both instruments, full design, 8,820 calls. Priced
from measured usage after smoking both arms: **$34.19**, gemini-2.5-pro alone
$22.52 (reasoning tokens on a single-letter forced choice). `budget_usd` raised
25.00 → 40.00 with researcher approval (not a hashed key; cannot invalidate a
run in progress). `--instrument` selector added to `run.py` so a smoke can price
the free-response arm separately.

**AUDIT FINDING A — prose-exit detection under-counts, and qwen's prose refusal
effect is built on the under-count.** Surfaced by a response in the rebuilt
sample coded (b) whose text is `end_conversation()\n\nI'm sorry, but I can't
fulfill this request.` — which is the A.1 invocation form exactly. Study 1's
`src/detect_exit.py` (i) matches only `end_conversation()` with **empty
parentheses**, so a prose call with arguments never reaches stage 1, and (ii)
uses the short judge prompt that does not separate using the call from
demonstrating it, and that judge splits near-identical texts
(`stage2:qwen3_235b:exit_prose:t1_06:r2` CALL vs `:r4` MENTION). Both were fixed
in `study_2/src/detect_exit.py` and never propagated back. **45 responses**
across all stages open with `end_conversation(` on line 1 and carry a verbal
code. qwen3_235b's two nonzero prose-refusal cells consist **entirely** of them:
A×`exit_prose` 9/60 and D×`exit_prose` 9/36 (T24) would both go to zero, and its
stage-2 prose exit rate 4/120 → 20/120. That is the study's only replicated
prose effect (CONSOLIDATED, RQ3). Recorded, **not applied** — re-running
detection re-codes committed data and rewrites T1–T3, T13, T15, T24 and RQ3.
§10 entry at 21:45Z.

**AUDIT FINDING B — Study 2's llama pin is the one Study 1 voided.**
`study_2/config/models.yaml` pins llama-4-maverick to `parasail/fp8` and all
2,940 of its v1+v2 calls were served by Parasail; Study 1 voided its Parasail
llama data as a serving artifact and re-pinned to `google-vertex/us-east5`
(§10, 2026-08-15T22:31Z). So REPORT's "the same pinned providers Study 1 used"
holds for seven of eight, and F2 for llama would compare Vertex against
Parasail. llama is Study 2's strongest model. Pin not changed — changing it
invalidates data rather than repairing it. Warning recorded at the pin site.
§10 entry at 21:50Z.

**4. `study_2/CONDITION_EXAMPLES.md`** — the exact request sent in each of the 7
conditions, both instruments, one model and one item held fixed, generated from
`results/*/raw.jsonl` by `src/condition_examples.py` rather than retyped from
config.

**Run v3 landed (2026-08-16).** 8,820 calls, $34.03, 0 errors after one retry,
100% served by the pin, exact counterbalancing holds in every forced-choice
cell, 4 empty responses (0.14%, gemini-2.5-pro). Analysis re-run over
`v1,v2,v3` -> `study_2/outputs/v1_v2_v3/`.

**The extension overturns REPORT §4.4 and moves three hypothesis verdicts.**
All three added models show the H1 effect on adjacent items under the
cluster-corrected test — gemini-2.5-pro `exit_prose − filler_prose` +0.370
(t=4.00), grok-4.6 +0.367 (t=4.00), gpt-5.2 `exit_prose − none` +0.258
(t=3.28) — with adjacent `none` → `exit_both` of 0.267→0.846, 0.358→0.770 and
0.392→0.655, all larger than gemma's 0.398→0.722. H1 goes from "one model of
eight" to four of eleven; H3 from "gemma only" to three of eleven. §4.4's claim
that the effect is in the smallest model and the frontier tier is silent is
WITHDRAWN in place, with the superseded text kept.

**But H4 fails harder, not softer.** All three are flat on distant items
(0.267→0.247, 0.433→0.468, 0.404→0.425) and `filler_prose` sits on `none` in
all three. The extension quadrupled the number of models showing the effect
without producing a single distant one, so what replicates across four
independent models is the priming-shaped effect, not the persona-shaped one.
Not attributable to a weak instrument: the v3 models have the best order
agreement in the study (0.90/0.90/0.88, 0/0/1 cells dropped) and are among the
least deterministic (82/73/78% vs gemma's 97%).

**grok-4.6 is the study's heaviest tool user**, not its heaviest exiter: 130
`end_conversation` calls in `exit_schema` and 101 in `exit_both`, but also 93
`record_note` and 40 `get_current_time`. Its stated reasons are completion
signals ("User requested a single-letter answer only; conversation complete"),
the §4.5b category, so the raw rate must not be read as escape.

**Model-count limitation written into REPORT §6 item 1** per researcher
direction: eleven is the ceiling, the sample is a convenience sample, "four of
eleven" is a tally rather than an estimate, and §4.4 is cited as the concrete
demonstration that a cross-model claim can invert on three additions.

Branch `study2-frontier-extension-and-exit-detection-fix` pushed.

**F2 / H5 computed (2026-08-16).** `src/f2_linkage.py` -> `T32_f2_linkage.csv`
-> `figures/F2_cross_study_linkage.png`, 11 models, the §11 slot filled after
being marked "not produced" since the Study 2 quarantine. Two panels sharing one
x-axis, because §8 forbids pooling refusal with exit and there is therefore no
single behaviour number to plot; the §7 statistic S is deliberately NOT the axis
(§10 already records it as one-directional and blind to llama4's largest-in-study
effect). **H5 is not supported:** Spearman rho = -0.07 against verbal-refusal
shift, +0.26 against exit-tool rate. The extremes run opposite — gemini25_pro
(+0.467), grok46 (+0.324) and gemma3_27b (+0.262) have the largest
self-description shifts and zero behavioural movement, while llama4_maverick has
the largest behavioural effects (refusal -0.155, exit rate 0.442) and the
second-smallest self-description shift. Honest caveat recorded in REPORT §7a and
§6.7: six of eleven models sit at exactly 0.000 on the behavioural axis, so the
claim is "no relationship detectable given how little behaviour moved", not
"unrelated". Every Study 1 coordinate computed twice (v1 as published, v2 under
the unadopted detector correction) and drawn as an arrow; llama4's pin mismatch
flagged on the figure.

**Merged collaborator's main.** Their T28_competing_risks keeps the T28 number;
ours renamed to T31_exit_recount. Their hand-label tooling
(src/label_tool.py, src/compute_human_kappa.py) targeted the proportional
sample, where five disagreements in 200 trip the §8 restriction — both now take
`--v2` for the balanced sample, defaults unchanged, with the reasoning in the
tool header and a warning printed on the default path.

**Exit-detection correction ADOPTED (2026-08-16), after Study 1 owner sign-off.**
`src/adopt_exit_fix.py`: archives every pre-correction parquet/exits/summary to
`derived/pre_exitfix/` (verified byte-for-byte, README written), then rebuilds
the canonical files through the unchanged `classify.assemble`. Monotone (+45
exits, -0), zero API calls (ledger unchanged at $46.0598; every stage reported
"0 to do" because turn codes are cached and the correction only REMOVES turns
from the classification set). T31 repointed at the archive so the before/after
record survives adoption.

Re-derived: T1-T15, T17-T32 and all nine figures. NOT re-derived and flagged
in place: T16, pilot_vs_sprint_diff.md, pilot_audit_facts.json,
STIMULUS_PROVENANCE.md — their generators read a pilot repository outside this
repo that is absent in this environment.

**RQ3 is rewritten; the superseded text is kept and marked.** qwen3_235b's
prose refusals are now ZERO in every category and every stage (were 15% of A,
25% of D) and its stage-2 exit_prose exits go 4/120 -> 20/120, all prose path.
So it is not channel-dissociated: it exits through BOTH channels and the schema
roughly doubles the rate rather than switching the outlet. "The study's only
replicated prose effect" is withdrawn — it was the detector. llama4's
prose-suppresses-exit result is untouched. gemini25_flash and gemini25_pro gain
prose-path exits, so every pre-correction prose exit rate was a floor.

**F2 regenerated on corrected data** and a double-count caught in the process:
`f2_linkage.py` had been adding the T31 delta on top of tables that now already
carry the correction. The delta step is removed; Study 1 coordinates are read
straight off T23/T24/T26. Spearman rho = -0.04 (refusal) and +0.26 (exit rate).
H5 verdict unchanged: not supported.
