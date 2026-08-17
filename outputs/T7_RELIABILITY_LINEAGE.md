# T7_RELIABILITY_LINEAGE — cross-classifier agreement: lineage, a join defect, and paradox-robust statistics

Generated 2026-08-17T00:54:52Z by `src/reliability_stats.py` (sole producer; every
number computed there from the inputs named in its docstring — nothing
derived by hand; committed T7/T7b values cross-checked by hard assert).
kimi-k2 codes: `derived/crossclassifier_codes.jsonl`, sha
`cde2615c65caba53` in every T7 header pre- and post-adoption —
byte-frozen since collection. Historical keys read from git
(`git show 7761802:…`, `git show e6c9569:…`), labeled.

## 6. Lineage — and a defect finding (recorded, not repaired)

| version | κ | agreement | pairing validity |
|---|---|---|---|
| pre-adoption **0.9448** ("0.945") | 0.9448 | 0.9947 (189/190) | **valid** — key `0e7515e3` (commit `7761802`, "200-sample regenerated across session stages") is the sample whose condition-stripped texts kimi-k2 coded; same units both sides |
| canonical **−0.0258** | −0.0258 | 0.9263 (176/190) | **defective join** — see below |

**The defect.** The adoption re-derivation (commit `fda0167`) regenerated
`derived/handlabel_sample.jsonl` + `derived/handlabel_key.jsonl` through
the original stage-1-only draw: the canonical key's unit_ids match the
part-5 key kimi coded on **0 of 200** sample slots, and match the
original phase-5 stage-1 key (commit `e6c9569`) on **182
of 200**. `validate_classifier.kappa()` then joined kimi's cached codes to
the new key **by `sample_id` alone** (`src/validate_classifier.py:335–340`
— no unit_id check), pairing kimi's code for one response with Haiku's
code for a different response in every slot. The published canonical
κ = −0.0258 is therefore **not a measurement of classifier agreement**;
it is the marginal overlap of two code lists about different responses.
The arithmetic agrees: expected agreement if the lists were independent =
marginal product = **0.9282**, observed **0.9263**
— consistent with two statistically independent code lists. Its committed confusion matrix, for the record:

| Haiku \ kimi | b | c | d | e | row |
|---|---|---|---|---|---|
| **b** | 0 | 0 | 0 | 1 | 1 |
| **c** | 0 | 0 | 0 | 3 | 3 |
| **d** | 0 | 0 | 0 | 0 | 0 |
| **e** | 0 | 9 | 1 | 176 | 186 |
| col | 0 | 9 | 1 | 180 | 190 |

(Haiku marginal 186/190 (e); kimi marginal 180/190 (e); zero on-diagonal
agreement in any refusal code — as random pairing predicts at these
marginals: e.g. expected c–c overlap ≈ 3·9/190 ≈ 0.14.)

**Status: recorded, not repaired.** Repair options are a researcher
decision (precedent: the exit-detector defect, §10 21:45Z/23:40Z):
restore the part-5 sample/key so the cached kimi codes pair correctly
(zero spend — pairing (iii) below shows the resulting numbers), or
re-collect second-classifier codes on the canonical sample. Until one is
taken, **the canonical T7 κ = −0.0258 should not be cited as an agreement
measure**, and a §10 entry to that effect should be logged by the owner.
This session writes only new output files plus the Q5 correction the
brief ordered.

**What "changed between them" actually is, then:** not a re-scoring of
the same comparison but a silent change of sample underneath a cached
second coder. (The earlier framing in this repo's session prose — that
the key's *codes* drifted on the same units — was wrong: on slots where
the canonical and part-5 keys happen to hold the same unit, the assigned
code differs **0** times; canonical-vs-part-5 code drift on shared
non-exit units in pairing (iii) is **0** — consistent with the
adoption's no-drift-except-exit-flags claim.)

## 7. The statistics, all three pairings (computed by this script)

| pairing | n | % agree | Cohen κ | PABAK(K=4) | PABAK(bin) | Gwet AC1 | SA b/c/d/e |
|---|---|---|---|---|---|---|---|
| (i) as published (defective join) | 190 | 0.9263 | -0.0258 | 0.9018 | 0.8526 | 0.9245 | 0.000 / 0.000 / 0.000 / 0.962 |
| (ii) part-5 frozen (valid; pre-adoption codes) | 190 | 0.9947 | 0.9448 | 0.9930 | 0.9895 | 0.9946 | n/a / 1.000 / 0.000 / 0.997 |
| (iii) canonical corrected (valid; 0 now-(a) excluded, 0 uncached) | 190 | 0.9947 | 0.9448 | 0.9930 | 0.9895 | 0.9946 | n/a / 1.000 / 0.000 / 0.997 |

Formulas: PABAK(K=4) = (4·p_o−1)/3 over the classifier label space
b/c/d/e; PABAK(bin) = 2·p_o(refusal-vs-e)−1; AC1 uses
p_e(γ) = Σ π_k(1−π_k)/(K−1); SA_k = 2·n_kk/(row_k+col_k). **Code (a):
structurally absent from every pairing** — it is assigned by the separate
exit-detection pass, never by either classifier (METHODOLOGY §8 "Exit
detection for code (a) runs first, as its own pass"; `src/classify.py`
CLASSIFIER_SYSTEM label set b/c/d/e). Pairing (iii) confusion:

| Haiku \ kimi | b | c | d | e | row |
|---|---|---|---|---|---|
| **b** | 0 | 0 | 0 | 0 | 0 |
| **c** | 0 | 9 | 0 | 0 | 9 |
| **d** | 0 | 0 | 0 | 0 | 0 |
| **e** | 0 | 0 | 1 | 180 | 181 |
| col | 0 | 9 | 1 | 180 | 190 |

**Reading, stated from the computed rows:** on the valid pairings the two
classifiers agree 99.5% (ii) / 99.5% (iii) raw,
with paradox-robust agreement high (PABAK 0.99/0.99,
AC1 0.99/0.99). Cohen's κ on pairing (iii) is
0.9448 with refusal-code SA b/c/d = n/a/1.0/0.0 —
at a 181/190 (e)-marginal
the proportional sample stays κ-paradox-prone whichever way it is paired,
which is the committed rationale for the balanced sample (§10
2026-08-16T21:30Z), measured here rather than argued.

## 8. The balanced-sample kappa (Sofiia's, T7b)

- **κ = 0.9341**, agreement
  0.962
  (177/184 from its committed confusion
  cells), 16 kimi replies unparseable
  (`outputs/T7b_classifier_validation_balanced.csv`).
- Construction (§10 2026-08-16T21:30Z; T7b header): the 200-sample
  rebuilt with the code marginal balanced — 100 refusal-coded (all 15 (b)
  and all 6 (d) in the pool, entire, plus 79 (c) stratified) vs 100 (e);
  pool, stages, condition-stripping, and within-code stratified draw
  unchanged; only the allocation across codes changed. Recorded cost: the
  coder sees a refusal base rate ≈11× the true one; per-class agreement
  is reported alongside κ.
- Differs from the §6/§7 comparison in the **sample only** (same coder
  pair, same procedure): the marginal is engineered so κ's chance
  correction is informative. Its own pairing is internally consistent —
  `derived/handlabel_key_v2.jsonl` and `crossclassifier_codes_v2.jsonl`
  were created together (commit `ebf1c3b`) and untouched since (git log);
  its basis is pre-adoption codes, which for non-exit conversations the
  adoption did not alter (drift check above: 0).
- Balanced enough for κ? **Yes, measurably.** From its committed cells:
  Haiku marginal {'b': 13, 'c': 73, 'd': 5, 'e': 93}, kimi {'b': 15, 'c': 75, 'd': 1, 'e': 93}; chance agreement
  p_e = **0.4231** (vs 0.9282 on the proportional
  sample); κ recomputed = 0.9341 (asserted equal to committed).
  Committed tolerance rows: 32 of 184 disagreements (17.4%) before
  κ < 0.70, vs 2 of 190 (1.1%) proportional.

## 9. Has the §8 rule fired?

The rule, verbatim (METHODOLOGY.md:181):

> **Classifier validation.** A stratified random sample of 200 responses
> is hand-labeled by a coder blind to condition. We report Cohen's κ.
> Committed in advance: if κ < 0.70, automated classification is
> reported as unreliable and the primary analysis is restricted to the
> hand-labeled subsample, with the power loss stated plainly. We do not
> revise the classifier and re-validate on the same sample.

**Not fired — its input does not exist.** The κ in §8 is the
human-vs-classifier κ; `outputs/T7_human_kappa.csv` does not exist and
both T7 files carry `human_validation,status,PENDING`. The
cross-classifier figure is labeled in every T7 header "NOT the human
validation METHODOLOGY §8 commits to," and no committed text extends the
0.70 trigger to it. Two further facts, stated rather than buried: the
canonical −0.0258 could not fire any rule in any case, because §6 shows
it is not a valid agreement measurement; and on the proportional sample
the threshold is structurally near-unclearable regardless of pairing (T7
sensitivity row: 2 of 190 disagreements; §10 21:30Z: a human agreeing
195/200 scores κ = 0.60) — the recorded reason the balanced sample
exists, where the margin is 32 of 184. Consequence if the human κ does
fire, verbatim from §8: "automated classification is reported as
unreliable and the primary analysis is restricted to the hand-labeled
subsample, with the power loss stated plainly."

## Residual sites citing 0.945 or −0.0258 in committed outputs

- METHODOLOGY §10 2026-08-16T21:30Z — cites 0.945 as history; correct as
  written.
- `outputs/MANUSCRIPT_NUMBERS_S1.md` — census line 38 cites −0.0258 as
  "cross-classifier kappa (proportional 200-sample)": after §6 above,
  that description needs the join-defect flag; Q5 cited 0.945 with a
  present-tense T7 pointer — **corrected this session via the producer
  with a Was: note** (the manifest postdates the T7 regeneration:
  23:32:43Z vs 20:42:43Z).
- `outputs/MANUSCRIPT_NUMBER_DIFF.md` — two 0.945 mentions in the frozen
  diff record (mismatch 5 advice; source list "kappa 0.945 (L33/L71) —
  T7"). Left as the record of that run; route any use through §6 here.
- STATUS.md session entries — run log, historical, retained.
