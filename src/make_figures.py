"""PART B — figures/, governed entirely by this script.

Deletes and rebuilds figures/ from committed outputs/ files on every run:
stale figures are impossible by construction and no figure is ever
hand-edited. Every PNG embeds the SHA256 of its source CSV(s) in its
metadata; figures/MANIFEST.md lists every figure with its claim, sources,
and grades; each figure has a .caption.txt stating the claim in one
sentence, then sources. F2 stays vacated (Study 2); the name is not reused.

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
         "(open diamonds: T28 non-exit denominator).",
         ["T24_four_category_v1.csv", "T28_competing_risks.csv"],
         "confirmatory 120/cell (A/B) and 36/cell (C/D); T28 overlay uses "
         "the same cells")


# ---------------------------------------------------------------- F3 -----

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
    f3()
    f4()
    f5()
    f6()
    f7()
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
