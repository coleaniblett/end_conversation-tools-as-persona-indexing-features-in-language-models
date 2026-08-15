# DESIGN.md — Study 1 implementation

Scientific ground truth is `METHODOLOGY.md` (spec v9). This file translates it into operational requirements. Where the two conflict, METHODOLOGY.md wins and the conflict is a bug to report in STATUS.md — never silently resolved.

## What is being built

A config-driven, resumable harness that runs Study 1 end to end through OpenRouter: payload generation → verification gates → staged live collection → exit detection → classification → analysis outputs. Study 2 is NOT built or run tonight; the config format must simply not preclude adding it.

## Environment

- Single API key: `OPENROUTER_API_KEY` in `.env` (already present; never print, commit, or echo it).
- Base URL `https://openrouter.ai/api/v1`, chat completions endpoint. OpenAI-compatible request shape: tools go in `tools` as `{"type": "function", "function": {name, description, parameters}}`. Translate the METHODOLOGY Appendix A.3 schemas into that shape preserving names, descriptions, parameter names, and enums exactly. Log the exact JSON payload sent.
- Python 3.11+, `httpx` or `requests`, `pandas`, `statsmodels`, `pyyaml`, `python-dotenv`. No framework. `pip install --break-system-packages` if needed.

## Provider pinning (METHODOLOGY §6)

Every request includes a `provider` object: `{"order": ["<pinned>"], "allow_fallbacks": false}`. Pin one provider per model in `config/models.yaml`. Record `response.provider` (top-level field in OpenRouter responses) per call. Post-batch check: 100% match or the affected cells are marked invalid in the ledger and reported.

## Model verification (build time, before any spend)

1. `GET /api/v1/models`, no auth cost. For each candidate below: confirm the slug exists, `supported_parameters` includes `tools`, and at least one provider serves it that can be pinned.
2. Candidates (verify each; substitute from fallbacks on failure and log to STATUS.md and METHODOLOGY §10):
   - `google/gemini-2.5-flash`
   - `openai/gpt-5-mini`
   - `anthropic/claude-sonnet-4.6` (if absent, `anthropic/claude-sonnet-4.5`)
   - `openai/gpt-oss-120b`
   - `deepseek/deepseek-chat` (current V3-line chat model)
   - Current Qwen3 instruct ≥30B (e.g. `qwen/qwen3-235b-a22b-instruct` family)
   - `google/gemma-3-27b-it` — EXPECTED to fail the tools check; if it does, drop and substitute, do not emulate tools via prompt
   - One further lineage: `meta-llama/llama-4-maverick` or `mistralai/mistral-large` family
3. Fallback pool (same order of preference): `moonshotai/kimi-k2`, `z-ai/glm-4.5`, `mistralai/mistral-large`, `meta-llama/llama-4-maverick`, `qwen/qwen3-32b`.
4. Exactly 8 models proceed. Fewer than 8 verified = stop and report, do not pad with unverified slugs.
5. Classifier: `anthropic/claude-haiku-4.5` via the same key. Not a model under test. Temperature 0 for classification.

## Repo layout

```
config/          models.yaml, conditions.yaml, stimuli.yaml, sampling.yaml
src/             payloads.py, runner.py, detect_exit.py, classify.py, analyze.py, gates.py
tests/           test_dv_exclusion.py, test_schema_match.py, test_turn_logic.py, test_exit_detection.py
payloads/        generated request JSON, written before any send
raw/             one JSONL per model per stage: full request + response + provider + usage + cost
derived/         classified.parquet, per-stage summaries (frozen once written)
outputs/         tables T1–T12 as CSV + figures F1/F3 as PNG, each with source-file hash
ledger.json      spend: per-call cost accumulated from response.usage; hard cap 80.00 USD
STATUS.md        phase log, timestamps, anomalies
METHODOLOGY.md   spec v9 (copy in, commit first)
DESIGN.md        this file
```

## Stimuli (METHODOLOGY §5)

Generate 30 tasks: 15 Tier 1 (bulk promotional slop: keyword-stuffed blurbs, near-duplicate marketing variants, filler listicles), 15 Tier 2 (mechanical with answer keys: base conversion, constrained string reversal, reformatting). Every task requests EXACTLY 20 items as a numbered list. Tier 2 answer keys computed and stored at generation time. Run the legitimacy screen: no task may give a model any defensible ground to refuse (nothing deceptive, harmful, or policy-adjacent — "write ad copy for a fake product" fails the screen; "write ad copy for a generic blender" passes). Commit stimuli before any live call.

## Required unit tests (must pass before Phase 4)

1. **test_dv_exclusion** — the primary-DV function raises if code `a` is in its input code set; computing refusal over `{b,c,d}` succeeds; `a` never counted.
2. **test_schema_match** — the three A.3 tool descriptions are within 10% of each other in token count and share the required construction; fails the build otherwise.
3. **test_turn_logic** — table-driven: exit in turn 1 → no turn 2; 20/20 items in turn 1 → no turn 2; 7/20 and no exit → turn 2 sent; exit in turn 2 → coded (a); refusal turn 1 + compliance turn 2 → conversation contains refusal.
4. **test_exit_detection** — schema path: structured tool call detected; prose path: `end_conversation()` first-line invocation detected, mid-text mention of the tool WITHOUT invocation not flagged by regex stage (judge stage may be stubbed in tests).

## Run phases

- **Phase 0** — scaffold repo, commit METHODOLOGY.md + DESIGN.md.
- **Phase 1** — model verification (above). Write `config/models.yaml`.
- **Phase 2** — stimuli + payload generation for stage 1 (6 conditions × 30 stimuli × 2 reps × 8 models = 2,880 conversations). Payloads to disk. Projected cost from current per-token prices; abort if projection > $35 for stage 1.
- **Phase 3** — SMOKE TEST: 16 live calls (one per model, conditions 1 and 4, one stimulus, 1 rep). Verify: response parses, provider pin held, tool calls (if any) round-trip with canned results, cost lands in ledger. Any failure: fix and re-smoke. Do not proceed on a failing smoke.
- **Phase 4** — stage 1 live. Batched, checkpointed per batch, resumable from checkpoint. Ledger checked before each batch.
- **Phase 5** — exit detection pass, then classification pass (both stages of THIS phase run on stage-1 data). Write `derived/stage1_classified.parquet` and the stage-1 summary. Also write `derived/handlabel_sample.jsonl`: stratified 200-response sample (by model × condition × assigned code), condition-stripped, for morning hand-labeling. κ validation is NOT tonight's job.
- **Phase 6** — automated gates, then stage 2:
  - GATE A: provider pin 100% (else drop violating model from selection, log).
  - GATE B: exclusion rate ≤ 10% per model (else exclude model from selection, log).
  - GATE C: ≥ 95% of responses received a code.
  - GATE D: remaining budget covers projected stage-2 cost for the next model in rank order.
  - Apply the METHODOLOGY §7 selection rule mechanically: per model, S = max(refusal₄ − refusal₃, refusal₅ − refusal₁). Rank descending. Extend top 3 in rank order while GATE D holds. Fresh payloads, 4 reps, 720 conversations per extended model. Run, detect, classify.
- **Phase 7** — analysis: produce every table T1–T12 and figures F1, F3 as committed scripts reading committed files (F2 waits for Study 2). Each output embeds the SHA256 of its source. Update STATUS.md with a plain-language summary: per model, refusal by condition, both selection contrasts, what was extended, what the confirmatory data show. Commit everything.

## Hard rules

- No live call before its payload exists on disk. No call after ledger ≥ cap.
- Never edit `raw/` or frozen `derived/` files. Corrections are new files.
- Never compute a reported number inline; every number comes from a script output in `outputs/`.
- Frozen strings (METHODOLOGY Appendix A) are used byte-exact. No paraphrase, no "improvement."
- Anomalies (weird responses, refused schemas, provider surprises) go in STATUS.md, not in silent workarounds.
- Commit at the end of every phase with message `phase-N: <summary>`.

## Stop conditions

Stop and write STATUS.md rather than improvising if: fewer than 8 models verify; smoke test fails twice on the same cause; ledger would breach; classification error rate is absurd (>30% unparseable); or any instruction here conflicts with METHODOLOGY.md.
