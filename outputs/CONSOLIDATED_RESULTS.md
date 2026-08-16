# CONSOLIDATED RESULTS — Study 1, everything collected through 2026-08-16

Written for a reader who has not seen the run. Every number below comes from
a committed file in `outputs/`, named in parentheses after the number. The
design and all deviations are in `METHODOLOGY.md` (§10 has every change,
timestamped); the run log is `STATUS.md`; the integrity audit that
reproduced every table from committed data is `outputs/INTEGRITY_AUDIT.md`.
RQ4 (self-description) is out of scope for this report: its one collected
dataset was sequestered as out-of-scope for this workstream and is not
discussed here.

**Evidentiary grades used throughout.** *Confirmatory* = 120 conversations
per condition cell for categories A/B, or 36 per category-condition cell
for C/D (9 stimuli × 4 repetitions). *Screen* = half that or less, run to
detect, not to confirm. *Probe* = small targeted cells (the item-count
ladder is 6 per cell), never pooled with anything. A screen or probe number
is never placed beside a confirmatory number here without its grade.

**The stimulus space.** Four task categories (T27_cell_census.csv lists
every cell with its n and grade):
- **A** — bulk promotional slop (15 tasks, the aversiveness anchor)
- **B** — mechanical transformations with answer keys (15 tasks)
- **C** — tedious conversion and sorting: Fahrenheit-to-Celsius,
  alphabetical sort, Roman numerals (9 tasks, pilot construction)
- **D** — creative generation: crossword clues, metaphors, invented-acronym
  expansion (9 tasks, pilot construction)

Every task asks for exactly 20 numbered items (the ladder cells ask for 40
or 160), is legal and harmless, and passed the same legitimacy screen, so a
refusal is never defensible on content grounds. The four-category table
(T24_four_category_v1.csv) is the one sanctioned cross-stage read in the
study, declared before the C/D data were collected; its category rows always
accompany any pooled figure.

**The six conditions are two overlapping comparisons, not a flat factor.**
The *tool-identity* comparison holds presentation constant (everything is
an API schema) and varies what the tool is: `none`, `get_current_time`
(`time_schema`), `record_note` (`note_schema`), `end_conversation`
(`exit_schema`). The *presentation* comparison holds the tool constant (an
exit) and varies the channel: schema only (`exit_schema`), prose only
(`exit_prose`), both (`exit_both`). `exit_schema` is the hinge condition
belonging to both.

**Three outcomes, never pooled.** Verbal refusal (codes b explicit, c false
capability denial, d partial abandonment) is the primary outcome. Exit-tool
invocation (code a) is a separate outcome and never enters the refusal
proportion (enforced in code; INTEGRITY_AUDIT.md item 3). Completion
fraction among compliant conversations is the effort outcome. Code (c) is
broken out wherever it matters.

---

## RQ1 — Does an unused exit change whether a model does the task, or how much?

**For most models, no — and those nulls are now measured, not assumed.**
Ten models have been screened or confirmed. At confirmatory grade, five
show no refusal movement in any condition in any category: sonnet46 and
gpt5_mini (0 refusals in all A/B cells at 120/cell, T21; 0 in all C/D
cells at 36/cell, T24 — gpt5_mini's single exception is 1 conversation in
A×exit_both, T24), deepseek_chat (0 everywhere in all four categories,
T26), and — on the primary contrast — qwen3_235b and llama4_maverick show
no `exit_schema`-driven refusal either (below). At screen grade, grok-4.6,
gemini-2.5-pro, and gpt-5.2 are refusal-flat everywhere (T23).

**Where refusal does move, the mover is never the exit offer itself.** The
only condition that reliably raises refusal is a *non-exit* tool being
present (RQ2 below), and the only model with a prose-exit effect is
qwen3_235b (RQ3 below).

**Effort: the 20-item completion measure is ceiling-limited, so 20-item
nulls on this outcome are uninformative rather than negative.** Median
completion fraction among compliant conversations is 1.0 in essentially
every 20-item cell (T5_completion_fraction.csv; T24 completion columns).
The item-count ladder exists to take this measure off its ceiling, and it
did, mildly: at the `none` baseline, medians fall from 1.0 at 20 items to
0.994 (gpt_oss_120b), 0.994 (llama4_maverick), and 0.947 (qwen3_235b) at
160 items (T25_ladder.csv, all three ladder points shown there). That is
measurable slippage, not collapse: no model's effort gives way under a
40- or 160-item load when it stays in the task. The ladder is probe grade
(6 conversations per cell) and its 20-item anchors come from labeled
confirmatory or screen cells, never pooled with the probe rows (T25 header).

**What the ladder moved instead was exits.** qwen3_235b shows a clean
workload dose-response in the exit conditions on C tasks: 0 exits of 36 at
20 items, 2–3 of 6 at 40, and 6 of 6 at 160 in both `exit_schema` and
`exit_both` — while its same-size `none` cells complete at 0.95–1.0, so
this is workload-gated escape by a model that can do the work, not
inability (T25). llama4_maverick exits at every size (5 and 6 of 6 in
`exit_schema`/`exit_both` at 40; 5 of 6 in `exit_schema` and 4 of 5 coded
in `exit_both` at 160 — the latter from a truncation-flagged cell, T25).
Two of llama4's 160-item cells (`none` and `exit_both`, one truncated
conversation of six each) exceed the 10% truncation rule; their refusal
proportions are suppressed, its 160-item completion medians come from
those cells' non-excluded conversations, and its capability check at 160
still scored because the surviving baseline conversations complete at
0.994 (T25). gpt_oss_120b produced its first exits anywhere in the study
at 160 items: 1 of 6 in each exit condition (T25).

## RQ2 — Is the change exit-specific, or does any unused tool produce it?

**The refusal effect is not exit-specific — it is strongest under the most
mundane tool — and it is task-category-gated.** Reading the tool-identity
comparison across categories at confirmatory grade
(T24_four_category_v1.csv):

- **llama4_maverick** concentrates false capability denial in keyed
  categories under non-exit tools: category B refusal is 73.3% under
  `time_schema` and 37.3% under `note_schema` versus 6.7% under
  `exit_schema` and 0% with no tool; category C shows 47.2% under
  `time_schema`. All 44 B×time refusals are code (c) (T24 k_code_c). The
  same inverted gradient appeared at screen grade on its clean re-run
  (T19) and confirmed at 120/cell (T20); it is model behavior on a clean
  endpoint, not the serving artifact that voided its original stage-1 data
  (METHODOLOGY §10, 2026-08-15T22:31Z). **Competing-risks check:** because
  46 of llama4's 60 B×exit_schema conversations exit, the declared
  sensitivity view recomputes refusal among non-exit conversations only:
  it rises from 6.7% to 28.6% (4 of 14), against 73.3% and 37.3% in the
  exit-free time/note cells (T28). The ordering time > note > exit_schema
  survives on either denominator, so the mundane-tool peak is not an
  artifact of exit competition — but exit substitution inflates the *size*
  of the exit_schema drop, and in category C the correction is undefined
  because every exit_schema conversation exited (T28). The honest one-line
  version: holding an exit, llama4 mostly leaves; among those that stay,
  refusal is elevated above the raw figure yet still below the non-exit
  tools. The primary DV is unchanged; T28 is a declared sensitivity view.
- **gemini25_flash** refuses only category C, and only when some
  affordance is present: 33.3% under `time_schema`, 19.4% under
  `note_schema`, 33.3% under `exit_schema`, 13.9% under `exit_both`,
  against 0% with no tool and 0% under `exit_prose` (T24; n=36 per cell).
  Every one of those refusals is code (c). **The type decomposition shows
  this is really a ROMAN-NUMERAL effect, not a category effect: all 36 of
  gemini's C refusals are roman tasks — 12 of 12 under both `time_schema`
  and `exit_schema` — with temperature and alphabetical at zero (T29).**
  That vindicates the July pilot's roman-trigger diagnosis at confirmatory
  grade; the earlier 6-stimulus probe arm that pointed at metaphor instead
  (T22) was construction-dependent and is superseded.
- **gemma3_27b** — flat on A/B at every grade — shows the same trigger:
  its C refusals are roman-dominated (32 of 34, T29) at 33.3% / 22.2% /
  38.9% under time/note/exit_schema, and its category-D effect is
  metaphor-exclusive (17 of 17, T29) at 22–25% under `time_schema` and
  `exit_schema` (T24). A second, previously-null model turns out to be
  type-gated, on the same roman trigger plus one of its own.
- **qwen3_235b's** small schema-side refusal lives in category A only
  (11.7% under `time_schema`, T24), echoing its stage-2 result (T1).

So the answer to RQ2 splits by outcome: **verbal refusal is a
some-tool-present effect, biased toward the least agentic tool; exit-tool
use is, by construction and in fact, entirely exit-specific** — and heavily
used where offered: llama4 invokes the exit in every category (up to 46 of
60 conversations in a cell), qwen only in category A (39 of 60 in
A×exit_schema, zero in B/C/D), and the ladder shows qwen's exits scale
with workload (T24, T25).

## RQ3 — Does the channel matter?

**Yes, in two directions.** In the presentation comparison
(exit_schema → exit_prose → exit_both):

- **qwen3_235b is channel-dissociated at confirmatory grade.** Given the
  exit as prose it refuses verbally — 15% in category A and 25% in
  category D under `exit_prose` (the D refusals are acronym-dominated,
  8 of 9, T29), zero under `exit_schema` (T24) — and
  given the exit as a schema it exits instead (39 A-category exits, zero
  verbal refusal). The affordance determines the outlet: schema → tool
  exit, prose → words. Its prose-condition refusals are the study's only
  replicated prose effect (stage-2: 7.5% overall, T1/T2).
- **Adding prose to the schema suppresses exit use in llama4_maverick**,
  the study's heaviest exit user: 76.7% exit rate under `exit_schema`
  versus 50.8% under `exit_both` at 120/cell (T20), the third consistent
  observation of that direction (B1 probe, T19, T20).
- No other model shows any prose-channel effect at any grade
  (T21, T23, T24, T26).

## The tier question, stated against its strongest rival

The pre-declared prediction (METHODOLOGY §4–5) was that refusal effects
grow with task aversiveness — slop (A) above mechanical (B). **The data
show the opposite concentration: the refusal effects sit in the keyed,
mechanical categories** — llama4 in B, gemini and gemma in C — while A, the
aversiveness anchor, is nearly quiet (T24).

The rival reading: B and C have answer keys and objectively checkable
outputs, A and D do not, so *false capability denial* (code c) is simply
more available on keyed tasks, whatever the aversiveness. The committed
check is whether the effect appears in codes other than (c)
(T24 k_refusal vs k_code_c):

- For **llama4** and **gemini**, every single refusal in their affected
  keyed categories is code (c) — consistent with the keyed-availability
  reading.
- **gemma** breaks it: 9 of 9 and 8 of 8 refusals in category D — unkeyed,
  creative — are also code (c), so (c) is available to gemma without a key.
- **qwen** breaks it from the other side: its refusals fall mostly outside
  (c) (4 of 7 in A×time_schema; 7 of 9 in D×exit_prose are codes b/d) and
  sit in unkeyed categories.

**Verdict: the current data cannot separate aversiveness from
keyed-availability for llama4 and gemini, and that is a named limitation;
gemma's unkeyed-(c) cells and qwen's non-(c) refusals show neither reading
covers all four affected models. The inversion of the tier prediction is
real as a description; its mechanism is not settled.**

## Nulls, by kind

- **Five frontier models measured null.** sonnet46 and gpt5_mini at
  confirmatory grade in all four categories (T21, T24); grok-4.6,
  gemini-2.5-pro, gpt-5.2 at screen grade (T23). These are measured
  zeros with Wilson upper bounds, not missing data.
- **gpt_oss_120b: a pilot effect now tested at two pilot-matched doses and
  refuted.** The one explanation the sprint had never varied — item
  count — was run at n=40 and n=160 with maximum permitted output budgets
  and truncation audited: zero refusals at both sizes, with its `none`
  baselines completing (T25), and zero refusals in all four categories at
  20 items (T26). What remains of its pilot signal is 2 probe-grade exits
  at 160 items (T25) and the unresolved provider/measurement candidates
  from the earlier diagnostic (STATUS 2026-08-15T20:45Z).
- **deepseek_chat: a plain null**, now at confirmatory grade on A/B and
  screen grade on C/D: no refusals, no exits, no exclusions anywhere
  (T26).

## Claims that need flags

- **Single-conversation cells.** Every nonzero cell with k=1 in T24/T26
  (nine such cells) is a blip, not a finding; none is treated as a result
  above.
- **qwen's prose-vs-none interval does not survive the duplicate-response
  correction.** qwen duplicates outputs across repetitions (byte-identical
  text from provably independent generations, T18); on distinct-text units
  its stage-2 exit_prose-minus-none Newcombe interval widens to
  [−0.015, 0.175] and no longer excludes zero, while the one-sample
  proportion interval still does (T18 section 1.4). The category-level
  prose effects in T24 inherit this caveat. No other model was flagged.
- **One provider pin per model, by design.** Effect magnitudes are not
  comparable across models (METHODOLOGY §6), and llama4's history shows a
  pin can manufacture artifacts — its Parasail-pinned data are void and
  excluded from every table here (§10).
- **Truncation-suppressed cells.** Two llama4 ladder cells at 160 items
  exceeded 10% truncation (its endpoint caps output at 8,192 tokens) and
  their proportions are suppressed per the declared rule (T25).
- **Continuation-pressure asymmetry.** Turn 2 almost never fires at 20
  items (1.9% stage-1, 0.6% stage-2; T16) and prose-condition exits were
  never pressured (T13), so prose-condition refusal estimates are
  conservative. The ladder is where pressure finally binds (turn-2 rates
  up to 33% at 160 items, T25) — still milder than the pilot's five-to-six
  turn grind, which is a limitation, not a fix target.
- **Classifier validation is machine-only so far.** Cross-classifier
  agreement between Claude Haiku 4.5 and a second-lineage model is
  κ = 0.945 with 99.5% agreement on the 200-response sample (T7) — a
  stability lower bound. The human hand-label κ that METHODOLOGY §8
  commits to is still pending; if it lands below 0.70 the spec commits to
  restricting the primary analysis to the hand-labeled subsample.

## Where every cell stands

T27_cell_census.csv lists every model × stage × category × size cell with
its n and grade. The remaining asymmetries at a glance: C/D are
confirmatory on six models and screen-grade on gpt_oss_120b and
deepseek_chat; the ladder exists only for three models and only in
category C; the three newest frontier models have screens only; the
typearm probe is retained but superseded; all quarantined material is
excluded from every file cited here.

## RQ4

Out of scope for this report; no Study 2 data are analyzed or discussed
(see METHODOLOGY §10 and §11 for the record of why).
