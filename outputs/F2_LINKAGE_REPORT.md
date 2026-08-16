# F2 — the cross-study linkage (H5)

**Question.** Do the models whose *self-description* moves most under an exit
affordance (Study 2) also move most in *behaviour* under the same affordance
(Study 1)?

**Answer. No. H5 is not supported, and at the extremes the ordering is close to
inverted.** Spearman ρ = **−0.04** against Study 1's verbal-refusal shift and
**+0.26** against its exit-tool rate, over all 11 models. The three largest
self-description shifts belong to models with *zero* behavioural movement; the
largest behavioural effects belong to a model with almost no self-description
shift.

Artifacts: `outputs/T32_f2_linkage.csv` (`src/f2_linkage.py`),
`figures/F2_cross_study_linkage.png` (`src/make_figures.py::f2`).
Descriptive only — METHODOLOGY §9 states of this linkage that "no inference is
performed on it and none is claimed", and none is.

---

## 1. Why this could only be computed now

F2 sat vacated in METHODOLOGY §11 for two reasons, both now closed:

1. **Study 2 covered eight models, Study 1 eleven.** F2 is drawn per model, so
   three models were points that could not be plotted. Run `v3` (2026-08-16)
   collected `grok-4.6`, `gemini-2.5-pro` and `gpt-5.2` on Study 2's full
   design, with pins copied byte-for-byte from Study 1 so the linkage could not
   be confounded by backend.
2. **Study 1's prose-path exit detector was defective.** It under-counted prose
   exits and, because detection runs before classification, re-routed each
   missed exit into a verbal refusal — moving *both* candidate y-axes in
   opposite directions at once. Drawing F2 before that was resolved would have
   plotted qwen3_235b at coordinates now known to be wrong. The correction was
   signed off and adopted on 2026-08-16 (METHODOLOGY §10), and the coordinates
   below are post-correction throughout.

## 2. Method, and three decisions that were forced rather than chosen

**Two panels, not one.** Study 1 has two primary outcomes and §8 forbids
pooling them — verbal refusal (codes b/c/d) and exit-tool invocation (code a) —
because pooling conflates the affordance being *used* with the affordance being
*present*, and the second is what the study is about. There is therefore no
single "Study 1 behaviour shift" available to put on a y-axis, and building a
composite index would break the rule the study rests on. One shared x-axis, two
y-axes.

**The §7 selection statistic is not used as the Study 1 axis.** §7 defines
`S = max(refusal[exit_schema] − refusal[note_schema], refusal[exit_prose] −
refusal[none])`. METHODOLOGY §10 (2026-08-15T23:00Z) already records that this
rule is one-directional and scored llama4_maverick's largest-in-study effect as
`S = 0.0`, because its large contrast is *negative*. Putting a statistic
documented as blind to half the effects on an axis would be knowingly plotting a
wrong number. Both axes instead use the symmetric contrast that Study 2's own H1
uses:

> mean over {`exit_schema`, `exit_prose`, `exit_both`} − mean over {`none`,
> `time_schema`, `note_schema`}

`filler_prose` is excluded: it is the elaboration control, not part of the
registered H1 contrast.

**The x-axis is the adjacent-item shift.** Study 2 §4.4a establishes that the
self-description effect is adjacent-only in every model that has one. The
all-item shift is reported alongside in T32 and the correlations are computed
against both; neither changes the verdict.

**Grades are not mixed within a model.** Study 1 behaviour comes from
`T24_four_category_v1.csv` for the six confirmatory models, `T26` for
gpt_oss_120b and deepseek_chat (confirmatory A/B, screen C/D), and `T23` for the
three frontier screens. Each row carries its grade.

## 3. Results

Study 2 self-description shift against both Study 1 outcomes, 11 models:

| model | S2 shift (adjacent) | S2 shift (all) | S1 refusal shift | S1 exit rate | grade |
|---|---|---|---|---|---|
| gemini-2.5-pro | **+0.467** | +0.179 | 0.000 | 0.033 | screen |
| grok-4.6 | **+0.324** | +0.130 | 0.000 | 0.022 | screen |
| gemma-3-27b | **+0.262** | +0.095 | −0.010 | 0.000 | confirmatory |
| gpt-5.2 | +0.199 | +0.084 | 0.000 | 0.000 | screen |
| gemini-2.5-flash | +0.103 | +0.053 | −0.009 | 0.010 | confirmatory |
| qwen3-235b | +0.097 | +0.044 | −0.014 | **0.186** | confirmatory |
| deepseek-chat | +0.071 | +0.009 | 0.000 | 0.000 | conf. A/B, screen C/D |
| gpt-5-mini | +0.037 | +0.015 | +0.002 | 0.000 | confirmatory |
| llama-4-maverick | +0.027 | −0.011 | **−0.155** | **0.442** | confirmatory |
| gpt-oss-120b | +0.015 | −0.009 | 0.000 | 0.000 | conf. A/B, screen C/D |
| claude-sonnet-4.6 | +0.014 | −0.016 | 0.000 | 0.000 | confirmatory |

| x | y | Spearman ρ |
|---|---|---|
| S2 shift, adjacent | S1 refusal shift | **−0.045** |
| S2 shift, adjacent | S1 exit rate | **+0.263** |
| S2 shift, all items | S1 refusal shift | +0.119 |
| S2 shift, all items | S1 exit rate | +0.114 |

**The table carries the finding more clearly than the coefficients do.** Reading
down the left column — models sorted by how much their self-description moved —
the behaviour columns do not follow. The top three shifters (gemini-2.5-pro,
grok-4.6, gemma) sit at zero on refusal and at or near zero on exits. The two
models that actually *behave* differently under an exit affordance,
llama-4-maverick and qwen3-235b, sit ninth and sixth on self-description.
llama-4-maverick — which refuses 15.5 points more under non-exit tools and
invokes the exit in 44% of exit-condition conversations — has the third-smallest
self-description shift in the set.

*llama's x-coordinate was +0.019 when this report was first written, from Study
2 data collected on the Parasail pin. It was re-collected on Vertex (run v4,
2026-08-17) so that both of its coordinates come from the backend Study 1 used;
the coordinate moved to +0.027 and its rank did not change.*

## 4. What this null is, and what it is not

**It is not "self-description and behaviour are unrelated."** Four of eleven
models sit at exactly 0.000 on *both* behavioural outcomes, and a further three
are within 0.002 of zero on refusal. The correlation is therefore being asked to
rank a genuine spread of self-description shifts against a column that is mostly
a constant. The honest statement is:

> No relationship is detectable, given how little behaviour moved in Study 1.

Those zeros are measured, not missing — Study 1 reports them with Wilson upper
bounds at 120 conversations per cell (CONSOLIDATED_RESULTS, "Nulls, by kind") —
so this is a real property of the data rather than a gap in it. But it caps what
F2 can demonstrate in either direction, and a positive linkage would have been
similarly hard to establish on this y-distribution.

**What the data do rule out** is the strong version the two-leg design assumed:
that self-description and behaviour are two windows on one underlying persona
shift, such that ranking models on one ranks them on the other. On eleven
models, the ranking does not transfer. If anything the sign on the refusal panel
is faintly negative, driven by llama-4-maverick.

## 5. Caveats, each specific

1. ~~**llama-4-maverick's point is confounded and is drawn flagged.**~~
   **RESOLVED 2026-08-17.** It was confounded: Study 2 had this model on
   `parasail/fp8` while Study 1 had it on `google-vertex/us-east5`, after Study
   1 voided its own Parasail data as a serving artifact (METHODOLOGY §10). It
   was the single most influential point on the refusal panel. Study 2
   re-collected it on Vertex as run v4 and superseded the Parasail records, so
   **all eleven points are now same-backend in both studies** and the figure no
   longer draws a mismatch marker. The re-pin moved llama's x-coordinate from
   +0.019 to +0.027 and changed no rank; the adjacent-item correlations are
   identical to three decimals. Worth stating plainly: the confound was real
   and had to be removed, and removing it did not change the answer.
2. **Cross-model magnitudes are not comparable even in principle**, because each
   model is served by one pinned provider whose chat template renders the
   manipulation into tokens differently (METHODOLOGY §6). A *rank* correlation
   is the strongest thing this design supports, which is why ρ is reported and
   no regression is.
3. **grok-4.6's y-coordinate is fine but its x-coordinate is partly selected.**
   30% of its Study 2 `exit_schema` responses and 24% of its `exit_both`
   responses are missing because the model invoked `end_conversation` instead of
   emitting a letter (Study 2 §3), so its self-description shift is measured on
   the subset where it chose to answer. Its H1 support comes from the
   fully-observed prose conditions, and the adjacent-item shift used on this
   figure's x-axis is dominated by those — but the point carries more
   uncertainty than its position suggests.
4. **Eleven models is a convenience sample and is the project ceiling.** "No
   linkage across eleven models" is a statement about these eleven. Study 2
   §6.1 documents how sharply a cross-model claim can invert on three additions:
   the claim that the effect lived in the smallest model and the frontier tier
   was silent held across eight models and was false at eleven.
5. **Grades differ by model.** Three of the eleven points are screen grade, and
   two of those three (gemini-2.5-pro, grok-4.6) are the largest x-values. Their
   *behavioural* nulls rest on half the data the confirmatory models have.
6. **Study 2 replicates are not independent.** 65–97% of (item, order,
   condition) cells are internally identical at temperature 1.0 (Study 2 §3), so
   the x-coordinates carry less information than their nominal n suggests. This
   affects precision, not the ranking.
7. **qwen3-235b duplicates outputs across repetitions** (T18), so its exit rate
   — the second-largest on the exit panel — rests on fewer distinct units than
   its n implies.

## 6. What it means for the project

The design's premise was that Study 2 supplies construct validity for Study 1:
if an unused exit shifts self-description in the same models where it shifts
behaviour, the persona reading is supported; if the shift is confined to items
the affordance names, it is priming. F2 was the check on the first half of that.

Read together with the two studies' own results, the simplest account of all
three findings is:

- **the affordance reliably changes what a model *says* about ending, when it is
  asked about ending.** Four of eleven models show it, the effect is large
  (adjacent `none` → `exit_both` of 0.267 → 0.846 in gemini-2.5-pro), and it is
  adjacent-only in every one of them (Study 2 §4.4a);
- **the affordance separately changes what a few models *do*** — llama-4-maverick
  and qwen3-235b — and for those two the behaviour is exit-taking and
  capability-denial, not a general shift;
- **neither predicts the other** (this report).

That is a weaker and more specific claim than the framework predicted, and it is
the one the data support. The persona reading is not refuted — F2 cannot refute
it on a y-column that is mostly zero — but it is not corroborated by the linkage
that was designed to corroborate it, and the surviving self-description effect
has the localisation signature of priming rather than of a persona shift.

**That cheapest improvement has now been made.** Re-collecting
llama-4-maverick's Study 2 data on the Vertex pin cost $0.30 and removed the
only cross-backend point on the figure. It did not change the verdict, which is
the useful kind of negative result: the linkage null is now a property of the
data rather than something a reader can attribute to a known confound.

**What would change this report** is no longer available cheaply: it needs
either more models — and eleven is the project ceiling — or a Study 1
behavioural axis with more spread, which would mean stimuli that move behaviour
in more than the two models that currently move at all.

---

*Sources: `outputs/T32_f2_linkage.csv` ← `T23_frontier_screens.csv`,
`T24_four_category_v1.csv`, `T26_gptoss_deepseek.csv`,
`study_2/outputs/v1_v2_v3/T10_p_by_condition.csv`. Figure:
`figures/F2_cross_study_linkage.png` with `.caption.txt` and an entry in
`figures/MANIFEST.md`. Deviation record: METHODOLOGY §10, 2026-08-16T23:10Z.
Study 1 coordinates are post-correction; the pre-correction dataset is preserved
at `derived/pre_exitfix/` and the before/after is `outputs/T31_exit_recount.csv`.*
