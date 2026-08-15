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
