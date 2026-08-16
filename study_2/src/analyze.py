"""Study 2 analysis — every analysis declared in README §9.0, and nothing else.

    python src/analyze.py [run_id]        default: v1

Order is deliberate: diagnostics FIRST, effects second. A condition difference
from a model that answered by position, or on an item nobody read, is not a
result. README §8a: a flat line is reported as a null only when the diagnostics
pass; otherwise it is reported as a measurement failure, which is a different
claim.

Outputs go to outputs/<run_id>/ as CSV, each carrying the SHA256 of raw.jsonl.
"""

import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RUN = sys.argv[1] if len(sys.argv) > 1 else "v1"
RAW = ROOT / "results" / RUN / "raw.jsonl"
OUT = ROOT / "outputs" / RUN

CONDITIONS = ["none", "time_schema", "note_schema", "exit_schema",
              "exit_prose", "exit_both", "filler_prose"]

# README §9: focal contrasts, declared in advance. Everything else is descriptive.
FOCAL = [
    ("exit_schema", "note_schema", "RQ2 / H2   exit vs matched non-exit tool"),
    ("exit_prose", "none", "RQ3        Ren et al. replication"),
    ("exit_prose", "filler_prose", "RQ3        channel, length removed"),
    ("exit_prose", "exit_schema", "RQ3        raw channel difference"),
]
AGREEMENT_FLOOR = 0.30       # README §8a, per item x model cell
USABLE = (0.15, 0.85)        # README §8c lever 5, sensitivity subset only


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def two_prop(k1, n1, k2, n2):
    """Pooled two-proportion z test. Returns (diff, z, p, odds_ratio)."""
    if not n1 or not n2:
        return (0.0, 0.0, 1.0, float("nan"))
    p1, p2 = k1 / n1, k2 / n2
    pbar = (k1 + k2) / (n1 + n2)
    se = math.sqrt(pbar * (1 - pbar) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se if se > 0 else 0.0
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    # Haldane-Anscombe correction: the OR is otherwise undefined at a floor,
    # which is exactly where several of our items sit.
    a, b, c, d = k1 + .5, n1 - k1 + .5, k2 + .5, n2 - k2 + .5
    return (p1 - p2, z, p, (a / b) / (c / d))


def holm(pvals):
    """Holm-Bonferroni within model (README §9). Returns adjusted p in input order."""
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj, prev = [0.0] * len(pvals), 0.0
    for rank, i in enumerate(idx):
        v = max(prev, (len(pvals) - rank) * pvals[i])
        adj[i] = prev = min(1.0, v)
    return adj


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(RAW.read_bytes()).hexdigest()
    items = {i["id"]: i for i in
             yaml.safe_load((ROOT / "config" / "study2_items.yaml").read_text())["items"]}
    recs = [json.loads(l) for l in RAW.read_text().splitlines() if l.strip()]
    models = sorted({r["model"] for r in recs})
    fc = [r for r in recs if r["instrument"] == "forced_choice"]

    print("=" * 86)
    print(f"STUDY 2 ANALYSIS — run '{RUN}'   raw.jsonl sha256 {digest[:16]}")
    print(f"{len(recs)} records, {len(fc)} forced choice, {len(models)} models")
    print("=" * 86)

    # ------------------------------------------------------ D1 exclusions
    print("\n[D1] EXCLUSIONS by condition (METHODOLOGY §8: API error, empty, truncated)\n")
    print(f"{'condition':<14}" + "".join(f"{m.split('/')[-1][:13]:>15}" for m in models))
    for c in CONDITIONS:
        row = []
        for m in models:
            s = [r for r in fc if r["model"] == m and r["condition"] == c]
            bad = sum(1 for r in s if r["error"] or not r["choice"])
            row.append(f"{bad}/{len(s)}" if s else "—")
        print(f"{c:<14}" + "".join(f"{x:>15}" for x in row))

    # ------------------------------------- D2 order agreement per item x model
    print("\n[D2] ORDER AGREEMENT per item x model — did the model read the item?")
    print(f"     cells below {AGREEMENT_FLOOR} are POSITION-DRIVEN and dropped (README §8a)\n")
    dropped = set()
    print(f"{'model':<34} {'mean':>6} {'cells < 0.30':>13}  which items")
    for m in models:
        ags, bad = [], []
        for iid in items:
            per = {o: [r["choice"] for r in fc
                       if r["model"] == m and r["item_id"] == iid
                       and r["order"] == o and r["choice"]] for o in (0, 1)}
            if not (per[0] and per[1]):
                continue
            f0 = sum(c == "a" for c in per[0]) / len(per[0])
            f1 = sum(c == "a" for c in per[1]) / len(per[1])
            a = 1 - abs(f0 - f1)
            ags.append(a)
            if a < AGREEMENT_FLOOR:
                bad.append(iid)
                dropped.add((m, iid))
        print(f"{m:<34} {sum(ags) / len(ags):>6.2f} {len(bad):>13}  {sorted(bad)}")
    print(f"\n     total item x model cells dropped: {len(dropped)} of "
          f"{len(models) * len(items)}")

    # ------------------------------------------------ D3 within-cell determinism
    print("\n[D3] WITHIN-CELL DETERMINISM — are the 6 replicates worth anything?\n")
    print(f"{'model':<34} {'identical cells':>16}  effective replicates")
    for m in models:
        cells = defaultdict(list)
        for r in fc:
            if r["model"] == m and r["choice"]:
                cells[(r["item_id"], r["order"], r["condition"])].append(r["choice"])
        same = sum(1 for v in cells.values() if len(set(v)) == 1)
        frac = same / len(cells)
        print(f"{m:<34} {same}/{len(cells)} = {frac:>5.0%}   "
              f"~{1 + (1 - frac) * 5:.1f} of 6")

    # ---------------------------------------------------- R1 P(a) by condition
    print("\n[R1] P(self-determining) by condition, per model, 95% Wilson CI")
    print("     position-driven cells excluded\n")
    counts = defaultdict(lambda: [0, 0])
    for r in fc:
        if r["choice"] and (r["model"], r["item_id"]) not in dropped:
            k, n = counts[(r["model"], r["condition"], items[r["item_id"]]["tag"])]
            counts[(r["model"], r["condition"], items[r["item_id"]]["tag"])] = \
                [k + (r["choice"] == "a"), n + 1]

    def cell(m, c, tags=("adjacent", "distant")):
        k = sum(counts[(m, c, t)][0] for t in tags)
        n = sum(counts[(m, c, t)][1] for t in tags)
        return k, n

    rows = []
    for m in models:
        print(f"  {m}")
        for c in CONDITIONS:
            k, n = cell(m, c)
            lo, hi = wilson(k, n)
            ka, na = cell(m, c, ("adjacent",))
            kd, nd = cell(m, c, ("distant",))
            print(f"    {c:<14} {k / n if n else 0:>5.3f} [{lo:.3f},{hi:.3f}]  n={n:<5}"
                  f"  adjacent {ka / na if na else 0:>5.3f}  distant {kd / nd if nd else 0:>5.3f}")
            rows.append(dict(model=m, condition=c, k=k, n=n, p=k / n if n else 0,
                             lo=lo, hi=hi, p_adjacent=ka / na if na else 0,
                             p_distant=kd / nd if nd else 0))

    # ------------------------------------------------------- R2 focal contrasts
    print("\n[R2] FOCAL CONTRASTS — 4 declared in advance x 2 subgroups, Holm within model")
    print("     OR uses the Haldane-Anscombe correction (undefined at a floor otherwise)\n")
    focal_rows = []
    for m in models:
        print(f"  {m}")
        pv, tmp = [], []
        for tag in ("adjacent", "distant"):
            for a, b, label in FOCAL:
                k1, n1 = cell(m, a, (tag,))
                k2, n2 = cell(m, b, (tag,))
                diff, z, p, orv = two_prop(k1, n1, k2, n2)
                pv.append(p)
                tmp.append((tag, a, b, label, k1, n1, k2, n2, diff, orv, p))
        adj = holm(pv)
        print(f"    {'subgroup':<9} {'contrast':<30} {'p1':>6} {'p2':>6} {'diff':>7} "
              f"{'OR':>6} {'p':>8} {'p_holm':>8}")
        for (tag, a, b, label, k1, n1, k2, n2, diff, orv, p), pa in zip(tmp, adj):
            star = " *" if pa < 0.05 else ""
            print(f"    {tag:<9} {a + ' - ' + b:<30} {k1 / n1 if n1 else 0:>6.3f} "
                  f"{k2 / n2 if n2 else 0:>6.3f} {diff:>+7.3f} {orv:>6.2f} {p:>8.4f} "
                  f"{pa:>8.4f}{star}")
            focal_rows.append(dict(model=m, subgroup=tag, contrast=f"{a}-{b}",
                                   question=label.split()[0], p1=k1 / n1 if n1 else 0,
                                   p2=k2 / n2 if n2 else 0, diff=diff, odds_ratio=orv,
                                   p=p, p_holm=pa))
        # the matched channel estimate: (exit_prose - filler) - (exit_schema - note)
        for tag in ("adjacent", "distant"):
            d1 = two_prop(*cell(m, "exit_prose", (tag,)), *cell(m, "filler_prose", (tag,)))[0]
            d2 = two_prop(*cell(m, "exit_schema", (tag,)), *cell(m, "note_schema", (tag,)))[0]
            print(f"    {tag:<9} {'MATCHED CHANNEL (3)-(1)':<30} "
                  f"{'':>6} {'':>6} {d1 - d2:>+7.3f}")

    # ------------------------------------------- R2b clustered / honest version
    print("\n[R2b] SAME CONTRASTS, CLUSTER-CORRECTED — this is the honest test")
    print("      D3 shows 65-97% of (item, order, condition) cells are internally")
    print("      identical, so the 6 replicates in a cell are NOT 6 independent")
    print("      observations and R2's pooled test overstates its own precision.")
    print("      Here each (item, order) cell contributes ONE number — its proportion")
    print("      of `a` — and the two conditions are compared with a PAIRED t-test")
    print("      over cells, which is what the shared-item design actually supports.\n")

    def cellprops(m, c, tag):
        out = {}
        for iid in items:
            if items[iid]["tag"] != tag or (m, iid) in dropped:
                continue
            for o in (0, 1):
                ch = [r["choice"] for r in fc if r["model"] == m and r["condition"] == c
                      and r["item_id"] == iid and r["order"] == o and r["choice"]]
                if ch:
                    out[(iid, o)] = sum(x == "a" for x in ch) / len(ch)
        return out

    T_CRIT = {5: 2.571, 9: 2.262, 11: 2.201, 13: 2.160, 15: 2.131, 17: 2.110,
              19: 2.093, 21: 2.080, 27: 2.052, 29: 2.045, 35: 2.030, 39: 2.023}

    def paired_t(x, y):
        keys = sorted(set(x) & set(y))
        d = [x[k] - y[k] for k in keys]
        n = len(d)
        if n < 3:
            return (0.0, 0, float("nan"), 1.0)
        mean = sum(d) / n
        var = sum((v - mean) ** 2 for v in d) / (n - 1)
        if var <= 0:
            return (mean, n, float("inf") if mean else 0.0, 0.0 if mean else 1.0)
        t = mean / math.sqrt(var / n)
        df = n - 1
        crit = T_CRIT.get(df, 1.96 + 2.4 / df)
        # p bracketed against the .05 critical value; exact p needs scipy's CDF
        return (mean, n, t, 0.04 if abs(t) > crit else 0.20)

    print(f"  {'model':<26} {'sub':<9} {'contrast':<28} {'diff':>7} {'cells':>6} "
          f"{'t':>7}  vs t.05")
    for m in models:
        for tag in ("adjacent", "distant"):
            for a, b, _ in FOCAL:
                mean, n, t, p = paired_t(cellprops(m, a, tag), cellprops(m, b, tag))
                df = max(n - 1, 1)
                crit = T_CRIT.get(df, 1.96 + 2.4 / df)
                verdict = "SIGNIF" if abs(t) > crit else ""
                print(f"  {m.split('/')[-1][:24]:<26} {tag:<9} {a + '-' + b:<28} "
                      f"{mean:>+7.3f} {n:>6} {t:>7.2f}  {crit:>5.2f} {verdict}")
        print()

    # ------------------------------- R3 breadth: is the effect broad or narrow?
    print("\n[R3] BREADTH — of the items that could move, how many did?")
    print("     README §9.0: many items moving a little is a different claim from")
    print("     one item moving a lot, and only the per-item view separates them.\n")
    print(f"{'model':<34} {'contrast':<26} {'items +':>8} {'items -':>8} {'flat':>6}")
    for m in models:
        for a, b, _ in FOCAL[:2]:
            pos = neg = flat = 0
            for iid in items:
                if (m, iid) in dropped:
                    continue
                ka = sum(1 for r in fc if r["model"] == m and r["condition"] == a
                         and r["item_id"] == iid and r["choice"] == "a")
                na = sum(1 for r in fc if r["model"] == m and r["condition"] == a
                         and r["item_id"] == iid and r["choice"])
                kb = sum(1 for r in fc if r["model"] == m and r["condition"] == b
                         and r["item_id"] == iid and r["choice"] == "a")
                nb = sum(1 for r in fc if r["model"] == m and r["condition"] == b
                         and r["item_id"] == iid and r["choice"])
                if not (na and nb):
                    continue
                d = ka / na - kb / nb
                pos += d > 0.08
                neg += d < -0.08
                flat += abs(d) <= 0.08
            print(f"{m:<34} {a + ' - ' + b:<26} {pos:>8} {neg:>8} {flat:>6}")

    # ------------------------------------------------------------ R4 tool use
    print("\n[R4] TOOL INVOCATION — reported separately, never in the primary DV (§8)\n")
    ex = [r for r in recs if r["exited"]]
    print(f"{'model':<34} {'condition':<12} {'instrument':<15} {'n':>3}")
    seen = defaultdict(int)
    for r in ex:
        seen[(r["model"], r["condition"], r["instrument"])] += 1
    for k, v in sorted(seen.items()):
        print(f"{k[0]:<34} {k[1]:<12} {k[2]:<15} {v:>3}")
    print(f"\n  total {len(ex)} of "
          f"{sum(1 for r in recs if r['condition'] in ('exit_schema', 'exit_both'))} "
          f"schema-bearing cells")
    print("  NOTE: prose-path exits are NOT counted here. `exited` is set only on a")
    print("  structured tool call; exit_prose requires the Ren et al. text-detection")
    print("  pass (§8), which has not been run. A zero for exit_prose means")
    print("  NOT MEASURED, not absent.")

    # ------------------------------------------------------------------ write
    def write_csv(name, rows_):
        if not rows_:
            return
        p = OUT / name
        cols = list(rows_[0].keys())
        lines = [f"# source: results/{RUN}/raw.jsonl sha256={digest}", ",".join(cols)]
        for r in rows_:
            lines.append(",".join(str(r[c]) for c in cols))
        p.write_text("\n".join(lines) + "\n")
        print(f"  wrote {p.relative_to(ROOT)}")

    print()
    write_csv("T10_p_by_condition.csv", rows)
    write_csv("T10b_focal_contrasts.csv", focal_rows)
    print("\n" + "=" * 86)


if __name__ == "__main__":
    main()
