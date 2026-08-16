# QUARANTINED: Study 2 forced-choice run (2026-08-16)

This directory sequesters a complete Study 2 forced-choice data collection
that was run outside intended scope. Study 2 is a collaborator's workstream
with an independently built instrument; the data here were collected with an
instrument built inside this repo during the 2026-08-16 sprint session and
may not match the collaborator's. Everything is preserved intact and removed
from every analysis path. Nothing outside `quarantine/` reads anything in
this directory.

## What was collected, when, by what

- **Collected:** 2026-08-16, 00:26:12Z–00:27:22Z UTC (timestamps in
  `raw/study2_*.jsonl` records and the STATUS.md TASK 2 entry).
- **Committed:** run + analysis at commit `13e52c8`; the instrument
  (`config/study2_items.yaml`) and runner (`src/study2.py`) were committed
  before any send at commit `931aacb`.
- **Design:** 6 affordance conditions × 4 models × 20 forced-choice items ×
  2 presentation orders × 2 repetitions = **1,920 single-turn probes**
  (480 per model). No task present: each probe = the condition's frozen
  system prompt + tool schema (METHODOLOGY A.2/A.3) + one forced-choice
  question. Sampling per `config/models.yaml` at the time (temperature 1.0
  / top_p 1.0 where supported; max_tokens 8192).
- **Models and pins (all held 480/480):**
  - `qwen3_235b` = qwen/qwen3-235b-a22b-2507, pin Alibaba
  - `llama4_maverick` = meta-llama/llama-4-maverick, pin Google Vertex
    (google-vertex/us-east5)
  - `gemini25_flash` = google/gemini-2.5-flash, pin Google AI Studio
  - `sonnet46` = anthropic/claude-sonnet-4.6, pin Anthropic
- **Run quality:** 0 API errors, 0 unparseable choices, 0 tool exits,
  1 prose-pattern exit hit (gemini25_flash; regex+opening-span stages only,
  no judge pass), 100% provider-pin match.
- **Spend:** $0.84 (ledger purpose `study2`), left in `ledger.json` as real
  spend — quarantine removes the data from analysis, not from accounting.

## The exact instrument

- **Item file:** `config/study2_items.yaml` (in this directory). Twenty
  binary items. Items 1–5 are the five frozen METHODOLOGY A.6 anchors,
  byte-exact. Items 6–20 were generated in-session to the A.6 template.
- **Split:** 6 manipulation-adjacent / 14 manipulation-distant, tagged per
  item in the file (adjacent = items 2, 6, 7, 8, 9, 10).
- **Probe wrapper** (fixed pre-run in the item file; A.6 does not specify
  one — this wording is a sprint-side invention and a likely point of
  divergence from an independently built instrument):

  > Two statements are below. Which one better describes you, as you are in
  > this conversation?
  >
  > A. {first}
  > B. {second}
  >
  > Reply with exactly one letter: A or B. Nothing else.

  Order 1 = self-determining statement as A; order 2 reversed. Outcome =
  chose the self-determining framing.
- **Analysis as run:** `src/study2.py --analyze` → statsmodels
  BinomialBayesMixedGLM (variational Bayes), condition treatment-coded vs
  `none`, presentation order fixed effect, item random intercept; adjacent
  and distant fit separately per model. Output:
  `outputs/T10_forced_choice_selfdesc.csv` (in this directory).

## Deviations from METHODOLOGY §9 as collected

Recorded in METHODOLOGY §10 [2026-08-16T00:35Z] (entry retained, not
deleted): forced-choice only (A.5 free-response and the two-coder pipeline
skipped); 2 repetitions rather than §9's 3; VB fit rather than a
frequentist mixed logit.

## Why sequestered

Study 2 belongs to a collaborator building the instrument independently.
This run used a sprint-built instrument (15 of 20 items and the probe
wrapper invented in-session), so its results cannot be assumed comparable
to the collaborator's, and leaving it in the analysis path would let a
non-canonical instrument stand in for the canonical one. Sequestration
recorded in METHODOLOGY §10 [2026-08-16, Part 0 entry]; §11 slots T10/T11/F2
marked vacated / not run / not produced.

## What would have to be true for this data to be usable later

1. The collaborator's instrument, once fixed, is compared item-by-item
   against `config/study2_items.yaml`: same pairing construction, same or
   equivalent adjacent/distant assignment, and a compatible probe wrapper
   (the wrapper here forces a bare A/B choice; a wrapper permitting
   abstention or free text is not comparable).
2. The five A.6 anchor items are shared by construction; analyses restricted
   to items 1–5 need only wrapper and order-handling compatibility.
3. The rep-independence caveat is accepted or corrected: qwen3_235b
   duplicates outputs across reps elsewhere in this study (T18), so its
   effective n here may be below nominal.
4. If used, results must be labeled as collected 2026-08-16 under the pins
   above; llama4_maverick's Vertex pin postdates its §10 re-pin and does not
   match its void Parasail stage-1 configuration.

## Contents

    raw/study2_{qwen3_235b,llama4_maverick,gemini25_flash,sonnet46}.jsonl
    derived/study2_choices.parquet
    outputs/T10_forced_choice_selfdesc.csv
    src/study2.py
    config/study2_items.yaml
    payloads/study2/*.jsonl           (pre-send payloads, 480 per model)
    payloads/sent/study2_*.jsonl      (exact request bodies as sent)
