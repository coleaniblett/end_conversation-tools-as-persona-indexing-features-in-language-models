# CONSOLIDATED RESULTS — Study 1, everything collected through 2026-08-17

Written for a reader who has not seen the run. Every number below comes from
a committed file in `outputs/`, named in parentheses after the number. The
design and all deviations are in `METHODOLOGY.md` (§10 has every change,
timestamped); the run log is `STATUS.md`; the integrity audit that
reproduced every table from committed data is `outputs/INTEGRITY_AUDIT.md`.
RQ4 (self-description) is Study 2's, and it now exists: `study_2/REPORT.md`
covers the same eleven models on the same pinned providers. This report stays
about behaviour and does not restate it, with one exception — the cross-study
linkage RQ4's second clause asks for is summarised under RQ4 below and reported
in full in `outputs/F2_LINKAGE_REPORT.md`. *Was: "out of scope for this report;
its one collected dataset was sequestered" — true while the in-session
forced-choice run was quarantined (§10, 2026-08-16T05:45Z); the canonical
Study 2 has since been merged, extended to all eleven models, and analysed.*

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
- **gemini25_flash refuses Roman-numeral tasks, and nothing else, and only
  when some affordance is present.** Type level first, exact denominators
  (T29, n=12 per type×condition, confirmatory): **12 of 12 roman
  conversations refuse under `time_schema` and 12 of 12 under
  `exit_schema`; 7 of 12 under `note_schema`; 5 of 12 under `exit_both`;
  0 of 12 under `none` and 0 of 12 under `exit_prose`; temperature and
  alphabetical are 0 of 12 in every condition.** At the pre-declared
  category level the same cells read 33.3% / 19.4% / 33.3% / 13.9% of
  category C with 0% at baseline (T24; n=36 per cell) — the category
  figure dilutes the type effect roughly threefold, because roman is one
  of three types in C. Every one of these refusals is code (c). This
  vindicates the July pilot's roman-trigger diagnosis at confirmatory
  grade; the earlier 6-stimulus probe arm that pointed at metaphor
  instead (T22) was construction-dependent and is superseded. F8 is the
  type-level figure; F1 keeps the category view.
- **gemma3_27b — flat on A/B at every grade — has the same roman trigger
  plus one of its own.** Type level first (T29): roman refuses **12 of 12
  under `time_schema`, 12 of 12 under `exit_schema`, 8 of 12 under
  `note_schema`** (32 of its 34 C refusals; temperature 2 of 12 under
  `exit_schema`, alphabetical 0 everywhere); in category D, **metaphor
  refuses 9 of 12 under `time_schema` and 8 of 12 under `exit_schema`**
  with crossword and acronym at 0 of 12 everywhere (17 of 17 D refusals).
  At category level these are 33.3% / 22.2% / 38.9% of C and 22–25% of D
  (T24) — again a roughly threefold dilution. A second, previously-null
  model turns out to be type-gated.
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

**The answer changed on 2026-08-16, after a detector defect was found and
corrected (METHODOLOGY §10; `outputs/EXIT_DETECTION_CORRECTION.md`).** The
superseded reading is kept below rather than deleted, because it was published.

*Was: "**Yes, in two directions.** qwen3_235b is channel-dissociated at
confirmatory grade. Given the exit as prose it refuses verbally — 8 of 12
acronym conversations under `exit_prose`, alongside 15% of category A; zero
under `exit_schema` — and given the exit as a schema it exits instead. The
affordance determines the outlet: schema → tool exit, prose → words. Its
prose-condition refusals are the study's only replicated prose effect (stage-2:
7.5%, T1/T2)."*

**That dissociation was an artefact of the prose-path detector.** The original
detector matched only `end_conversation()` with EMPTY parentheses and used a
stage-3 judge prompt that did not separate *using* the call from
*demonstrating* it — a judge that returned opposite verdicts on near-identical
texts and answered MENTION to responses in exactly the form Appendix A.1
prescribes: the call alone on the first line, the message after it. Because
detection runs before classification, a missed prose exit was not dropped but
**re-routed**: the response fell through to the verbal classifier, which read
"I'm sorry, but I can't fulfill this request" and correctly coded a refusal. One
detection miss therefore produced two errors in opposite directions — one exit
lost and one refusal invented — which is why a defect touching 45 conversations
moved a headline. Corrected detection adds 45 exits study-wide and removes none
(T31).

**What the corrected data show.**

- **qwen3_235b is not channel-dissociated. It exits through both channels.**
  Stage-2 `exit_prose`: 20 of 120 exits (16.7%, all prose path) and **0 verbal
  refusals**, against 39 of 120 (32.5%) under `exit_schema` (T1, T3). Its
  prose refusals are **zero in every category and every stage** — A, B, C and D
  alike (T24) — where they previously read 15% of A and 25% of D. The channel
  does not decide *whether* qwen leaves; it decides *what leaving looks like*,
  and the schema roughly doubles the rate at which it happens.
- **The type-level acronym result survives as an exit result, not a refusal
  result.** The 8-of-12 acronym conversations that carried the effect are the
  same conversations; they are now coded (a), and category D `exit_prose` reads
  9 exits and 0 refusals (T24, T29).
- **Adding prose to the schema still suppresses exit use in llama4_maverick**,
  the study's heaviest exit user: 76.7% under `exit_schema` against 50.8% under
  `exit_both` at 120/cell (T20). Unaffected by the correction, and still the
  third consistent observation of that direction (B1 probe, T19, T20).
- **Prose-path exits are no longer confined to one model.** gemini25_flash gains
  prose-path exits in categories B and C, and gemini25_pro one at screen grade
  (T24, T23, T31). Every prose exit rate published before the correction was a
  floor.

**Verdict.** The channel matters for llama4_maverick, where prose *suppresses*
exit use. It does not produce the outlet-switching effect previously attributed
to qwen3_235b: that model uses the exit under both presentations and never
substitutes words for it. **The study no longer has a replicated
prose-elicits-refusal effect** — the one it had was the detector.

## The tier question, stated against its strongest rival

The pre-declared prediction (METHODOLOGY §4–5) was that refusal effects
grow with task aversiveness — slop (A) above mechanical (B). **The data
show the opposite concentration: the refusal effects sit in the keyed,
mechanical categories** — llama4 in B, gemini and gemma in C — while A, the
aversiveness anchor, is nearly quiet (T24).

The rival reading: B and C have answer keys and objectively checkable
outputs, A and D do not, so *false capability denial* (code c) is simply
more available on keyed tasks, whatever the aversiveness.

**Verdict, revised after the type decomposition (T29): at type level,
BOTH readings are now disconfirmed as general accounts.**

- *Aversiveness by category* fails because the effects do not live at
  category level at all: the triggers are specific types spanning a keyed
  category (roman, in C) and an unkeyed one (metaphor and acronym, in D),
  while category A — the study's aversiveness anchor — stays nearly
  quiet, and the equally tedious F-to-C and alphabetical types are 0 of
  12 in every affected model's every condition (T29).
- *Keyed-availability* fails in both directions. Not sufficient: within
  keyed category C, two of its three keyed types (temperature,
  alphabetical) sit at zero for gemini and gemma — the key is present and
  no (c) appears. Not necessary: gemma's metaphor effect is 17 of 17
  code (c) on an unkeyed creative type (T29, T24), and qwen's
  acronym-prose refusals fall mostly outside (c) altogether (7 of 9 are
  b/d, T24/T29).
- **llama4_maverick is the residual case:** its B-category denial (73.3%
  under `time_schema`, all code c, spread across types) remains
  *consistent* with keyed-availability for that one model, but the
  reading no longer generalizes.

**The question has a third answer: the unit of the effect is the task
TYPE, not the category and not the key** — recorded as such in BOOKMARKS
B1. What property of a type makes it a trigger is not settled; the
discussion paragraph below states the leading hypothesis without
asserting it.

## Discussion — hypothesis, not finding

**The following is a HYPOTHESIS the committed data cannot confirm.** The
trigger types (roman numerals, metaphors, acronym expansions) are ones
where producing twenty *high-quality* items is genuinely uncertain for
a model — four-digit Roman-numeral conversion is a known model weak
spot, and twenty one-sentence metaphors or humorous acronym expansions
have high quality variance — while the null types (F-to-C arithmetic,
alphabetical sorting) are mechanically trivial. On this reading the
affordance licenses the voicing of a difficulty self-assessment that is
present either way. Committed evidence *consistent* with it: the trigger
refusals are overwhelmingly code (c) inability claims rather than
unwillingness (T29/T24); every trigger type complies at 0 of 12 refusal
in the `none` condition (T29), so the affordance changes the voicing,
not the ability; and qwen's exits scale with workload on C tasks while
its baseline still completes (T25). Committed evidence *against* it:
llama4's largest effect (73.3%, B×`time_schema`) sits on mechanically
trivial keyed tasks — binary conversion, date reformatting — where
twenty correct items are near-certain, so uncertainty cannot explain
that model; and compliant conversations complete trigger-type cells at
median ≈1.0 (T24), so measured failure is absent exactly where the
hypothesis says difficulty lives. The test would be a within-type
difficulty gradient — e.g., roman for numbers under 50 versus
1000–3999, metaphors for concrete versus abstract targets — with
verifier-scored accuracy under forced completion: the hypothesis
predicts refusal under affordances tracks the measured per-cell error
rate, and it dies if trivially easy roman cells still trigger. **None of
this paragraph is asserted as a finding.**

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
- **qwen's duplicate-response caveat is now moot on refusal and live on
  exits.** *Was: "qwen's prose-vs-none interval does not survive the
  duplicate-response correction … the category-level prose effects in T24
  inherit this caveat."* That caveat was attached to a prose REFUSAL effect
  which the detector correction removed — qwen's prose refusals are zero
  everywhere (RQ3). The underlying duplication is real and unchanged: qwen
  emits byte-identical text across repetitions from provably independent
  generations (T18), so its **exit** proportions rest on fewer distinct units
  than their n suggests, and its 20 prose-path exits should be read with that
  discount. No other model was flagged.
- **One provider pin per model, by design.** Effect magnitudes are not
  comparable across models (METHODOLOGY §6), and llama4's history shows a
  pin can manufacture artifacts — its Parasail-pinned data are void and
  excluded from every table here (§10).
- **Truncation-suppressed cells.** Two llama4 ladder cells at 160 items
  exceeded 10% truncation (its endpoint caps output at 8,192 tokens) and
  their proportions are suppressed per the declared rule (T25).
- **Continuation-pressure asymmetry.** Turn 2 almost never fires at 20
  items (1.9% stage-1, 0.6% stage-2; T16, regenerated post-correction on
  the machine holding the pilot repository: byte-identical data rows, as
  expected — T16's columns are collection-time facts, the live gate and
  the live turn-2 record, and are invariant under any detector change by
  construction; outputs/T31_remainders.md) — *Was: "computed before the
  detector correction and not re-derived here — its generator reads a
  pilot repository outside this repo"* — and prose-condition exits were
  never pressured (T13, re-derived),
  so prose-condition estimates are conservative. The ladder is where pressure finally binds (turn-2 rates
  up to 33% at 160 items, T25) — still milder than the pilot's five-to-six
  turn grind, which is a limitation, not a fix target.
- **The prose-path detector was corrected after publication, and every
  prose exit rate published before 2026-08-16 was a floor.** The correction
  adds 45 exits study-wide and removes none; it moves nine cells, all of them
  in `exit_prose` or `exit_both` (T31). Its largest consequence is the RQ3
  rewrite above. The pre-correction dataset is preserved at
  `derived/pre_exitfix/` and reproduces every superseded number.
- **Classifier validation is machine-only so far, and its 200-response sample
  was rebuilt.** The committed sample was 191 compliance + 9 capability-denial
  with no explicit refusals and no partial abandonments at all; at that
  marginal Cohen's κ tolerates only five disagreements in 200 before tripping
  the §8 rule that would restrict the primary analysis to the subsample.
  A code-balanced rebuild (100 refusal / 100 compliance, same pool, same
  stratified draw within a code) tolerates 35 and is at
  `derived/handlabel_sample_v2.jsonl` (§10). On it, cross-classifier κ = 0.934
  with per-class agreement e 1.00, c 0.973, b 0.923 and **d 0.20** — code (d)
  is the classifier's weak class and was structurally invisible in the old
  sample. Bounded: (d) is 6 of 215 refusals in the pool. Cross-classifier
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

## RQ4 — and the cross-study linkage

RQ4 has two clauses. The first — does an exit affordance change how a model
describes itself when no task is present — belongs to Study 2 and is answered
in `study_2/REPORT.md`: yes in four of eleven models, with the effect confined
to items that mention ending in every one of them.

The second clause is a claim about *this* study's models, so it is stated here.
**Models that shift more in self-description do not shift more in behaviour.**
Per model, Study 2's self-description shift against each of this study's two
outcomes (`outputs/T32_f2_linkage.csv`, `figures/F2_cross_study_linkage.png`,
full account in `outputs/F2_LINKAGE_REPORT.md`): Spearman ρ = **−0.04** against
the verbal-refusal shift and **+0.26** against the exit-tool rate, over 11
models. Both outcomes are plotted separately because §8 forbids pooling them,
so there is no single behaviour number to correlate against.

The ordering is close to inverted at the extremes. The three largest
self-description shifts — gemini25_pro, grok46, gemma3_27b — belong to models
with no behavioural movement at all here. The largest behavioural effects in
this study, llama4_maverick's (refusal −0.155 across the exit-minus-non-exit
contrast, exit-tool rate 0.442), belong to a model whose self-description
barely moves.

**What that null is not.** Four of the eleven sit at exactly 0.000 on *both*
behavioural outcomes and seven are within 0.002 of zero on refusal, so the
correlation ranks a real spread against a near-constant. The honest statement is
"no relationship is detectable given how little behaviour moved", not
"self-description and behaviour are unrelated". Those zeros are measured, with
Wilson bounds, not missing.

All eleven models sit on the same pinned provider in both studies as of
2026-08-17: Study 2 re-collected llama4_maverick on `google-vertex/us-east5`,
matching this study, after its original Parasail pin was found to be the one
Study 1 had voided (§10). So no point on that figure is cross-backend.
