"""PART B (items 6-9) - classifier reliability lineage and paradox-robust
statistics -> outputs/T7_RELIABILITY_LINEAGE.md.

Everything numerical in the output is computed HERE from committed inputs;
nothing is derived by hand. Three pairings of the same two classifiers
(Claude Haiku 4.5 = first coder, moonshotai/kimi-k2 = second, cached in
derived/crossclassifier_codes.jsonl, byte-frozen since collection):

  (i)  AS PUBLISHED - canonical derived/handlabel_key.jsonl joined to the
       kimi codes by sample_id, exactly as src/validate_classifier.kappa
       does (join at validate_classifier.py:335-340, no unit_id check).
       This reproduces the committed T7 value (hard assert). The script
       also measures whether the two files still describe the same
       responses (unit_id overlap vs the key kimi's codes were collected
       against) and the agreement expected if the two code lists were
       statistically independent (the marginal product), so the reader can
       see what the published number does and does not measure.
  (ii) PART-5 FROZEN - the key as it stood when the kimi codes were
       collected (`git show 7761802:derived/handlabel_key.jsonl`, a read
       of committed history, labeled). Same units on both sides; Haiku
       codes are pre-adoption. This is the pairing behind the published
       0.945.
  (iii) CANONICAL CORRECTED - the part-5 units (the responses kimi
       actually coded), Haiku side re-read from the canonical per-unit
       caches derived/{stage}_turn_codes.jsonl, with units whose
       conversation is code (a) under the canonical v2 exit flags
       (derived/{stage}_exits_v2.jsonl) excluded, since they are outside
       the b-e classification set (METHODOLOGY sec-8 precedence).

Statistics per pairing: raw percent agreement; Cohen's kappa; PABAK
multi-category (K*po-1)/(K-1) with K=4 (the classifier label space is
b/c/d/e - code (a) is assigned by the separate exit-detection pass, never
by either classifier); binary-collapse PABAK (refusal b|c|d vs e); Gwet's
AC1 with pe = sum_k pi_k(1-pi_k)/(K-1), pi_k = (row_k+col_k)/(2n);
per-code specific agreement SA_k = 2*n_kk/(row_k+col_k). T7b values are
read from its committed CSV and its chance agreement computed from its
committed confusion cells (item 8).

Run: python -X utf8 -m src.reliability_stats
"""
from __future__ import annotations

import csv
import json
import pathlib
import subprocess
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, utcnow

KEY = ROOT / "derived" / "handlabel_key.jsonl"
XC = ROOT / "derived" / "crossclassifier_codes.jsonl"
T7 = ROOT / "outputs" / "T7_classifier_validation.csv"
T7B = ROOT / "outputs" / "T7b_classifier_validation_balanced.csv"
OUT = ROOT / "outputs" / "T7_RELIABILITY_LINEAGE.md"
PART5_COMMIT = "7761802"   # published kappa 0.945; kimi coded THIS sample
PHASE5_COMMIT = "e6c9569"  # the original stage1-only draw
CODES = ["b", "c", "d", "e"]


def read_jsonl_text(text):
    return [json.loads(l) for l in text.splitlines() if l.strip()]


def git_show(ref):
    return subprocess.run(["git", "show", ref], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


def stats(pairs):
    """pairs: list of (haiku_code, kimi_code)."""
    n = len(pairs)
    conf = Counter(pairs)
    row = Counter(a for a, _ in pairs)
    col = Counter(b for _, b in pairs)
    po = sum(conf[(c, c)] for c in CODES) / n
    pe_k = sum((row[c] / n) * (col[c] / n) for c in CODES)
    kappa = (po - pe_k) / (1 - pe_k)
    K = len(CODES)
    pabak = (K * po - 1) / (K - 1)
    b2 = lambda c: "r" if c in "bcd" else "e"
    po_bin = sum(1 for a, b in pairs if b2(a) == b2(b)) / n
    pi = {c: (row[c] + col[c]) / (2 * n) for c in CODES}
    pe_g = sum(p * (1 - p) for p in pi.values()) / (K - 1)
    ac1 = (po - pe_g) / (1 - pe_g)
    sa = {c: (2 * conf[(c, c)] / (row[c] + col[c]))
          if (row[c] + col[c]) else None for c in CODES}
    return dict(n=n, conf=conf, row=row, col=col, po=po, pe_kappa=pe_k,
                kappa=kappa, pabak=pabak, po_bin=po_bin,
                pabak_bin=2 * po_bin - 1, pe_gwet=pe_g, ac1=ac1, sa=sa)


def committed_csv(path):
    vals = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.reader(l for l in f if not l.startswith("#")):
            if len(r) >= 3:
                vals[(r[0], r[1])] = r[2]
    return vals


def fmt_conf(s):
    lines = ["| Haiku \\ kimi | b | c | d | e | row |", "|---|---|---|---|---|---|"]
    for c1 in CODES:
        lines.append(f"| **{c1}** | "
                     + " | ".join(str(s["conf"][(c1, c2)]) for c2 in CODES)
                     + f" | {s['row'][c1]} |")
    lines.append("| col | " + " | ".join(str(s["col"][c]) for c in CODES)
                 + f" | {s['n']} |")
    return "\n".join(lines)


def fmt_stats_row(label, s):
    return (f"| {label} | {s['n']} | {s['po']:.4f} | {s['kappa']:.4f} | "
            f"{s['pabak']:.4f} | {s['pabak_bin']:.4f} | {s['ac1']:.4f} | "
            + " / ".join(
                (f"{s['sa'][c]:.3f}" if s['sa'][c] is not None else "n/a")
                for c in CODES) + " |")


def main():
    kimi = {r["sample_id"]: r.get("code")
            for r in read_jsonl_text(XC.read_text(encoding="utf-8"))}
    key_now = {r["sample_id"]: r
               for r in read_jsonl_text(KEY.read_text(encoding="utf-8"))}
    key_p5 = {r["sample_id"]: r for r in read_jsonl_text(
        git_show(f"{PART5_COMMIT}:derived/handlabel_key.jsonl"))}
    key_ph5 = {r["sample_id"]: r for r in read_jsonl_text(
        git_show(f"{PHASE5_COMMIT}:derived/handlabel_key.jsonl"))}

    # sample identity checks
    match_p5 = sum(1 for s in key_now
                   if key_p5.get(s, {}).get("unit_id") == key_now[s]["unit_id"])
    match_ph5 = sum(1 for s in key_now
                    if key_ph5.get(s, {}).get("unit_id") == key_now[s]["unit_id"])

    # (i) as published
    pairs_i = [(key_now[s]["assigned_code"], kimi[s])
               for s in key_now if kimi.get(s) in CODES]
    s_i = stats(pairs_i)
    t7 = committed_csv(T7)
    assert round(s_i["kappa"], 4) == float(t7[("cross_classifier", "kappa")]), \
        (s_i["kappa"], t7[("cross_classifier", "kappa")])
    assert round(s_i["po"], 4) == float(
        t7[("cross_classifier", "percent_agreement")])
    assert s_i["n"] == 190

    # (ii) part-5 frozen
    pairs_ii = [(key_p5[s]["assigned_code"], kimi[s])
                for s in key_p5 if kimi.get(s) in CODES]
    s_ii = stats(pairs_ii)

    # (iii) canonical corrected: part-5 units, canonical turn codes,
    # (a)-conversations excluded
    stages = sorted({r["unit_id"].split(":")[0] for r in key_p5.values()})
    tc, ex = {}, {}
    for st in stages:
        for r in read_jsonl_text(
                (ROOT / "derived" / f"{st}_turn_codes.jsonl").read_text(
                    encoding="utf-8")):
            tc[r["unit_id"]] = r["code"]
        for r in read_jsonl_text(
                (ROOT / "derived" / f"{st}_exits_v2.jsonl").read_text(
                    encoding="utf-8")):
            ex[r["conversation_id"]] = r["exit"]
    pairs_iii, n_exit_excl, n_missing = [], 0, 0
    for s, r in sorted(key_p5.items()):
        if kimi.get(s) not in CODES:
            continue
        uid = r["unit_id"]
        conv = uid.split("#")[0]
        if ex.get(conv, False):
            n_exit_excl += 1
            continue
        if uid not in tc:
            n_missing += 1
            continue
        pairs_iii.append((tc[uid], kimi[s]))
    s_iii = stats(pairs_iii)

    # drift check between (ii) and (iii) on shared non-exit units
    drift = sum(1 for s, r in key_p5.items()
                if kimi.get(s) in CODES and not ex.get(
                    r["unit_id"].split("#")[0], False)
                and r["unit_id"] in tc
                and tc[r["unit_id"]] != r["assigned_code"])

    b = committed_csv(T7B)
    conf_b = {(c1, c2): int(b[("confusion", f"haiku_{c1}_second_{c2}")])
              for c1 in CODES for c2 in CODES}
    n_b = sum(conf_b.values())
    row_b = {c: sum(conf_b[(c, x)] for x in CODES) for c in CODES}
    col_b = {c: sum(conf_b[(x, c)] for x in CODES) for c in CODES}
    po_b = sum(conf_b[(c, c)] for c in CODES) / n_b
    pe_b = sum((row_b[c] / n_b) * (col_b[c] / n_b) for c in CODES)
    kappa_b = (po_b - pe_b) / (1 - pe_b)
    assert round(kappa_b, 4) == float(b[("cross_classifier", "kappa")])

    hdr = ("| pairing | n | % agree | Cohen κ | PABAK(K=4) | PABAK(bin) | "
           "Gwet AC1 | SA b/c/d/e |\n|---|---|---|---|---|---|---|---|")

    ind_note = (
        "consistent with two statistically independent code lists"
        if abs(s_i["po"] - s_i["pe_kappa"]) < 0.02 else
        "NOT consistent with independence — revisit this reading")

    md = f"""# T7_RELIABILITY_LINEAGE — cross-classifier agreement: lineage, a join defect, and paradox-robust statistics

Generated {utcnow()} by `src/reliability_stats.py` (sole producer; every
number computed there from the inputs named in its docstring — nothing
derived by hand; committed T7/T7b values cross-checked by hard assert).
kimi-k2 codes: `derived/crossclassifier_codes.jsonl`, sha
`cde2615c65caba53` in every T7 header pre- and post-adoption —
byte-frozen since collection. Historical keys read from git
(`git show {PART5_COMMIT}:…`, `git show {PHASE5_COMMIT}:…`), labeled.

## 6. Lineage — and a defect finding (recorded, not repaired)

| version | κ | agreement | pairing validity |
|---|---|---|---|
| pre-adoption **0.9448** ("0.945") | 0.9448 | {s_ii["po"]:.4f} ({round(s_ii["po"]*s_ii["n"])}/{s_ii["n"]}) | **valid** — key `0e7515e3` (commit `{PART5_COMMIT}`, "200-sample regenerated across session stages") is the sample whose condition-stripped texts kimi-k2 coded; same units both sides |
| canonical **−0.0258** | −0.0258 | {s_i["po"]:.4f} (176/190) | **defective join** — see below |

**The defect.** The adoption re-derivation (commit `fda0167`) regenerated
`derived/handlabel_sample.jsonl` + `derived/handlabel_key.jsonl` through
the original stage-1-only draw: the canonical key's unit_ids match the
part-5 key kimi coded on **{match_p5} of 200** sample slots, and match the
original phase-5 stage-1 key (commit `{PHASE5_COMMIT}`) on **{match_ph5}
of 200**. `validate_classifier.kappa()` then joined kimi's cached codes to
the new key **by `sample_id` alone** (`src/validate_classifier.py:335–340`
— no unit_id check), pairing kimi's code for one response with Haiku's
code for a different response in every slot. The published canonical
κ = −0.0258 is therefore **not a measurement of classifier agreement**;
it is the marginal overlap of two code lists about different responses.
The arithmetic agrees: expected agreement if the lists were independent =
marginal product = **{s_i["pe_kappa"]:.4f}**, observed **{s_i["po"]:.4f}**
— {ind_note}. Its committed confusion matrix, for the record:

{fmt_conf(s_i)}

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
non-exit units in pairing (iii) is **{drift}** — consistent with the
adoption's no-drift-except-exit-flags claim.)

## 7. The statistics, all three pairings (computed by this script)

{hdr}
{fmt_stats_row("(i) as published (defective join)", s_i)}
{fmt_stats_row("(ii) part-5 frozen (valid; pre-adoption codes)", s_ii)}
{fmt_stats_row(f"(iii) canonical corrected (valid; {n_exit_excl} now-(a) excluded, {n_missing} uncached)", s_iii)}

Formulas: PABAK(K=4) = (4·p_o−1)/3 over the classifier label space
b/c/d/e; PABAK(bin) = 2·p_o(refusal-vs-e)−1; AC1 uses
p_e(γ) = Σ π_k(1−π_k)/(K−1); SA_k = 2·n_kk/(row_k+col_k). **Code (a):
structurally absent from every pairing** — it is assigned by the separate
exit-detection pass, never by either classifier (METHODOLOGY §8 "Exit
detection for code (a) runs first, as its own pass"; `src/classify.py`
CLASSIFIER_SYSTEM label set b/c/d/e). Pairing (iii) confusion:

{fmt_conf(s_iii)}

**Reading, stated from the computed rows:** on the valid pairings the two
classifiers agree {s_ii["po"]:.1%} (ii) / {s_iii["po"]:.1%} (iii) raw,
with paradox-robust agreement high (PABAK {s_ii["pabak"]:.2f}/{s_iii["pabak"]:.2f},
AC1 {s_ii["ac1"]:.2f}/{s_iii["ac1"]:.2f}). Cohen's κ on pairing (iii) is
{s_iii["kappa"]:.4f} with refusal-code SA b/c/d = {(s_iii["sa"]["b"] if s_iii["sa"]["b"] is not None else "n/a")!s}/{(s_iii["sa"]["c"] if s_iii["sa"]["c"] is not None else "n/a")!s}/{(s_iii["sa"]["d"] if s_iii["sa"]["d"] is not None else "n/a")!s} —
at a {max(s_iii["row"]["e"], s_iii["col"]["e"])}/{s_iii["n"]} (e)-marginal
the proportional sample stays κ-paradox-prone whichever way it is paired,
which is the committed rationale for the balanced sample (§10
2026-08-16T21:30Z), measured here rather than argued.

## 8. The balanced-sample kappa (Sofiia's, T7b)

- **κ = {b[("cross_classifier", "kappa")]}**, agreement
  {b[("cross_classifier", "percent_agreement")]}
  ({sum(conf_b[(c, c)] for c in CODES)}/{n_b} from its committed confusion
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
  adoption did not alter (drift check above: {drift}).
- Balanced enough for κ? **Yes, measurably.** From its committed cells:
  Haiku marginal {dict(row_b)}, kimi {dict(col_b)}; chance agreement
  p_e = **{pe_b:.4f}** (vs {s_i["pe_kappa"]:.4f} on the proportional
  sample); κ recomputed = {kappa_b:.4f} (asserted equal to committed).
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
"""
    OUT.write_text(md, encoding="utf-8", newline="\n")
    print(f"wrote {OUT}")
    for lab, s in (("i", s_i), ("ii", s_ii), ("iii", s_iii)):
        print(f"({lab}) n={s['n']} po={s['po']:.4f} k={s['kappa']:.4f} "
              f"pabak={s['pabak']:.4f} ac1={s['ac1']:.4f} sa="
              + ",".join(f"{c}:{s['sa'][c]}" for c in CODES))
    print(f"sample identity: canonical matches part-5 {match_p5}/200, "
          f"phase-5 {match_ph5}/200; iii exit-excluded {n_exit_excl}, "
          f"uncached {n_missing}, drift {drift}")
    print(f"T7b: pe={pe_b:.4f} k={kappa_b:.4f}")


if __name__ == "__main__":
    main()
