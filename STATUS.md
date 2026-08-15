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
