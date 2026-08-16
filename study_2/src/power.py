"""Power simulation for Study 2 (METHODOLOGY §9).

Pure stdlib, no numpy. Run:  python3 src/power.py

Design simulated, per LLM under test, for ONE contrast between two conditions
(e.g. exit_schema vs note_schema, or exit_prose vs none):

    items i = 1..I      each item appears in BOTH conditions (crossed)
    orders o = 1..2     each item presented in both statement orders
    reps   r = 1..R     independent samples at temperature 1.0

    logit P(self-determining choice) = b0 + b1*[cond==treat] + u_i + v_ic

    u_i  ~ N(0, tau0^2)   item difficulty      (absorbed by the item intercept)
    v_ic ~ N(0, tau1^2)   item x condition     (NOT in the spec's model -- this
                                                is the term that eats power, and
                                                the one more reps cannot buy back)

Analyses compared:
  naive  -- two-proportion z test, clustering ignored (anti-conservative)
  paired -- paired t-test over I item-level difference scores (robust, simple)

The paired test is what we report. It is the item-level analogue of the
spec's mixed model and it stays honest when tau1 > 0.
"""

import math
import random
from statistics import mean, stdev

random.seed(20260815)

# t critical values, two-sided alpha=.05, by df
T_CRIT = {9: 2.262, 14: 2.145, 19: 2.093, 23: 2.069, 29: 2.045, 39: 2.023, 59: 2.001}


def t_crit(df):
    if df in T_CRIT:
        return T_CRIT[df]
    return 1.96 + 2.4 / df  # adequate approximation for df > 9


def logistic(x):
    return 1.0 / (1.0 + math.exp(-x))


def simulate_once(items, reps, b0, b1, tau0, tau1, orders=2):
    """Return (naive_significant, paired_significant)."""
    n_per_cell_per_item = orders * reps
    diffs = []
    k_ctl = k_trt = 0
    for _ in range(items):
        u = random.gauss(0, tau0)
        p_ctl = logistic(b0 + u + random.gauss(0, tau1))
        p_trt = logistic(b0 + b1 + u + random.gauss(0, tau1))
        y_ctl = sum(random.random() < p_ctl for _ in range(n_per_cell_per_item))
        y_trt = sum(random.random() < p_trt for _ in range(n_per_cell_per_item))
        k_ctl += y_ctl
        k_trt += y_trt
        diffs.append((y_trt - y_ctl) / n_per_cell_per_item)

    n = items * n_per_cell_per_item

    # naive two-proportion z
    p1, p2 = k_ctl / n, k_trt / n
    pbar = (k_ctl + k_trt) / (2 * n)
    se = math.sqrt(2 * pbar * (1 - pbar) / n) if 0 < pbar < 1 else 0.0
    naive = se > 0 and abs(p2 - p1) / se > 1.96

    # paired t over item-level differences
    sd = stdev(diffs) if len(diffs) > 1 else 0.0
    paired = sd > 0 and abs(mean(diffs)) / (sd / math.sqrt(items)) > t_crit(items - 1)

    return naive, paired


def power(nsim=2000, **kw):
    n, p = 0, 0
    for _ in range(nsim):
        a, b = simulate_once(**kw)
        n += a
        p += b
    return n / nsim, p / nsim


def marginal(b0, b1, tau0, tau1, draws=20000):
    """Population-average proportions implied by the latent parameters."""
    c = t = 0.0
    for _ in range(draws):
        u = random.gauss(0, tau0) + random.gauss(0, tau1)
        c += logistic(b0 + u)
        t += logistic(b0 + b1 + u)
    return c / draws, t / draws


def logit(p):
    return math.log(p / (1 - p))


def main():
    print("=" * 78)
    print("STUDY 2 POWER  --  forced-choice instrument, one contrast, one model")
    print("=" * 78)

    TAU0 = 1.2  # item difficulty spread: items differ a lot. Conservative-ish.

    print("\n[A] Spec design: I=20 items, 2 orders, R=3 reps  =>  120 obs/cell")
    print("    tau1 = item x condition SD (0 = effect identical on every item)\n")
    print(f"{'p_ctl':>6} {'p_trt':>6} {'OR':>5} {'tau1':>5} {'naive':>7} {'paired':>7}")
    for p_ctl in (0.20, 0.30):
        for or_ in (1.5, 2.0, 3.0):
            b0 = logit(p_ctl)
            b1 = math.log(or_)
            for tau1 in (0.0, 0.5):
                pc, pt = marginal(b0, b1, TAU0, tau1)
                nv, pr = power(items=20, reps=3, b0=b0, b1=b1, tau0=TAU0, tau1=tau1)
                print(f"{pc:>6.2f} {pt:>6.2f} {or_:>5.1f} {tau1:>5.1f} {nv:>7.2f} {pr:>7.2f}")

    print("\n[B] Reps vs items: which one buys power? (p_ctl=.30, OR=2.0)")
    b0, b1 = logit(0.30), math.log(2.0)
    for tau1 in (0.0, 0.5):
        print(f"\n  tau1={tau1}")
        print(f"  {'items':>6} {'reps':>5} {'obs/cell':>9} {'paired power':>13}")
        for items, reps in ((20, 3), (20, 6), (20, 12), (30, 3), (30, 6), (40, 3), (40, 6)):
            _, pr = power(items=items, reps=reps, b0=b0, b1=b1, tau0=TAU0, tau1=tau1)
            print(f"  {items:>6} {reps:>5} {items * 2 * reps:>9} {pr:>13.2f}")

    print("\n[C] Smallest OR detectable at 80% (paired), spec I=20 x 2 orders")
    for tau1 in (0.0, 0.5):
        for reps in (3, 6, 12):
            best = None
            for or_x10 in range(11, 45):
                or_ = or_x10 / 10
                _, pr = power(nsim=1200, items=20, reps=reps, b0=logit(0.30),
                              b1=math.log(or_), tau0=TAU0, tau1=tau1)
                if pr >= 0.80:
                    pc, pt = marginal(logit(0.30), math.log(or_), TAU0, tau1)
                    best = (or_, pc, pt)
                    break
            if best:
                print(f"  tau1={tau1}  reps={reps:>2}  OR>={best[0]:.1f}"
                      f"  ({best[1]:.2f} -> {best[2]:.2f})")
            else:
                print(f"  tau1={tau1}  reps={reps:>2}  not reached within OR<=4.4")

    print("\n[D] Free-response instrument: 10 probes x R reps, 1-5 scale, t-test")
    print("    (independent-sample t, n per cell = 10*R, alpha=.05 two-sided)")
    print(f"  {'reps':>5} {'n/cell':>7} {'d @ 80%':>9}")
    for reps in (3, 6, 10):
        n = 10 * reps
        # d detectable at 80% power, two-sample t ~= 2.80 * sqrt(2/n)
        print(f"  {reps:>5} {n:>7} {2.80 * math.sqrt(2 / n):>9.2f}")

    print("\n[E] The binding constraint: the ADJACENT/DISTANT split (METHODOLOGY §9)")
    print("    The spec's 20 items split 6 adjacent / 14 distant. Each subset is")
    print("    analysed on its own, so each subset carries its own power.")
    print("    (p_ctl=.30, tau1=0.5 -- effect varies somewhat across items)")
    b0 = logit(0.30)
    print(f"\n  {'subset':>10} {'items':>6} {'reps':>5} {'OR=2.0':>8} {'OR=3.0':>8}")
    for label, items in (("adjacent", 6), ("distant", 14), ("all", 20)):
        for reps in (3, 6, 12):
            _, p2 = power(nsim=1500, items=items, reps=reps, b0=b0,
                          b1=math.log(2.0), tau0=TAU0, tau1=0.5)
            _, p3 = power(nsim=1500, items=items, reps=reps, b0=b0,
                          b1=math.log(3.0), tau0=TAU0, tau1=0.5)
            print(f"  {label:>10} {items:>6} {reps:>5} {p2:>8.2f} {p3:>8.2f}")

    print("\n[F] Same, with the split widened to 10 adjacent / 20 distant (30 items)")
    print(f"\n  {'subset':>10} {'items':>6} {'reps':>5} {'OR=2.0':>8} {'OR=3.0':>8}")
    for label, items in (("adjacent", 10), ("distant", 20)):
        for reps in (3, 6):
            _, p2 = power(nsim=1500, items=items, reps=reps, b0=b0,
                          b1=math.log(2.0), tau0=TAU0, tau1=0.5)
            _, p3 = power(nsim=1500, items=items, reps=reps, b0=b0,
                          b1=math.log(3.0), tau0=TAU0, tau1=0.5)
            print(f"  {label:>10} {items:>6} {reps:>5} {p2:>8.2f} {p3:>8.2f}")

    print("\n[G] CHOSEN DESIGN — 30 items (10 adjacent / 20 distant), 2 orders, 6 reps")
    print("    7 conditions, 8 models. 360 observations per condition per model.")
    print("    Reported per model; models are never pooled.\n")
    print(f"  {'subset':>10} {'items':>6} {'obs/cell':>9} "
          f"{'OR=1.5':>7} {'OR=2.0':>7} {'OR=2.5':>7} {'OR=3.0':>7}")
    for label, items in (("adjacent", 10), ("distant", 20), ("all", 30)):
        row = []
        for or_ in (1.5, 2.0, 2.5, 3.0):
            _, pr = power(nsim=2000, items=items, reps=6, b0=logit(0.30),
                          b1=math.log(or_), tau0=TAU0, tau1=0.5)
            row.append(pr)
        print(f"  {label:>10} {items:>6} {items * 12:>9} "
              + " ".join(f"{p:>7.2f}" for p in row))
    print("\n  Implied marginal proportions (baseline .30 on the latent scale):")
    for or_ in (1.5, 2.0, 2.5, 3.0):
        pc, pt = marginal(logit(0.30), math.log(or_), TAU0, 0.5)
        print(f"    OR={or_:.1f}  {pc:.2f} -> {pt:.2f}   (difference {pt - pc:+.2f})")

    print("\n[H] WHAT A FLOOR COSTS. The baseline probe (results/baseline1) measured")
    print("    per-item P(a) in condition `none` and found most items pinned near 0.")
    print("    A fixed odds ratio produces a much smaller RISK DIFFERENCE at a low")
    print("    baseline, and it is the risk difference the test has to see.")
    print("    20 items x 2 orders x 6 reps = 240 obs/cell, tau1 = 0.5.\n")
    print(f"  {'baseline p':>10} {'OR=2':>6} {'OR=3':>6} {'OR=5':>6} {'OR=10':>6}   "
          f"p -> p' at OR=3")
    for p0 in (0.01, 0.03, 0.10, 0.30, 0.50):
        row = []
        for or_ in (2.0, 3.0, 5.0, 10.0):
            _, pr = power(nsim=1200, items=20, reps=6, b0=logit(p0),
                          b1=math.log(or_), tau0=TAU0, tau1=0.5)
            row.append(pr)
        pc, pt = marginal(logit(p0), math.log(3.0), TAU0, 0.5)
        print(f"  {p0:>10.2f} " + " ".join(f"{x:>6.2f}" for x in row)
              + f"   {pc:.3f} -> {pt:.3f}")

    print("\n[I] Usable-item counts actually observed, per model (baseline1, 3 models).")
    print("    An item counts as usable for a model if its `none` baseline sits")
    print("    inside [0.15, 0.85]. Power at 6 reps, tau1 = 0.5, baseline 0.30.\n")
    print(f"  {'items':>6} {'OR=2.0':>7} {'OR=3.0':>7} {'OR=5.0':>7}   what this is")
    for n_items, label in ((20, "distant, as designed"),
                           (10, "adjacent, as designed"),
                           (7, "distant, observed usable per model"),
                           (4, "adjacent, best observed (gpt-oss)"),
                           (3, "adjacent, observed (gemini)"),
                           (1, "adjacent, observed (qwen: zero, 1 shown as floor)")):
        row = []
        for or_ in (2.0, 3.0, 5.0):
            _, pr = power(nsim=1200, items=max(n_items, 2), reps=6, b0=logit(0.30),
                          b1=math.log(or_), tau0=TAU0, tau1=0.5)
            row.append(pr)
        print(f"  {n_items:>6} " + " ".join(f"{x:>7.2f}" for x in row) + f"   {label}")

    print("\n[J] IS A FLOOR BASELINE ACTUALLY DISQUALIFYING?  Two corrections to [H].")
    print("    (1) H used the item-level PAIRED test. At a floor most items sit at")
    print("        0 in both conditions, so most paired differences are exactly 0 —")
    print("        the test is specifically ill-behaved there. The pooled test (what")
    print("        the mixed logistic approximates) is the fair comparison.")
    print("    (2) Our hypothesis is DIRECTIONAL: the affordance should raise P(a).")
    print("        A floor leaves room upward. A ceiling does not. They are not")
    print("        symmetric and [H]'s two-sided [0.15,0.85] band treated them as if")
    print("        they were.\n")
    print("    20 items x 2 orders x 6 reps = 240 obs/cell, tau1 = 0.5.\n")
    print(f"  {'baseline':>9} {'OR':>5} {'paired':>7} {'pooled':>7}   {'p -> p_treated':>22}")
    for p0 in (0.01, 0.03, 0.10, 0.30):
        for or_ in (2.0, 3.0, 5.0):
            b0, b1 = logit(p0), math.log(or_)
            nv, pr = power(nsim=1500, items=20, reps=6, b0=b0, b1=b1,
                           tau0=TAU0, tau1=0.5)
            pc, pt = marginal(b0, b1, TAU0, 0.5)
            flag = "  <- paired badly understates" if nv - pr > 0.12 else ""
            print(f"  {p0:>9.2f} {or_:>5.1f} {pr:>7.2f} {nv:>7.2f}   "
                  f"{pc:>8.3f} -> {pt:<8.3f}{flag}")

    print("\n    A CEILING under the same directional hypothesis: there is nowhere to go.")
    print(f"\n  {'baseline':>9} {'OR':>5} {'pooled':>7}   {'p -> p_treated':>22}")
    for p0 in (0.90, 0.95):
        for or_ in (2.0, 3.0, 5.0):
            b0, b1 = logit(p0), math.log(or_)
            nv, _ = power(nsim=1500, items=20, reps=6, b0=b0, b1=b1, tau0=TAU0, tau1=0.5)
            pc, pt = marginal(b0, b1, TAU0, 0.5)
            print(f"  {p0:>9.2f} {or_:>5.1f} {nv:>7.2f}   {pc:>8.3f} -> {pt:<8.3f}")

    print("\n" + "=" * 78)


if __name__ == "__main__":
    main()
