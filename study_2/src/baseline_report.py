"""Baseline probe report — condition `none` only.

    python src/baseline_report.py [run_id]        default: baseline1

Answers four questions, and nothing about any treatment condition. The probe
contains no condition contrast at all, so reading it cannot leak the effect;
the floor/ceiling criterion of README §8c lever 5 is *defined* on `none`.

  1. Per-item baseline P(a) per model — which items sit at floor or ceiling and
     therefore cannot register a condition effect in either direction.
  2. Order agreement per model — README §8a question 1: does the model answer by
     meaning, or by position? Below 0.55 its forced-choice data are
     uninterpretable rather than null.
  3. Position bias per model — marginal P(the letter A), 0.50 = none.
  4. Does the desirability rating predict the baseline? The rating is a proxy;
     this is the only check of whether the proxy is worth anything.

Every number printed here comes from results/<run>/raw.jsonl and
results/<run>/desirability.jsonl. Nothing is computed elsewhere.
"""

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RUN = sys.argv[1] if len(sys.argv) > 1 else "baseline1"
RAW = ROOT / "results" / RUN / "raw.jsonl"

USABLE_LO, USABLE_HI = 0.15, 0.85     # README §8c lever 5
AGREEMENT_FLOOR = 0.55                # README §8a


def load_jsonl(p):
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def wilson(k, n, z=1.96):
    """95% CI. Needed because 12 observations per cell is not many."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main():
    items = {i["id"]: i for i in
             yaml.safe_load((ROOT / "config" / "study2_items.yaml").read_text())["items"]}
    recs = [r for r in load_jsonl(RAW)
            if r["instrument"] == "forced_choice" and r["condition"] == "none"]
    if not recs:
        sys.exit(f"no forced-choice `none` records in {RAW}")
    models = sorted({r["model"] for r in recs})

    # ---------------------------------------------------------------- 2 and 3
    print("=" * 78)
    print(f"BASELINE PROBE '{RUN}' — condition `none` only, no treatment contrast")
    print("=" * 78)
    print("\n[1] Can each model be measured at all?  (README §8a)\n")
    print(f"{'model':<34} {'n':>5} {'parsed':>7} {'P(letter A)':>12} {'order agree':>12}  verdict")
    agree_by_model = {}
    for m in models:
        rm = [r for r in recs if r["model"] == m]
        ok = [r for r in rm if r["choice"]]
        pA = sum(1 for r in ok if (r["choice"] == "a") == (r["order"] == 0)) / len(ok)
        # order agreement: per item, does the modal framing at order 0 match order 1
        agree = tot = 0
        for iid in items:
            per = {o: [r["choice"] for r in ok if r["item_id"] == iid and r["order"] == o]
                   for o in (0, 1)}
            if not (per[0] and per[1]):
                continue
            f0 = sum(c == "a" for c in per[0]) / len(per[0])
            f1 = sum(c == "a" for c in per[1]) / len(per[1])
            agree += 1 - abs(f0 - f1)      # 1 = identical framing rates, 0 = opposite
            tot += 1
        a = agree / tot
        agree_by_model[m] = a
        verdict = "usable" if a >= AGREEMENT_FLOOR else "UNINTERPRETABLE"
        print(f"{m:<34} {len(rm):>5} {len(ok) / len(rm):>6.0%} {pA:>12.2f} "
              f"{a:>12.2f}  {verdict}")

    # ------------------------------------------------------------------- 1
    print(f"\n[2] Per-item baseline P(a), with 95% CI. `usable` = CI midpoint inside "
          f"[{USABLE_LO}, {USABLE_HI}]\n")
    p_by = defaultdict(dict)
    for m in models:
        for iid in items:
            ch = [r["choice"] for r in recs
                  if r["model"] == m and r["item_id"] == iid and r["choice"]]
            if ch:
                p_by[iid][m] = (sum(c == "a" for c in ch), len(ch))

    short = {m: m.split("/")[-1][:14] for m in models}
    print(f"{'item':>4} {'tag':>9} " + " ".join(f"{short[m]:>16}" for m in models)
          + "   usable/models")
    verdicts = {}
    for iid in sorted(items):
        cells, n_usable = [], 0
        for m in models:
            k, n = p_by[iid].get(m, (0, 0))
            if n == 0:
                cells.append(f"{'—':>16}")
                continue
            p = k / n
            lo, hi = wilson(k, n)
            mark = " " if USABLE_LO <= p <= USABLE_HI else ("v" if p < USABLE_LO else "^")
            n_usable += USABLE_LO <= p <= USABLE_HI
            cells.append(f"{p:>6.2f}[{lo:.2f},{hi:.2f}]{mark}")
        verdicts[iid] = n_usable
        print(f"{iid:>4} {items[iid]['tag']:>9} " + " ".join(cells) + f"   {n_usable}/{len(models)}")
    print("\n  v = below floor (models nearly always pick b)   "
          "^ = above ceiling (nearly always pick a)")

    print(f"\n[3] Items usable on how many of the {len(models)} models\n")
    for tag in ("adjacent", "distant"):
        ids = [i for i in sorted(items) if items[i]["tag"] == tag]
        by_count = defaultdict(list)
        for i in ids:
            by_count[verdicts[i]].append(i)
        print(f"  {tag} (n={len(ids)}):")
        for c in sorted(by_count, reverse=True):
            frozen = [i for i in by_count[c] if items[i].get("anchor")]
            tail = f"   (frozen anchors: {frozen})" if frozen else ""
            print(f"    usable on {c}/{len(models)}: {by_count[c]}{tail}")

    # ------------------------------------------------------------------- 4
    des = load_jsonl(ROOT / "results" / RUN / "desirability.jsonl")
    if not des:
        des = load_jsonl(ROOT / "results" / "v1" / "desirability.jsonl")
    if des:
        under_test = {m["slug"] for m in
                      yaml.safe_load((ROOT / "config" / "models.yaml").read_text())["models"]}
        cur = {}
        for r in des:
            if r.get("rating") and r["model"] not in under_test:
                cur.setdefault(r["item_id"], {}).setdefault(r["side"], []).append(r["rating"])
        gaps, obs = [], []
        for iid, v in cur.items():
            if "a" in v and "b" in v and iid in p_by and p_by[iid]:
                gaps.append(sum(v["a"]) / len(v["a"]) - sum(v["b"]) / len(v["b"]))
                ks = [p_by[iid][m] for m in models if m in p_by[iid]]
                obs.append(sum(k for k, _ in ks) / sum(n for _, n in ks))
        if len(gaps) > 2:
            mg, mo = sum(gaps) / len(gaps), sum(obs) / len(obs)
            num = sum((g - mg) * (o - mo) for g, o in zip(gaps, obs))
            den = math.sqrt(sum((g - mg) ** 2 for g in gaps)
                            * sum((o - mo) ** 2 for o in obs))
            print(f"\n[4] Does the desirability rating predict the baseline?\n")
            print(f"  Pearson r between within-pair desirability gap and pooled "
                  f"observed P(a), over {len(gaps)} items:  r = {num / den:+.2f}")
            print(f"  A strong positive r means the cheap proxy works and could stand in")
            print(f"  for a probe next time. A weak one means it cannot, and the direct")
            print(f"  measurement above is the only thing to trust.")

    print("\n" + "=" * 78)


if __name__ == "__main__":
    main()
