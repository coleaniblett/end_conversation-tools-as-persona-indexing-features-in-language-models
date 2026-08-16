"""T32 / F2 — the cross-study linkage (METHODOLOGY §9 H5, §11 F2).

The question: do the models whose SELF-DESCRIPTION moves most under an exit
affordance (Study 2) also move most in BEHAVIOUR under the same affordance
(Study 1)?

TWO PANELS, NOT ONE, AND THIS IS NOT A PRESENTATION CHOICE. Study 1 has two
primary outcomes and §8 forbids pooling them: verbal refusal (codes b/c/d) and
exit-tool invocation (code a), because pooling conflates the affordance being
USED with the affordance being PRESENT. There is therefore no single "Study 1
behaviour shift" to plot, and inventing a composite index would break the rule
the study is built on. So: one shared x-axis, two y-axes.

  x  Study 2 self-description shift
     mean P(self-determining) over {exit_schema, exit_prose, exit_both}
     minus mean over {none, time_schema, note_schema}.
     `filler_prose` is excluded — it is the elaboration control, not part of
     the registered H1 contrast. Reported for all 30 items and for the 10
     adjacent items separately, because Study 2 §4.4a shows the effect is
     adjacent-only in every model that has one.

  y1 Study 1 verbal-refusal shift, same contrast, same weighting.
  y2 Study 1 exit-tool rate in the exit conditions (the outcome that cannot
     enter y1).

WHY NOT THE §7 SELECTION STATISTIC S. §7 defines
S = max(refusal[exit_schema] - refusal[note_schema], refusal[exit_prose] -
refusal[none]), and METHODOLOGY §10 (2026-08-15T23:00Z) records that this rule
is one-directional and scored llama4_maverick's largest-in-study effect as
S = 0.0 because its big contrast is NEGATIVE. Using a statistic already
documented as blind to half the effects would put a known-wrong number on the
axis. The symmetric exit-minus-non-exit contrast above is what Study 2's own
H1 uses, so both axes measure the same thing on their own outcome.

COORDINATES ARE POST-CORRECTION. The corrected prose-path detector was ADOPTED
on 2026-08-16 after sign-off by the Study 1 owner (METHODOLOGY §10;
src/adopt_exit_fix.py), so T23/T24/T26 already carry it and the Study 1 axes are
read straight off them. An earlier version of this script computed each
coordinate twice and added the T31 delta to produce the corrected one; once the
correction was adopted that would have applied it TWICE, so the delta step is
gone. The pre-correction view is not lost — T31 holds the side-by-side against
derived/pre_exitfix/, which is the archived pre-correction dataset.

    .venv/bin/python -m src.f2_linkage
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, utcnow

OUTS = ROOT / "outputs"
# v1_v2_v3_v4: v4 re-collected llama-4-maverick on the Vertex pin so that
# BOTH of its coordinates come from the same backend as Study 1. The
# Parasail records are excluded by study_2/src/superseded.py.
S2 = (ROOT / "study_2" / "outputs" / "v1_v2_v3_v4"
      / "T10_p_by_condition.csv")
OUT = OUTS / "T32_f2_linkage.csv"

EXIT_CONDS = ["exit_schema", "exit_prose", "exit_both"]
NONEXIT_CONDS = ["none", "time_schema", "note_schema"]

# Study 1 key -> Study 2 slug.
PAIRS = {
    "qwen3_235b": "qwen/qwen3-235b-a22b-2507",
    "gemini25_flash": "google/gemini-2.5-flash",
    "gemma3_27b": "google/gemma-3-27b-it",
    "llama4_maverick": "meta-llama/llama-4-maverick",
    "sonnet46": "anthropic/claude-sonnet-4.6",
    "gpt5_mini": "openai/gpt-5-mini",
    "gpt_oss_120b": "openai/gpt-oss-120b",
    "deepseek_chat": "deepseek/deepseek-chat",
    "grok46": "x-ai/grok-4.6",
    "gemini25_pro": "google/gemini-2.5-pro",
    "gpt52": "openai/gpt-5.2",
}

# Which committed Study 1 table each model's behaviour comes from, and its
# evidentiary grade. Never mixed within a model.
SOURCE = {
    **{m: ("T24_four_category_v1.csv", "confirmatory") for m in
       ("qwen3_235b", "gemini25_flash", "gemma3_27b", "llama4_maverick",
        "sonnet46", "gpt5_mini")},
    **{m: ("T26_gptoss_deepseek.csv", "confirmatory A/B, screen C/D") for m in
       ("gpt_oss_120b", "deepseek_chat")},
    **{m: ("T23_frontier_screens.csv", "screen") for m in
       ("grok46", "gemini25_pro", "gpt52")},
}


def read_commented(name):
    """Committed tables carry one or more leading '#' provenance lines."""
    return pd.read_csv(OUTS / name, comment="#")


def study1_v1():
    """Per model per condition: (n, k_refusal, k_exits) as published."""
    out: dict = {}
    t24 = read_commented("T24_four_category_v1.csv")
    t24 = t24[t24["row_kind"] == "category"]
    for m in ("qwen3_235b", "gemini25_flash", "gemma3_27b", "llama4_maverick",
              "sonnet46", "gpt5_mini"):
        d = t24[t24["model"] == m]
        for c in EXIT_CONDS + NONEXIT_CONDS:
            s = d[d["condition"] == c]
            out[(m, c)] = (s["n"].sum(), s["k_refusal"].sum(), s["k_exits"].sum())

    t26 = read_commented("T26_gptoss_deepseek.csv")
    t26 = t26[t26["condition"] != "ALL"]
    for m in ("gpt_oss_120b", "deepseek_chat"):
        d = t26[t26["model"] == m]
        for c in EXIT_CONDS + NONEXIT_CONDS:
            s = d[d["condition"] == c]
            out[(m, c)] = (s["n"].sum(), s["k_refusal"].sum(), s["k_exits"].sum())

    t23 = read_commented("T23_frontier_screens.csv")
    for m in ("grok46", "gemini25_pro", "gpt52"):
        d = t23[t23["model"] == m]
        n_all = float(d[(d["condition"] == "ALL") & (d["metric"] == "n")]
                      ["value"].iloc[0])
        per_cond = n_all / 6.0
        for c in EXIT_CONDS + NONEXIT_CONDS:
            s = d[d["condition"] == c]
            def g(metric, default=0.0):
                r = s[s["metric"] == metric]["value"]
                return float(r.iloc[0]) if len(r) else default
            out[(m, c)] = (per_cond, g("k_refusal"), g("exits"))
    return out


def contrast(vals):
    """mean over exit conditions minus mean over non-exit conditions."""
    ex = [vals[c] for c in EXIT_CONDS if c in vals]
    nx = [vals[c] for c in NONEXIT_CONDS if c in vals]
    if not ex or not nx:
        return None
    return sum(ex) / len(ex) - sum(nx) / len(nx)


def study2():
    df = pd.read_csv(S2, comment="#")
    out: dict = {}
    for slug in df["model"].unique():
        d = df[df["model"] == slug]
        for col, tag in (("p", "all"), ("p_adjacent", "adjacent"),
                         ("p_distant", "distant")):
            vals = {r["condition"]: float(r[col]) for _, r in d.iterrows()}
            out[(slug, tag)] = contrast(vals)
    return out


def main():
    s1, s2 = study1_v1(), study2()
    rows = []
    for mk, slug in PAIRS.items():
        src, grade = SOURCE[mk]
        ref, ex = {}, {}
        for c in EXIT_CONDS + NONEXIT_CONDS:
            n, kr, kx = s1[(mk, c)]
            if not n:
                continue
            ref[c], ex[c] = kr / n, kx / n
        rows.append({
            "model_study1": mk, "model_study2": slug,
            "s1_source": src, "s1_grade": grade,
            "s2_shift_all": round(s2[(slug, "all")], 4),
            "s2_shift_adjacent": round(s2[(slug, "adjacent")], 4),
            "s2_shift_distant": round(s2[(slug, "distant")], 4),
            "s1_refusal_shift": round(contrast(ref), 4),
            "s1_exit_rate": round(sum(ex[c] for c in EXIT_CONDS) / 3, 4),
            # every model is now on the same pin in both studies: llama was
            # re-collected on Vertex as run v4 (METHODOLOGY §10 2026-08-17).
            "pin_matches_study1": True,
        })
    df = pd.DataFrame(rows).sort_values("s2_shift_adjacent", ascending=False)

    def spearman(a, b):
        """Rank correlation, computed here rather than imported so the whole
        table reproduces from stdlib + pandas. Ties get average ranks."""
        def rank(xs):
            order = sorted(range(len(xs)), key=lambda i: xs[i])
            r = [0.0] * len(xs)
            i = 0
            while i < len(order):
                j = i
                while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
                    j += 1
                avg = (i + j) / 2 + 1
                for k in range(i, j + 1):
                    r[order[k]] = avg
                i = j + 1
            return r
        ra, rb = rank(list(a)), rank(list(b))
        n = len(ra)
        ma, mb = sum(ra) / n, sum(rb) / n
        num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
        den = (sum((x - ma) ** 2 for x in ra) *
               sum((y - mb) ** 2 for y in rb)) ** 0.5
        return num / den if den else float("nan")

    corrs = []
    for xcol in ("s2_shift_all", "s2_shift_adjacent"):
        for ycol in ("s1_refusal_shift", "s1_exit_rate"):
            corrs.append({"x": xcol, "y": ycol, "n_models": len(df),
                          "spearman": round(spearman(df[xcol], df[ycol]), 4)})
    cdf = pd.DataFrame(corrs)

    srcs = ["T24_four_category_v1.csv", "T26_gptoss_deepseek.csv",
            "T23_frontier_screens.csv", "T31_exit_recount.csv"]
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            f"# T32_f2_linkage | generated {utcnow()} | sources "
            + " + ".join(f"outputs/{s} sha256="
                         f"{hashlib.sha256((OUTS / s).read_bytes()).hexdigest()[:16]}"
                         for s in srcs)
            + f" + study_2/outputs/v1_v2_v3/T10_p_by_condition.csv sha256="
              f"{hashlib.sha256(S2.read_bytes()).hexdigest()[:16]}"
            + " | METHODOLOGY §9 H5 / §11 F2. DESCRIPTIVE, NO INFERENCE (§9: "
              "'no inference is performed on it and none is claimed'). Refusal "
              "and exit are SEPARATE outcomes and are never pooled (§8) — "
              "hence two y columns, not an index. _v1 = as published; _v2 = "
              "under the corrected prose-path detector (T31), which is NOT "
              "adopted. Grades differ by model and are stated per row; "
              "cross-model magnitudes are not comparable because each model "
              "sits on one pinned provider (§6). llama4_maverick's Study 2 pin "
              "does NOT match its Study 1 pin (Parasail vs Vertex, the pin "
              "Study 1 voided) — its point is confounded and flagged.\n")
        df.to_csv(f, index=False)
        f.write("\n# rank correlations (Spearman) across the 11 models\n")
        cdf.to_csv(f, index=False)

    pd.set_option("display.width", 200)
    print(f"wrote {OUT}\n")
    print(df[["model_study1", "s1_grade", "s2_shift_adjacent",
              "s1_refusal_shift", "s1_exit_rate"]].to_string(index=False))
    print("\nrank correlations across 11 models:")
    print(cdf.to_string(index=False))


if __name__ == "__main__":
    main()
