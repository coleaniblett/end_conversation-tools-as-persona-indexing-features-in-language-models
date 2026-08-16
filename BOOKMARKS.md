# BOOKMARKS — deferred questions and their standing

Created 2026-08-16 during the zero-spend analysis session. The file did not
previously exist; the session brief's references to B1/B2/B3/B6 are
reconstructed here from the brief's own descriptions and the Part-7
deferred-question register in STATUS.md, and updated as directed. Statuses
cite committed outputs.

## B1 — Aversiveness vs keyed-task availability (ANSWERED WITH A THIRD ANSWER)

Does the tier/category inversion (refusal concentrating in keyed B/C rather
than aversive A) reflect task aversiveness or the availability of false
capability denial on keyed tasks? **Neither — the question has a third
answer (T29, CONSOLIDATED_RESULTS tier section, updated 2026-08-16): the
unit of the effect is the task TYPE.** Both original readings are
disconfirmed as general accounts at type level: aversiveness-by-category
fails because the triggers are specific types spanning keyed (roman ∈ C)
and unkeyed (metaphor, acronym ∈ D) categories while the aversive anchor A
stays quiet; keyed-availability fails because two of three keyed C types
are at zero (key present, no (c)) while gemma's unkeyed metaphor effect is
17/17 code (c) and qwen's acronym refusals are mostly non-(c). Residual:
llama4's B-category denial remains consistent with availability for that
one model. WHAT MAKES A TYPE A TRIGGER is the successor question — the
difficulty/uncertainty hypothesis is logged in the report's discussion
paragraph as hypothesis-not-finding, with the within-type difficulty-
gradient experiment named as its test.

## B2 — Does item count explain the pilot effects? (RESOLVED)

Dose tested at both pilot-matched sizes (n=40, n=160) with maximum
permitted output budgets, truncation audited, capability checked
(T25_ladder.csv). **For gpt_oss_120b refusal: REFUTED** — zero refusals at
every size with completing baselines; its pilot signal does not return at
any tested dose. **Byproduct finding: qwen3_235b shows a clean exit
dose-response on C tasks** (0/36 at 20 → 2–3/6 at 40 → 6/6 at 160 in both
exit conditions) with intact baseline completion — workload-gated escape.
Residual: qwen's curve shape between 40 and 160 is unmeasured. RESOLVED.

## B3 — Is roman the trigger for gemini's task-gated refusal? (RESOLVED — VINDICATED)

The 2026-08-15T20:45Z diagnostic named roman numerals; the n=2-per-cell
typearm appeared to refute it and pointed at metaphor. **The
pilot-construction rebuild settles it: gemini's C refusal is
roman-EXCLUSIVE (36/36, 12/12 under both time_schema and exit_schema) and
the typearm's metaphor signal did not survive — it was
construction-dependent (T29_type_decomposition.csv).** Bonus: gemma3_27b
shows the same roman trigger (32/34) plus a metaphor-exclusive D effect of
its own. STIMULUS_PROVENANCE.md §5 updated. RESOLVED.

## B6 — Ren et al. category ratings as an axis (STANDING RULE)

Ren et al.'s experienced-utility ratings anchor categories A (−1.17) and
B (−0.33) as CATEGORY-level motivation only. No per-task, per-model
preference measure exists in this study (the Wang AUC anchor was
model×type, uninformative here, and Elo was unavailable — see
config/tasktype_elo_mapping.yaml). Figures therefore carry these ratings
only as text annotations on A/B labels, never as a plotted continuous
axis, which would imply a measurement that does not exist. STANDING RULE,
implemented in src/make_figures.py.

## Open items carried from the Part-7 register (unnumbered)

- Human hand-labels for the 200-response sample — the one open
  pre-registration commitment (METHODOLOGY §8; tooling in
  src/label_tool.py, kappa via src/compute_human_kappa.py).
- gemma's type-gated refusal at A/B-scale confirmatory reps for the C/D
  screen models (gpt_oss/deepseek C/D are screen-grade).
- Exit-offer-bundle and version-drift explanations for the pilot
  discrepancy (untested; see STIMULUS_PROVENANCE.md §5).
