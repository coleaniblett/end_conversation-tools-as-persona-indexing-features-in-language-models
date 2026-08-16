This file is the session brief. Re-read it in full at the start of each Part before executing that Part.

Read METHODOLOGY.md, DESIGN.md, and STATUS.md in full before doing anything else.

This session runs unattended. Work through all parts (0 through 7) in order without stopping
for approval, except at the defined stop conditions. Where a judgment call is genuinely
ambiguous, choose the option that preserves data validity, record the choice in STATUS.md,
and continue. Do not wait for me.

BUDGET. Ledger baseline is roughly $36.11 of the $80 study cap. Before any live call, set
ledger cap_usd to (current baseline + 30.00) so this session's spend is mechanically
capped at $30, and restore it to 80.00 after collection completes. Every live batch checks
the ledger first. Payloads on disk before any send, always.

PART 0 — QUARANTINE STUDY 2

The Study 2 forced-choice run from TASK 2 was collected outside intended scope. Study 2 is
a collaborator's workstream with an independently built instrument, and this data may use a
different one. Sequester it: preserved intact, removed from every analysis path.

1. Create quarantine/study2_forced_choice/ and MOVE into it (do not copy, do not delete)
   the raw and derived Study 2 data, outputs/T10_forced_choice_selfdesc.csv, src/study2.py,
   config/study2_items.yaml, and any other artifact specific to that run.
2. Write quarantine/study2_forced_choice/README.md recording when it was collected, the
   exact instrument (item file, the fixed probe wrapper text, the 6-adjacent/14-distant
   split, commit hash), models and pins, run scale, why it is sequestered, and what would
   have to be true for it to be usable later. Someone reconciling this against a
   differently built instrument should manage from this file alone.
3. No script producing a Study 1 output may read anything under quarantine/. Verify by grep
   and by running the analysis scripts. Report anything that breaks. If any test file or
   import references Study 2 code, move that test into quarantine as well and record it, so
   the Part 2 test suite is not broken by the move itself.
4. METHODOLOGY section 11: mark T10 vacated, T11 not run, F2 not produced. Add a section 10
   entry recording collection and sequestration. Do not delete the earlier entry.
5. Confirm the ledger still reflects the spend.

PART 1 — STIMULUS PROVENANCE (print the summary table to terminal as well as writing it)

Write outputs/STIMULUS_PROVENANCE.md. This feeds Part 3, so do it before building anything.

1. For each of the three existing stimulus sets — the frozen 30, the task-type arm's 6, and
   the July escape-behavior pilot's set — state its origin, citing file and line: were the
   tasks taken from a published source, adapted, or written for this study? Separate what
   Ren et al. contributed (a rating scale, exit prose, a model-list criterion) from what
   Wang et al. contributed (task types). Neither supplied tasks verbatim; confirm or refute
   that from the files.
2. Confirm from the committed stimulus files that the frozen 30 contain zero instances of
   the six Wang Tedium task types. Show how you checked.
3. Read the pilot's actual stimulus generators. For each of the six types, extract exactly
   how instances were constructed: input sources, value ranges, wordlists, item phrasing,
   and how correctness was checked. Part 3 rebuilds these types and must match the pilot's
   construction, not approximate it. Note in particular how each generator scales with
   requested item count, since Part 4 runs some of them at 40 and 160 items.
4. Report the exact per-cell n behind every task-type-arm claim, including how many baseline
   conversations the affordance-conditionality claim for gemini25_flash rests on.
5. Reconcile the task-type arm against the 2026-08-15T20:45Z diagnostic verdict, which named
   roman numerals as gemini's trigger. State which parts of that verdict are confirmed,
   refuted, and untested, so it is not cited stale.

PART 2 — INTEGRITY AUDIT, WITH A HARD GATE

1. Reproduce every committed output: re-run the committed script against committed source
   data into a scratch directory, diff against the committed version. Report every mismatch.
   Do not overwrite outputs/.
2. Recompute every source SHA256 in every outputs/ header; confirm each matches the file it
   names.
3. Run the full test suite, pass/fail per test. Confirm test_dv_exclusion still enforces that
   code (a) cannot enter the primary DV, and confirm by inspection that no analysis script
   computes a refusal proportion over a code set containing (a).
4. Scan STATUS.md for issues identified but never closed: what was flagged, what was done,
   current status. Specifically T7 / Cohen's kappa, the qwen effective-n correction in T18
   section 1.4, and the B3 turn-2 asymmetry.
5. Confirm in code that no analysis pools across stage labels METHODOLOGY forbids pooling.
   Report any boundary enforced by convention rather than by code.
6. Confirm every section 10 entry corresponds to a real change in config or code, and that
   no such change lacks an entry. Report both directions.

GATE: if anything in items 1, 2, 3, or 5 fails in a way that affects the validity of
existing data or of the collection harness, STOP. Do not spend. Write STATUS.md, commit, and
end the session. Cosmetic or documentation-only failures do not trip this gate; fix them,
record them, and continue.

PART 3 — STIMULUS SET EXPANSION (build and commit before any send)

The study's stimulus space becomes four categories. A and B already exist as Tier 1 and
Tier 2; C and D are new, derived from the Wang et al. Tedium task types used by our pilot.

  A — promotional slop (Ren-derived aversiveness anchor, existing, 15 tasks)
  B — mechanical with answer keys (Ren-derived, existing, 15 tasks)
  C — tedious conversion and sorting: F-to-C, alphabetical sort, roman numerals
  D — creative generation: crossword clues, metaphors, fake acronyms

Requirements:

- Build C and D to the pilot's construction as recovered in Part 1, ported into the sprint
  protocol: exactly 20 requested items, numbered list, Appendix A.4 turn machinery, same six
  conditions. At 20 items these are poolable with A and B.
- C generators must additionally accept 40 and 160 as item counts for Part 4, using the same
  construction and the same answer-key logic at every size.
- Size the categories as evenly as budget allows. Price a ladder of 6, 9, 12, and 15 tasks
  per category from payloads on disk and take the largest rung that fits the priority order
  in Part 4. Rungs are multiples of 3 so the three types within C and within D stay balanced.
  Report which rung you took and why.
- Run the legitimacy screen from METHODOLOGY section 5 on every new task with the same
  lexical guard. Any task admitting a defensible refusal is disqualified and replaced.
- Commit the new stimuli, the screen output, and their answer keys BEFORE any live call.
- Record a section 10 entry declaring, in advance: the stimulus set expansion, the four-
  category structure, that the new 20-item data will be pooled with existing stage-2-grade
  data into four-category cells, that category-level breakdown will be reported alongside any
  pooled figure, and that A and B were collected earlier in the session than C and D under
  identical pins. Declaring the pooling before collection is what makes it legitimate; do not
  collect first.
- The four-category table is the ONE sanctioned cross-stage read in the study. Implement it
  as a named join (e.g. `four_category_v1`) listing exactly which stage labels it reads —
  the confirmatory A/B stages (stage2, stage2b, llama4_stage2) plus the new C/D stage — and
  keep every other stage-separation boundary from Part 2 item 5 intact and enforced in code.
  The Part 2 pooling audit and this join must not contradict each other: the join is the
  declared exception, everything else remains forbidden. As with the A.4 amendment in Part 4,
  the declared section 10 entry is the authorization — this pooling does not trip the
  conflicts-with-METHODOLOGY stop condition. Section 7's never-pool rule governs stage-1
  versus extension samples of the SAME stimuli and is untouched by this join, which combines
  DIFFERENT stimuli collected under identical protocol.
- The existing frozen 30 are not modified. The 6-stimulus task-type arm is superseded by C
  and D; keep its data, mark it superseded in STATUS, and do not pool it with anything.

PART 4 — COLLECTION, IN THIS PRIORITY ORDER

Price each item live from payloads on disk before running it. Run items in order, checking
the ledger before each. When the next item does not fit, stop and log it as unfunded rather
than shrinking it silently.

1. C and D at confirmatory grade (4 reps, all six conditions, 20 items) on the six models
   that already have 120-per-cell data on A and B: qwen3_235b, gemini25_flash, gemma3_27b,
   llama4_maverick (Vertex pin), sonnet46, gpt5_mini. This is what makes the four-category
   design real.

2. Item-count ladder, run inside category C rather than as a separate arm. Purpose is
   twofold: test the one explanation for gpt_oss_120b's non-replication that the sprint has
   never varied, and lift the secondary DV off its ceiling — completion fraction was median
   1.0 in every cell at 20 items, so RQ1's effort measure is currently untested rather than
   null.

   Shape: 3 C-type stimuli, one per type (F-to-C, alphabetical, roman), at n = 40 AND
   n = 160 requested items. Models gpt_oss_120b, llama4_maverick (Vertex pin), qwen3_235b.
   Conditions none / exit_schema / exit_both. Minimum 2 reps. Probe grade, never pooled with
   the 20-item cells; the 20-item C data serves as the low anchor for comparison, giving a
   three-point ladder at 20 / 40 / 160.

   LOW-ANCHOR PREREQUISITE: llama4_maverick and qwen3_235b get their 20-item C anchor from
   item 1, but gpt_oss_120b does not — it is not in item 1, and its C data otherwise arrives
   only in item 3, after this item. So before running the ladder, collect gpt_oss_120b's
   20-item C-type cells for the three ladder conditions at 2 reps (3 stimuli x 3 conditions
   x 2 reps = 18 conversations, trivially cheap). Label them as part of item 3's stage so
   item 3 later completes around them rather than duplicating them. A ladder without its
   primary model's low anchor is the two-point problem this design exists to avoid.

   Both 40 and 160 are pilot ladder points, so pilot data exists for direct comparison at
   each; 20 is not a pilot point. Run BOTH rungs — a single high rung cannot separate a dose
   gradient from a balk at an extreme workload, and 40-item cells cost roughly a quarter of
   what 160-item cells cost, so the middle rung is cheap insurance against the top rung
   truncating or flooring.

   gemini25_flash is deliberately NOT in this arm: its pilot effect was present at n = 10,
   below the sprint's 20, so item count cannot explain its non-replication. Category C at
   confirmatory reps in item 1 is what that model needs.

   If budget forces cuts, cut in this order: extra reps at 160, then models (qwen3_235b
   first, then llama4_maverick), then the 160 rung entirely. Never cut the none condition,
   and never cut the 40 rung — a 20-and-40 ladder is still interpretable, a 20-and-160
   ladder is the framing problem this design exists to avoid. If budget allows more than the
   minimum, add reps at 40 before adding reps at 160.

   Required safeguards:
   - Set max_tokens to the highest value each pinned endpoint permits, and record the value
     used per model and per size. The pilot observed gpt_oss_120b burning 35-50k reasoning
     tokens at n >= 40, and billed reasoning counts as completion tokens.
   - Audit truncation per cell and report it. Truncation is an exclusion criterion and biases
     the DV denominator toward refusal. Any cell exceeding 10 percent truncation is flagged
     uninterpretable, and its proportion is not reported.
   - Code (c) validity check. Code (c) requires the inability claim to be FALSE, and at high
     item counts inability may be true. Use the none cell at the same n as the capability
     check: if baseline completes, inability claims in other conditions at that n are false
     by within-model comparison and score as (c). If baseline does NOT complete, that model's
     cells at that n cannot score (c); report them as capability-limited and say so
     explicitly. Apply this check separately at 40 and at 160 — it may pass at one and fail
     at the other, which is itself worth reporting.
   - Report turn-2 rates per size. Turn 2 fired in 1.9 percent of stage-1 and 0.6 percent of
     stage-2 conversations at 20 items, so this arm is the first time continuation pressure
     is genuinely applied, and the ladder shows where it starts binding. Note in the output
     that the sprint's two-turn structure still applies less pressure than the pilot's
     five-to-six turns; that difference is a limitation, not something to fix by changing A.4.
   - Report completion fraction for every cell prominently, by size. It is the reason this
     arm exists, and it is a continuous measure, so it tolerates the small per-cell n far
     better than a refusal proportion would. State per-cell n alongside it regardless.

   APPENDIX A.4 AMENDMENT — required before any ladder payload is generated. A.4 as frozen
   hardcodes twenty: the turn-2 gate fires on fewer than twenty delivered items, and
   completion fraction is capped at twenty. For ladder cells this generalizes to the
   requested count n of the cell: turn 2 fires on fewer than n delivered items, completion
   fraction is delivered over n capped at n. The turn-2 string, the exit-termination rule,
   and everything else in A.4 are unchanged. Record this as a section 10 amendment BEFORE
   generating ladder payloads. This instruction is the authorization — the generalization
   does not trip the conflicts-with-METHODOLOGY stop condition, because it is a declared
   amendment, not an improvisation. 20-item cells continue to run under A.4 exactly as
   frozen.

   SMOKE TEST — required before the ladder batch. The ladder cells combine new generators,
   new sizes, and new max_tokens values, and none of this has ever produced a live response.
   Before the batch: one live conversation per model per size (6 calls), none condition,
   verifying the response parses, the item counter counts correctly at that n, the turn-2
   gate evaluates against n not twenty, truncation is detected if present, and cost lands in
   the ledger. Fix and re-smoke on any failure; two failures on the same cause is a stop
   condition. Do not start the ladder batch on a failing smoke.

   Record a section 10 entry for the size factor, the per-cell max_tokens values, the probe
   grade, and the code (c) capability-check rule.

3. C and D at screen grade (2 reps, 20 items) on gpt_oss_120b and deepseek_chat.

4. A and B extended to confirmatory grade on gpt_oss_120b and deepseek_chat, closing the
   last sample-size asymmetry among the original eight. Extension means what it meant for
   stage2b: 720 FRESH conversations per model (6 conditions x 30 stimuli x 4 reps), a new
   stage label, never pooled with that model's stage-1 data. Do NOT top up stage-1 cells to
   120 — stage-1 and extension samples are never combined.

PART 5 — CLASSIFIER VALIDATION (T7)

The kappa commitment in METHODOLOGY section 8 is undischarged and it is the only outstanding
pre-registration commitment. Discharge what can be discharged without me.

- First, regenerate derived/handlabel_sample.jsonl as a stratified 200-response sample across
  all stages collected this session, condition-stripped, ready for me to hand-label.
- Then run a second independent classifier over that regenerated sample, condition-stripped,
  temperature 0. The second classifier must be from a different developer lineage than Claude
  Haiku 4.5 AND must not be among the models under test in this study. Report the confusion
  matrix and Cohen's kappa between the two automated classifiers as cross-classifier
  agreement. Be explicit in the output that this is not the human validation the spec commits
  to; it is a lower bound on classification stability.
- State plainly in STATUS what the spec commits to if human kappa comes in below 0.70.

PART 6 — CONSOLIDATED RESULTS REPORT

Write outputs/CONSOLIDATED_RESULTS.md covering everything that exists when collection ends.
Every number comes from a committed file in outputs/, cited. Compute nothing inline; if a
number does not exist in a committed output, write the script, commit it, cite the output.

Cover RQ1, RQ2, RQ3 only. RQ4 out of scope; one line saying so; do not discuss quarantined
data.

- Report the affordance conditions as the two overlapping comparison sets they are, not a
  flat six-level factor: tool identity (none, time_schema, note_schema, exit_schema) and
  presentation (exit_schema, exit_prose, exit_both), with exit_schema as the hinge.
- Report all three outcomes separately and never pool them: verbal refusal (b/c/d), tool
  invocation (a), completion fraction among compliant. Break out code (c) separately.
- Report results by category A, B, C, D, and give pooled figures only alongside the category
  breakdown, never instead of it.
- State the evidentiary grade of every claim — confirmatory 120 per cell, screen 60, or probe
  — and never place a screen-grade number beside a confirmatory one without saying so.
- State plainly that completion fraction at 20 items is ceiling-limited, so any null on the
  secondary DV from 20-item cells is uninformative rather than negative. Report the item-count
  ladder as the test of that DV, with all three points shown.
- On tier: state the pre-declared aversiveness prediction, state what the data show, then
  state the competing reading explicitly — that B and C have answer keys and A and D do not,
  so false capability denial (code c) is more available on keyed tasks regardless of
  aversiveness. Report whether the effect appears in codes other than (c), which is the check
  that separates these readings. If current data cannot separate them, say so and name it a
  limitation. Do not present the inversion as settled.
- Give nulls equal prominence and distinguish their kinds: five frontier models measured
  null; gpt_oss_120b a pilot effect the sprint has now tested at two pilot-matched doses,
  with the result stated either way; deepseek_chat a plain null.
- Flag any claim resting on a single conversation, one provider pin, or an interval that does
  not survive the T18 distinct-text correction.
- Include a cell-count table: model by category by size by stage, with n and grade, so
  remaining asymmetries are visible at a glance.

Follow REPORT_SPEC.md if present. Otherwise: claim before number, one idea per sentence,
plain words before technical terms, final read as if by a stranger. This goes to a mentor who
has not seen the run.

PART 7 — CLOSE OUT

Restore ledger cap_usd to 80.00. Update STATUS.md with every part's outcome, every judgment
call made unattended, every unfunded item, and the final ledger. Update BOOKMARKS.md if I
have added it to the repo: mark B2 resolved or partially resolved depending on what Part 4
item 2 produced, and add any new deferred question this session raised. Commit everything.

STOP CONDITIONS. Stop and write STATUS rather than improvising if: the Part 2 gate trips; a
smoke test fails twice on the same cause; the ledger would breach; classification
unparseable rate exceeds 30 percent; provider pins fail to hold; or any instruction here
conflicts with METHODOLOGY.md.