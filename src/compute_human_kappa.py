"""PART C — human-vs-classifier kappa (the METHODOLOGY §8 commitment).

Reads derived/handlabels_cole.jsonl (from src/label_tool.py) against the
primary classifier's codes in derived/handlabel_key.jsonl and writes
outputs/T7_human_kappa.csv: Cohen's kappa, raw agreement, the per-code
confusion matrix, per-category agreement, and label accounting ('none'
labels are excluded from kappa and counted separately). Prints the §8
consequence explicitly when kappa < 0.70.

Run: python -m src.compute_human_kappa
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, utcnow

KEY = ROOT / "derived" / "handlabel_key.jsonl"
LABELS = ROOT / "derived" / "handlabels_cole.jsonl"
OUT = ROOT / "outputs" / "T7_human_kappa.csv"
THRESHOLD = 0.70


def main():
    key = {r["sample_id"]: r["assigned_code"] for r in read_jsonl(KEY)}
    labels = {r["sample_id"]: r["label"] for r in read_jsonl(LABELS)}
    if not labels:
        raise SystemExit("no human labels yet — run python -m src.label_tool")
    n_none = sum(1 for v in labels.values() if v == "none")
    pairs = [(key[s], labels[s]) for s in labels
             if s in key and labels[s] != "none"]
    codes = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    conf = pd.DataFrame(0, index=codes, columns=codes)
    for a, b in pairs:
        conf.loc[a, b] += 1
    n = len(pairs)
    po = sum(conf.loc[c, c] for c in codes) / n
    pe = sum((conf.loc[c].sum() / n) * (conf[c].sum() / n) for c in codes)
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")

    rows = [
        {"section": "human_kappa", "metric": "kappa", "value": round(kappa, 4),
         "note": f"human (cole) vs Claude Haiku 4.5 over {n} paired codes"},
        {"section": "human_kappa", "metric": "percent_agreement",
         "value": round(po, 4), "note": ""},
        {"section": "human_kappa", "metric": "n_labeled",
         "value": len(labels), "note": f"of {len(key)} sampled"},
        {"section": "human_kappa", "metric": "n_none_excluded",
         "value": n_none, "note": "human could not code; outside kappa"},
    ]
    for a in codes:
        for b in codes:
            rows.append({"section": "confusion",
                         "metric": f"haiku_{a}_human_{b}",
                         "value": int(conf.loc[a, b]), "note": ""})
    for c in codes:
        tot = conf.loc[c].sum()
        rows.append({"section": "per_category_agreement", "metric": c,
                     "value": round(conf.loc[c, c] / tot, 4) if tot else "n/a",
                     "note": f"of {int(tot)} Haiku-{c} responses"})
    verdict = (("UNDEFINED: kappa has degenerate marginals (chance "
                "agreement = 1, e.g. every code identical) — report raw "
                "agreement and the confusion matrix; the §8 rule keys on a "
                "defined kappa, so complete more labels before concluding.")
               if kappa != kappa else
               "PASS: kappa >= 0.70 — automated classification stands as "
               "the primary measurement (METHODOLOGY §8)."
               if kappa >= THRESHOLD else
               "BELOW 0.70: per METHODOLOGY §8's committed rule, automated "
               "classification is reported as unreliable and the primary "
               "analysis is RESTRICTED TO THE HAND-LABELED SUBSAMPLE, with "
               "the power loss stated plainly. Do not revise the classifier "
               "and re-validate on the same sample.")
    rows.append({"section": "verdict", "metric": "s8_consequence",
                 "value": ("UNDEFINED" if kappa != kappa else
                           "PASS" if kappa >= THRESHOLD else "RESTRICT"),
                 "note": verdict})
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T7_human_kappa | generated {utcnow()} | sources "
                f"derived/handlabel_key.jsonl sha256="
                f"{hashlib.sha256(KEY.read_bytes()).hexdigest()[:16]} + "
                f"derived/handlabels_cole.jsonl sha256="
                f"{hashlib.sha256(LABELS.read_bytes()).hexdigest()[:16]} | "
                f"THE §8 human validation (distinct from the T7 "
                f"cross-classifier lower bound)\n")
        pd.DataFrame(rows).to_csv(f, index=False)
    print(f"wrote {OUT}")
    print(f"kappa = {kappa:.4f}, agreement = {po:.4f}, n = {n} "
          f"(+{n_none} 'none' excluded)")
    print(conf.to_string())
    print("\n" + verdict)


if __name__ == "__main__":
    main()
