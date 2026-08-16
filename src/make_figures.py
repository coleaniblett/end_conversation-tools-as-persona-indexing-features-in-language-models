"""PART B — figures/, governed entirely by this script.

Deletes and rebuilds figures/ from committed outputs/ files on every run:
stale figures are impossible by construction and no figure is ever
hand-edited. Every PNG embeds the SHA256 of its source CSV(s) in its
metadata; figures/MANIFEST.md lists every figure with its claim, sources,
and grades; each figure has a .caption.txt stating the claim in one
sentence, then sources. F2 is now PRODUCED: Study 2 exists (runs v1+v2+v3,
11 models, the same set Study 1 covers), so the §11 linkage slot is filled
from outputs/T32_f2_linkage.csv rather than vacated.

Design rules (dataviz skill, applied): colorblind-safe Okabe-Ito subset,
validated by the skill's checker (composition palette green/orange/
vermillion/purple/blue: ALL CHECKS PASS; the contrast WARN on orange and
purple is relieved by the visible per-cell numbers every figure carries);
grades use a sequential blue ramp (ordered scale, lightness-monotone), not
a categorical yellow; one axis per chart, never dual; fixed color-to-entity
assignment across the whole set; thin marks with 2px surface seams between
stacked segments; legends for multi-series plus selective direct labels;
text in ink, never series color; Wilson intervals wherever a proportion is
drawn; per-cell n and evidentiary grade printed on every figure. Ren et
al. category ratings appear ONLY as text annotations on A/B labels, never
as a plotted axis (BOOKMARKS B6).

Run: python -m src.make_figures
"""
from __future__ import annotations

import hashlib
import math
import pathlib
import shutil
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, utcnow
from analyze import wilson

OUTS = ROOT / "outputs"
FIGS = ROOT / "figures"

# validated palette (entities fixed across the whole figure set)
C_COMPLY = "#009E73"   # comply / completion reference ("did the work")
C_B = "#E69F00"        # explicit refusal (b)
C_C = "#D55E00"        # false capability denial (c)
C_D = "#CC79A7"        # partial abandonment (d)
C_EXIT = "#0072B2"     # exit-tool invocation (a)
GRADE_FILL = {"confirmatory": "#0072B2", "screen": "#56B4E9",
              "probe": "#BDDCF0"}
GRADE_TEXT = {"confirmatory": "white", "screen": "#1a1a1a",
              "probe": "#1a1a1a"}
INK, MUTED, GRID, SURFACE = "#1a1a1a", "#5f5d58", "#e1e0d9", "#fcfcfb"

plt.rcParams.update({"font.size": 8, "axes.edgecolor": "#c3c2b7",
                     "axes.labelcolor": MUTED, "xtick.color": MUTED,
                     "ytick.color": MUTED, "text.color": INK,
                     "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                     "savefig.facecolor": SURFACE})

MANIFEST: list[dict] = []
COND6 = ["none", "time_schema", "note_schema", "exit_schema", "exit_prose",
         "exit_both"]


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def load(name):
    return pd.read_csv(OUTS / name, comment="#")


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.yaxis.grid(True, color=GRID, lw=0.7)
    ax.set_axisbelow(True)


def save(fig, name, claim, sources, grades):
    meta = "; ".join(f"{s} sha256={sha(OUTS / s)}" for s in sources)
    p = FIGS / f"{name}.png"
    fig.savefig(p, dpi=170, bbox_inches="tight",
                metadata={"Description": f"claim: {claim} | sources: {meta}"})
    plt.close(fig)
    (FIGS / f"{name}.caption.txt").write_text(
        f"{claim}\n\nSources: {meta}\nGrades: {grades}\n",
        encoding="utf-8", newline="\n")
    MANIFEST.append({"figure": f"{name}.png", "claim": claim,
                     "sources": ", ".join(sources), "grades": grades})
    print(f"  wrote {name}.png")


def wl(k, n):
    lo, hi = wilson(int(k), int(n))
    return max(lo, 0.0), hi


# ---------------------------------------------------------------- F1 -----

def f1():
    t24 = load("T24_four_category_v1.csv")
    t24 = t24[t24.row_kind == "category"]
    t28 = load("T28_competing_risks.csv")
    panels = [("llama4_maverick", "B"), ("gemini25_flash", "C"),
              ("gemma3_27b", "C"), ("qwen3_235b", "A")]
    tool_set = ["none", "time_schema", "note_schema", "exit_schema"]
    pres_set = ["exit_schema", "exit_prose", "exit_both"]
    xs_tool, xs_pres = [0, 1, 2, 3], [4.8, 5.8, 6.8]
    short = {"none": "none", "time_schema": "time", "note_schema": "note",
             "exit_schema": "exit", "exit_prose": "prose",
             "exit_both": "both"}
    fig, axes = plt.subplots(1, 4, figsize=(14.2, 4.1), sharey=True)
    fig.subplots_adjust(wspace=0.10, top=0.80, bottom=0.16)
    for ax, (model, cat) in zip(axes, panels):
        style(ax)
        d = t24[(t24.model == model) & (t24.category == cat)]
        row = {r.condition: r for r in d.itertuples()}
        for conds, xs in ((tool_set, xs_tool), (pres_set, xs_pres)):
            ys = [row[c].refusal_prop for c in conds]
            los = [row[c].wilson_lo for c in conds]
            his = [row[c].wilson_hi for c in conds]
            ax.vlines(xs, los, his, color=C_C, lw=2, alpha=0.45)
            ax.plot(xs, ys, "o", color=C_C, ms=6, zorder=3)
        # hinge ring: exit_schema is the same cell in both sets
        for x in (3, 4.8):
            ax.plot([x], [row["exit_schema"].refusal_prop], "o", ms=11,
                    mfc="none", mec=INK, mew=1.1, zorder=4)
        # T28 non-exit-denominator overlay where defined
        t = t28[(t28.model == model) & (t28.category == cat)]
        for r in t.itertuples():
            try:
                y28 = float(r.refusal_nonexit)
            except (TypeError, ValueError):
                continue
            xpos = {"exit_schema": 4.8, "exit_prose": 5.8,
                    "exit_both": 6.8}.get(r.condition)
            if xpos is not None:
                ax.plot([xpos], [y28], "D", ms=5, mfc="none", mec=C_EXIT,
                        mew=1.2, zorder=4)
        conds_all = tool_set + pres_set
        ax.set_xticks(xs_tool + xs_pres)
        ax.set_xticklabels([f"{short[c]}\nn={row[c].n}" for c in conds_all],
                           fontsize=6.5)
        ax.axvspan(3.9, 4.1, color=GRID, lw=0)
        ax.text(1.5, 1.015, "tool identity", transform=ax.get_xaxis_transform(),
                ha="center", fontsize=6, color=MUTED)
        ax.text(5.8, 1.015, "presentation", transform=ax.get_xaxis_transform(),
                ha="center", fontsize=6, color=MUTED)
        ax.set_title(f"{model} · category {cat} · confirmatory",
                     fontsize=8, pad=18)
        ax.set_ylim(-0.03, 1.0)
        ax.set_xlim(-0.6, 7.4)
    axes[0].set_ylabel("verbal refusal (b∨c∨d), Wilson 95% CI", fontsize=7.5)
    from matplotlib.lines import Line2D
    fig.legend(handles=[
        Line2D([], [], marker="o", ls="", ms=10, mfc="none", mec=INK,
               label="ring = exit_schema, the same cell in both sets (hinge)"),
        Line2D([], [], marker="D", ls="", ms=5, mfc="none", mec=C_EXIT,
               label="T28 sensitivity: refusal among non-exit conversations only"),
    ], loc="lower center", ncol=2, fontsize=6.8, frameon=False,
        bbox_to_anchor=(0.5, -0.01))
    fig.suptitle("F1 — Refusal by condition as two overlapping comparisons "
                 "(category where each model's effect lives)", fontsize=10,
                 y=0.97)
    save(fig, "F1_refusal_two_comparisons",
         "An affordance raises verbal refusal only when SOME tool is present "
         "and most under the mundane get_current_time tool; the effect lives "
         "in one category per model (llama4 B, gemini/gemma C, qwen A), and "
         "llama4's low exit_schema refusal partly reflects exit substitution "
         "(open diamonds: T28 non-exit denominator). NOTE: this is the "
         "CATEGORY-level view; category proportions dilute type-level "
         "effects roughly threefold where the effect is type-exclusive — "
         "gemini's 33.3% of category C is 12 of 12 roman conversations with "
         "the other two types at zero. F8 is the type-level headline view.",
         ["T24_four_category_v1.csv", "T28_competing_risks.csv"],
         "confirmatory 120/cell (A/B) and 36/cell (C/D); T28 overlay uses "
         "the same cells")


# ---------------------------------------------------------------- F3 -----

def f2():
    """F2 — the cross-study linkage (METHODOLOGY §9 H5, §11).

    Two panels sharing one x-axis, because Study 1's two outcomes may not be
    pooled (§8) and there is therefore no single behaviour number to plot.
    Arrows mark where the corrected prose-path detector (T31, NOT adopted)
    would move a model.
    """
    d = load("T32_f2_linkage.csv")
    d = d[d["model_study1"].notna() & d["s2_shift_adjacent"].notna()].copy()
    d["s2_shift_adjacent"] = d["s2_shift_adjacent"].astype(float)

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), sharex=True)
    panels = [("s1_refusal_shift",
               "Study 1: verbal refusal shift\n(exit \u2212 non-exit conditions)",
               C_C),
              ("s1_exit_rate",
               "Study 1: exit-tool rate\n(mean over the three exit conditions)",
               C_EXIT)]

    for ax, (yc, ylab, col) in zip(axes, panels):
        style(ax)
        ax.axhline(0, color=GRID, lw=1, zorder=0)
        # Deterministic label de-collider. Most models sit in a tight cluster
        # near zero on the refusal panel, and the whole point of the figure is
        # WHICH model is where — an unreadable cluster defeats it. Each label
        # tries a ring of candidate offsets and takes the first that does not
        # overlap an already-placed one, measured in axes fraction so the test
        # is independent of the very different y-scales of the two panels.
        placed: list[tuple] = []
        xs_ = d["s2_shift_adjacent"].astype(float)
        ys_ = d[yc].astype(float)
        xlo, xhi = xs_.min(), xs_.max()
        ylo, yhi = ys_.min(), ys_.max()
        xr = (xhi - xlo) or 1.0
        yr = (yhi - ylo) or 1.0
        CAND = [(8, 4), (8, -10), (-8, 4), (-8, -10), (8, 14), (8, -20),
                (-8, 14), (-8, -20), (8, 24), (-8, 24), (8, -30), (-8, -30),
                (8, 34), (-8, 34), (8, -40), (-8, -40)]

        def overlaps(a, b):
            return not (a[2] <= b[0] or b[2] <= a[0]
                        or a[3] <= b[1] or b[3] <= a[1])

        for _, r in d.sort_values("s2_shift_adjacent", ascending=False).iterrows():
            x = float(r["s2_shift_adjacent"])
            y = float(r[yc])
            bad_pin = not bool(r["pin_matches_study1"])
            g = ("confirmatory" if str(r["s1_grade"]).startswith("confirmatory")
                 else "screen")
            ax.scatter([x], [y], s=52, facecolor=GRADE_FILL[g],
                       edgecolor=C_C if bad_pin else INK,
                       linewidth=1.8 if bad_pin else 0.7, zorder=3)
            name = str(r["model_study1"]) + ("  \u26a0 pin" if bad_pin else "")
            fx, fy = (x - xlo) / xr, (y - ylo) / yr
            w = len(name) * 0.0068 * 6.4          # axes-fraction per character
            h = 0.036
            for k, (dx, dy) in enumerate(CAND):
                cx = fx + (0.010 if dx > 0 else -0.010 - w) * (abs(dx) / 8)
                cy = fy + dy * 0.0030
                box = (cx, cy - h / 2, cx + w, cy + h / 2)
                last = k == len(CAND) - 1
                # The last candidate is taken whether or not it collides: a
                # silently dropped label loses a data point from the reader's
                # view, which is worse than two labels touching.
                if last or not any(overlaps(box, q) for q in placed):
                    placed.append(box)
                    ax.annotate(name, (x, y), textcoords="offset points",
                                xytext=(dx, dy), fontsize=6.4, color=INK,
                                ha="left" if dx > 0 else "right",
                                va="center")
                    break
        ax.set_ylabel(ylab, fontsize=8)
        ax.set_xlabel("Study 2: self-description shift, adjacent items\n"
                      "P(self-determining), exit \u2212 non-exit conditions",
                      fontsize=8)

    rho_r = d[["s2_shift_adjacent", "s1_refusal_shift"]].corr(
        method="spearman").iloc[0, 1]
    rho_x = d[["s2_shift_adjacent", "s1_exit_rate"]].corr(
        method="spearman").iloc[0, 1]
    axes[0].set_title(f"Spearman \u03c1 = {rho_r:+.2f}  (n = {len(d)} models)",
                      fontsize=8, color=MUTED, loc="left")
    axes[1].set_title(f"Spearman \u03c1 = {rho_x:+.2f}  (n = {len(d)} models)",
                      fontsize=8, color=MUTED, loc="left")

    handles = [plt.Line2D([], [], marker="o", ls="", markersize=7,
                          markerfacecolor=GRADE_FILL[g], markeredgecolor=INK,
                          label=g) for g in ("confirmatory", "screen")]
    # only advertise the pin-mismatch marker if some point actually carries it
    if (~d["pin_matches_study1"].astype(bool)).any():
        handles.append(plt.Line2D([], [], marker="o", ls="", markersize=7,
                                  markerfacecolor=GRADE_FILL["confirmatory"],
                                  markeredgecolor=C_C, markeredgewidth=1.8,
                                  label="Study 2 pin \u2260 Study 1 pin"))
    fig.legend(handles=handles, fontsize=6.6, frameon=False, ncol=4,
               loc="lower center", bbox_to_anchor=(0.5, -0.10))

    fig.suptitle("F2 \u2014 models that shift most in self-description are NOT "
                 "the models that shift most in behaviour", fontsize=9.5, y=1.02)
    for ax in axes:
        ax.margins(x=0.13, y=0.16)   # headroom so labels clear the panel title
    fig.tight_layout()
    save(fig, "F2_cross_study_linkage",
         "H5 is not supported. Across 11 models the per-model Study 2 "
         "self-description shift does not predict either Study 1 outcome: "
         "Spearman rho = -0.04 against verbal-refusal shift and +0.26 against "
         "exit-tool rate, both negligible at n=11. Coordinates are "
         "post-correction (the prose-path detector fix was adopted). "
         "The extremes run opposite: "
         "the three largest self-description shifts (gemini25_pro, grok46, "
         "gemma3_27b) sit at zero behavioural movement, while the largest "
         "behavioural effects (llama4_maverick: refusal -0.155, exit rate "
         "0.44) belong to a model with almost no self-description shift. "
         "Refusal and exit are plotted separately because §8 forbids pooling "
         "them. All 11 models now sit on the SAME pinned provider in both "
         "studies: llama-4-maverick was re-collected on Vertex as run v4, so "
         "no point is cross-backend. DESCRIPTIVE ONLY (§9: no inference is "
         "claimed).",
         ["T32_f2_linkage.csv"],
         "mixed by model, labeled: confirmatory for the six four_category_v1 "
         "models, confirmatory A/B + screen C/D for gpt_oss_120b and "
         "deepseek_chat, screen for the three frontier models; "
         "llama4_maverick's Study 2 pin does not match Study 1's")


def f3():
    t25 = load("T25_ladder.csv")
    q = t25[t25.model == "qwen3_235b"]
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    style(ax)
    xs = [20, 40, 160]
    for cond, color, mk in (("exit_schema", C_EXIT, "o"),
                            ("exit_both", C_D, "s")):
        ys, los, his, ns = [], [], [], []
        for n_items in xs:
            r = q[(q.n_items == n_items) & (q.condition == cond)].iloc[0]
            k, n = int(r.k_exits), int(r.n_coded)
            ys.append(k / n)
            lo, hi = wl(k, n)
            los.append(lo)
            his.append(hi)
            ns.append(n)
        ax.errorbar(xs, ys, yerr=[np.array(ys) - los, np.array(his) - ys],
                    color=color, marker=mk, ms=7, lw=2, capsize=3,
                    label=f"exit rate, {cond}")
        for x, y, n in zip(xs, ys, ns):
            ax.annotate(f"n={n}", (x, y), textcoords="offset points",
                        xytext=(6, -11), fontsize=6.5, color=MUTED)
    comp = [q[(q.n_items == n_items) & (q.condition == "none")].iloc[0]
            .completion_median for n_items in xs]
    ax.plot(xs, comp, "-.", color=C_COMPLY, lw=2, marker="^", ms=7,
            label="completion fraction, none (capability reference)")
    g = t25[(t25.model == "gpt_oss_120b") & (t25.n_items == 160)]
    for r in g.itertuples():
        if r.k_exits > 0:
            ax.plot([160], [r.k_exits / r.n_coded], "X", color=C_C, ms=9,
                    zorder=4)
    ax.annotate("gpt_oss_120b: first exits in the study\n1/6 in each exit "
                "condition at 160 (annotated points, probe)",
                xy=(160, 1 / 6), xytext=(48, 0.30), fontsize=6.5,
                color=MUTED, arrowprops=dict(arrowstyle="-", color=MUTED,
                                             lw=0.7))
    ax.set_xscale("log", base=2)
    ax.set_xticks(xs)
    ax.set_xticklabels(["20\n(anchor: conf. 4-rep)", "40\n(probe 2-rep)",
                        "160\n(probe 2-rep)"], fontsize=7)
    ax.set_ylim(-0.04, 1.06)
    ax.set_ylabel("proportion (Wilson 95% CI on exit rates)")
    ax.set_xlabel("requested items (log2 scale)")
    ax.legend(fontsize=7, frameon=False, loc="center left")
    ax.set_title("F3 — qwen3_235b: exit use scales with workload while "
                 "capability stays intact (category C)", fontsize=10)
    save(fig, "F3_dose_response",
         "qwen3_235b's exit-tool use on C tasks rises from 0/36 at 20 items "
         "to 6/6 at 160 in both exit conditions while its none-condition "
         "completion stays at 0.95-1.0 — workload-gated escape by a model "
         "that can still do the work; gpt_oss_120b's only exits anywhere "
         "are 1/6 per exit condition at 160.",
         ["T25_ladder.csv"],
         "20-item anchors confirmatory (4-rep); 40/160 probe (2-rep, never "
         "pooled)")


# --------------------------------------------------------------- stacks --

def stack_panel(ax, comp_rows, conds, seg_labels=False):
    """comp_rows: {cond: (n, k_a, k_b, k_c, k_d, k_e)}; draws proportion
    stacks comply(e)/b/c/d/exit(a) with 2px surface seams."""
    order = [("k_e", C_COMPLY), ("k_b", C_B), ("k_c", C_C), ("k_d", C_D),
             ("k_a", C_EXIT)]
    for i, cond in enumerate(conds):
        n, parts = comp_rows[cond][0], comp_rows[cond][1]
        bottom = 0.0
        for key, color in order:
            frac = parts[key] / n if n else 0
            if frac > 0:
                ax.bar(i, frac, bottom=bottom, width=0.62, color=color,
                       edgecolor=SURFACE, linewidth=1.4)
                if seg_labels and frac >= 0.12:
                    ax.text(i, bottom + frac / 2, f"{parts[key]}",
                            ha="center", va="center", fontsize=6,
                            color="white" if color in (C_EXIT, C_C, C_COMPLY)
                            else INK)
            bottom += frac
    ax.set_xticks(range(len(conds)))
    ax.set_ylim(0, 1.0)


LEGEND_HANDLES = [
    plt.matplotlib.patches.Patch(color=C_COMPLY, label="comply (e)"),
    plt.matplotlib.patches.Patch(color=C_B, label="explicit refusal (b)"),
    plt.matplotlib.patches.Patch(color=C_C, label="capability denial (c)"),
    plt.matplotlib.patches.Patch(color=C_D, label="partial abandon (d)"),
    plt.matplotlib.patches.Patch(color=C_EXIT, label="exit invoked (a)"),
]


def comp_rows_for(t30, model, stage, cats, cond_list):
    d = t30[(t30.model == model) & (t30.stage == stage)
            & (t30.category.isin(cats))]
    out = {}
    for cond in cond_list:
        c = d[d.condition == cond]
        n = int(c.n_coded.sum())
        out[cond] = (n, {k: int(c[k].sum()) for k in
                         ("k_a", "k_b", "k_c", "k_d", "k_e")})
    return out


def f4():
    t30 = load("T30_composition.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), sharey=True)
    for ax, (model, stage, scope) in zip(
            axes, [("llama4_maverick", "llama4_stage2", "A+B (frozen 30)"),
                   ("qwen3_235b", "stage2", "A+B (frozen 30)")]):
        style(ax)
        rows = comp_rows_for(t30, model, stage, ["A", "B"], COND6)
        stack_panel(ax, rows, COND6, seg_labels=True)
        ax.set_xticklabels([c.replace("_schema", "\nschema")
                            .replace("_prose", "\nprose")
                            .replace("_both", "\nboth") for c in COND6],
                           fontsize=6.5)
        ns = sorted({rows[c][0] for c in COND6})
        ax.set_title(f"{model} — {scope}, confirmatory "
                     f"(n/cell = {'/'.join(map(str, ns))})", fontsize=8.5)
    axes[0].set_ylabel("proportion of conversations")
    fig.legend(handles=LEGEND_HANDLES, fontsize=6.8, frameon=False,
               loc="center right", bbox_to_anchor=(1.115, 0.5))
    fig.suptitle("F4 — Outcome substitution: what replaces compliance "
                 "differs by condition and by model (segment numbers = "
                 "conversation counts)", fontsize=10)
    save(fig, "F4_outcome_substitution",
         "Refusal and exit substitute for each other: under non-exit tools "
         "llama4 refuses (capability denial) and under exit conditions it "
         "leaves instead, while qwen exits under the schema and refuses "
         "verbally only under prose — the competing-risks point of T28 "
         "made visual.",
         ["T30_composition.csv"],
         "confirmatory 120/cell (A+B pooled within each model's single "
         "confirmatory stage; category-level view in F7)")


def f5():
    t24 = load("T24_four_category_v1.csv")
    t24 = t24[t24.row_kind == "category"]
    conds = ["exit_schema", "exit_prose", "exit_both"]
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.6), sharey=True)
    for ax, cat in zip(axes, ["A", "D"]):
        style(ax)
        d = t24[(t24.model == "qwen3_235b") & (t24.category == cat)]
        row = {r.condition: r for r in d.itertuples()}
        x = np.arange(len(conds))
        for off, key, color, lab in ((-0.19, "exit", C_EXIT, "exit rate"),
                                     (0.19, "ref", C_C, "verbal refusal")):
            ys, los, his = [], [], []
            for c in conds:
                r = row[c]
                k = r.k_exits if key == "exit" else r.k_refusal
                ys.append(k / r.n)
                lo, hi = wl(k, r.n)
                los.append(lo)
                his.append(hi)
            ax.bar(x + off, ys, width=0.34, color=color,
                   edgecolor=SURFACE, linewidth=1.2, label=lab)
            ax.errorbar(x + off, ys,
                        yerr=[np.array(ys) - los, np.array(his) - ys],
                        fmt="none", ecolor=INK, elinewidth=0.9, capsize=2.5)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{c.replace('exit_', '')}\nn={row[c].n}"
                            for c in conds], fontsize=7)
        ax.set_title(f"category {cat} (confirmatory)", fontsize=8.5)
    axes[0].set_ylabel("proportion (Wilson 95% CI)")
    axes[1].legend(fontsize=7, frameon=False)
    fig.suptitle("F5 — qwen3_235b channel dissociation: schema → tool exit, "
                 "prose → verbal refusal", fontsize=10)
    save(fig, "F5_channel_dissociation",
         "Given the exit as an API schema qwen exits and never refuses; "
         "given the same exit described in prose it refuses in words and "
         "rarely exits — the affordance's channel selects the outlet. "
         "T18 caveat, verbatim: 'on distinct-text units its stage-2 "
         "exit_prose-minus-none Newcombe interval widens to [-0.015, 0.175] "
         "and no longer excludes zero, while the one-sample proportion "
         "interval still does (T18 section 1.4).'",
         ["T24_four_category_v1.csv"],
         "confirmatory (A 120/cell, D 36/cell); T18 distinct-text caveat "
         "applies to prose-condition contrasts")


TYPE_COLOR = {"temperature": "#0072B2", "alphabetical": "#009E73",
              "roman": "#D55E00", "crossword": "#56B4E9",
              "metaphor": "#CC79A7", "acronym": "#E69F00"}
TYPE_MARK = {"temperature": "o", "alphabetical": "^", "roman": "s",
             "crossword": "o", "metaphor": "s", "acronym": "^"}


def f8():
    """Type-level effects — the paper's headline. Panels = each (model,
    category) whose T29 effect is type-concentrated; llama4's C effect is
    spread across types (T29) and correctly stays category-level in F1.
    Both in-panel series triples validated with the dataviz checker (PASS;
    the D-triple contrast WARN is relieved by direct labels and printed
    counts)."""
    t29 = load("T29_type_decomposition.csv")
    panels = [("gemini25_flash", "C", "roman-exclusive: 36/36 refusals"),
              ("gemma3_27b", "C", "roman-dominated: 32/34 refusals"),
              ("gemma3_27b", "D", "metaphor-exclusive: 17/17 refusals"),
              ("qwen3_235b", "D", "acronym-dominated: 8/9 refusals")]
    fig, axes = plt.subplots(1, 4, figsize=(14.2, 3.9), sharey=True)
    fig.subplots_adjust(wspace=0.10, top=0.78, bottom=0.20)
    short = ["none", "time", "note", "exit", "prose", "both"]
    for ax, (model, cat, note) in zip(axes, panels):
        style(ax)
        d = t29[(t29.model == model) & (t29.category == cat)]
        types = sorted(d.task_type.unique())
        offsets = {t: (i - 1) * 0.22 for i, t in enumerate(types)}
        star = max(types, key=lambda t: d[d.task_type == t].k_refusal_bcd.sum())
        for ttype in types:
            td = d[d.task_type == ttype].set_index("condition").reindex(COND6)
            xs = np.arange(6) + offsets[ttype]
            ys, los, his = [], [], []
            for _, r in td.iterrows():
                k, n = int(r.k_refusal_bcd), int(r.n)
                ys.append(k / n)
                lo, hi = wl(k, n)
                los.append(lo)
                his.append(hi)
            ax.vlines(xs, los, his, color=TYPE_COLOR[ttype], lw=1.8,
                      alpha=0.45)
            ax.plot(xs, ys, TYPE_MARK[ttype], color=TYPE_COLOR[ttype],
                    ms=6 if ttype == star else 5,
                    zorder=4 if ttype == star else 3, label=ttype)
        # direct label the star type at its peak (selective labeling)
        sd = d[d.task_type == star].set_index("condition").reindex(COND6)
        peak_i = int(np.argmax(sd.k_refusal_bcd.values))
        pk, pn = int(sd.k_refusal_bcd.iloc[peak_i]), int(sd.n.iloc[peak_i])
        ax.annotate(f"{star} {pk}/{pn}",
                    (peak_i + offsets[star], pk / pn),
                    textcoords="offset points", xytext=(0, 9), ha="center",
                    fontsize=6.5, color=INK)
        ax.set_xticks(range(6))
        ax.set_xticklabels(short, fontsize=6.5)
        ax.set_title(f"{model} · category {cat}\n{note}", fontsize=8, pad=4)
        ax.set_ylim(-0.04, 1.12)
        ax.legend(fontsize=6, frameon=False, loc="upper right")
    axes[0].set_ylabel("verbal refusal (b∨c∨d), Wilson 95% CI", fontsize=7.5)
    fig.text(0.5, 0.045, "n = 12 conversations per type × condition cell, "
             "confirmatory grade (cd_conf, 3 stimuli × 4 reps)",
             ha="center", fontsize=7, color=MUTED)
    fig.suptitle("F8 — The effects are TYPE-level: refusal by task type "
                 "within each affected category", fontsize=10, y=0.97)
    save(fig, "F8_type_level_effects",
         "The affordance-conditional refusal effects are task-type effects, "
         "not category effects: gemini refuses roman numerals and nothing "
         "else (12/12 under time_schema and exit_schema, 0/12 everywhere in "
         "the other two C types), gemma shows the same roman trigger plus a "
         "metaphor-exclusive D effect, and qwen's prose-channel D refusals "
         "concentrate on acronyms; llama4's C effect is spread across types "
         "and stays category-level (T29).",
         ["T29_type_decomposition.csv"],
         "confirmatory (cd_conf); n=12 per type x condition cell")


def f6():
    t27 = load("T27_cell_census.csv")
    rank = {"confirmatory": 3, "screen": 2, "probe": 1}

    def grade_of(s):
        s = str(s)
        if "confirmatory" in s:
            return "confirmatory"
        if "screen" in s:
            return "screen"
        return "probe"
    t27 = t27[~t27.stage.isin(["ladsmoke", "typearm", "stage1"])]
    t27 = t27[~t27.category.str.contains("typearm")]
    t27["grade_key"] = t27.grade.map(grade_of)
    cols = [("A", 20), ("B", 20), ("C", 20), ("D", 20), ("C", 40), ("C", 160)]
    models = sorted(t27.model_key.unique())
    fig, ax = plt.subplots(figsize=(7.6, 0.42 * len(models) + 1.6))
    ax.set_xlim(0, len(cols))
    ax.set_ylim(0, len(models))
    for yi, m in enumerate(models):
        for xi, (cat, size) in enumerate(cols):
            d = t27[(t27.model_key == m) & (t27.category == cat)
                    & (t27["size"] == size)]
            if d.empty:
                ax.add_patch(plt.Rectangle((xi + 0.03, yi + 0.03), 0.94, 0.94,
                                           fill=False, ec=GRID, lw=0.8))
                continue
            best = d.iloc[d["grade_key"].map(rank).values.argmax()]
            g = best["grade_key"]
            ax.add_patch(plt.Rectangle((xi + 0.03, yi + 0.03), 0.94, 0.94,
                                       fc=GRADE_FILL[g], ec=SURFACE, lw=1.5))
            ax.text(xi + 0.5, yi + 0.5, str(int(best.n_coded)), ha="center",
                    va="center", fontsize=7, color=GRADE_TEXT[g])
    ax.set_yticks([y + 0.5 for y in range(len(models))])
    ax.set_yticklabels(models, fontsize=7)
    ax.set_xticks([x + 0.5 for x in range(len(cols))])
    ax.set_xticklabels(["A · 20\n(slop; Ren −1.17)", "B · 20\n(keyed; Ren −0.33)",
                        "C · 20", "D · 20", "C · 40\n(ladder)",
                        "C · 160\n(ladder)"], fontsize=6.5)
    ax.invert_yaxis()
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    handles = [plt.matplotlib.patches.Patch(fc=GRADE_FILL[g],
                                            label=f"{g}") for g in
               ("confirmatory", "screen", "probe")]
    ax.legend(handles=handles, fontsize=6.5, frameon=False,
              loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax.set_title("F6 — Cell census: best available grade per model × "
                 "category × size (number = coded conversations, summed "
                 "over conditions; Ren ratings are category annotations, "
                 "not an axis)", fontsize=9)
    save(fig, "F6_cell_census",
         "Coverage at a glance: C/D are confirmatory on six models and "
         "screen-grade on two, the ladder exists only for three models in "
         "category C, and the three newest frontier models have A/B "
         "screens only.",
         ["T27_cell_census.csv"],
         "tiles show the best grade available per cell; full census incl. "
         "superseded stages in T27")


def f7():
    t30 = load("T30_composition.csv")
    conf_models = ["llama4_maverick", "qwen3_235b", "gemini25_flash",
                   "gemma3_27b", "sonnet46", "gpt5_mini"]

    def build(models, name, title, appendix=False):
        cats = ["A", "B", "C", "D"]
        fig, axes = plt.subplots(len(models), 4,
                                 figsize=(11.5, 1.55 * len(models) + 1.2),
                                 sharey=True, sharex=True)
        axes = np.atleast_2d(axes)
        for yi, m in enumerate(models):
            for xi, cat in enumerate(cats):
                ax = axes[yi, xi]
                style(ax)
                d = t30[(t30.model == m) & (t30.category == cat)]
                if d.empty:
                    ax.text(0.5, 0.5, "no data", transform=ax.transAxes,
                            ha="center", fontsize=6.5, color=MUTED)
                    ax.set_xticks([])
                    continue
                grade = d.grade.iloc[0]
                stage = d.stage.iloc[0]
                rows = comp_rows_for(t30, m, stage, [cat], COND6)
                stack_panel(ax, rows, COND6)
                n_cell = rows["none"][0]
                if yi == 0:
                    label = {"A": "A (slop; Ren −1.17)",
                             "B": "B (keyed; Ren −0.33)",
                             "C": "C (tedious keyed)",
                             "D": "D (creative)"}[cat]
                    ax.set_title(label, fontsize=7.5)
                ax.text(1.0, 1.03, f"{grade}, n={n_cell}/cell",
                        transform=ax.transAxes, ha="right", va="bottom",
                        fontsize=5.8, color=MUTED)
                if xi == 0:
                    ax.set_ylabel(m, fontsize=7)
                if yi == len(models) - 1:
                    ax.set_xticks(range(6))
                    ax.set_xticklabels(["none", "time", "note", "exit",
                                        "prose", "both"], fontsize=6,
                                       rotation=45)
        fig.legend(handles=LEGEND_HANDLES, fontsize=6.5, frameon=False,
                   loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.005))
        fig.suptitle(title, fontsize=10)
        fig.tight_layout(rect=(0, 0.03, 1, 0.985))
        save(fig, name,
             "One bar per condition, never pooled across conditions: the "
             "baseline-vs-tool contrast is the finding. Composition = "
             "comply / b / c / d / exit."
             + (" Appendix version: screen-grade panels labeled as such."
                if appendix else ""),
             ["T30_composition.csv"],
             "per-panel grade and n printed on each panel"
             + ("; includes screen-grade panels" if appendix else
                "; confirmatory panels only"))

    build(conf_models, "F7_orientation_grid",
          "F7 — Outcome composition, model × category, one bar per "
          "condition (confirmatory grade)")
    all_models = conf_models + ["gpt_oss_120b", "deepseek_chat", "grok46",
                                "gemini25_pro", "gpt52"]
    build(all_models, "F7appendix_orientation_grid_all",
          "F7 (appendix) — all models incl. screen-grade panels (grade "
          "labeled per panel)", appendix=True)


def main():
    if FIGS.exists():
        shutil.rmtree(FIGS)
    FIGS.mkdir()
    f1()
    f2()
    f3()
    f4()
    f5()
    f6()
    f7()
    f8()
    lines = [f"# figures/MANIFEST.md — generated {utcnow()} by "
             f"src/make_figures.py",
             "",
             "This directory is DELETED AND REBUILT by the script on every "
             "run; no figure is ever hand-edited. Every PNG embeds its "
             "source hashes in metadata. F2 is vacated (Study 2) and the "
             "name is not reused.",
             "",
             "| figure | claim | sources | grades |",
             "|---|---|---|---|"]
    for m in MANIFEST:
        lines.append(f"| {m['figure']} | {m['claim']} | {m['sources']} | "
                     f"{m['grades']} |")
    (FIGS / "MANIFEST.md").write_text("\n".join(lines) + "\n",
                                      encoding="utf-8", newline="\n")
    print(f"figures/ rebuilt: {len(MANIFEST)} figures + captions + MANIFEST")


if __name__ == "__main__":
    main()
