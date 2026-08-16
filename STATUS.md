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
