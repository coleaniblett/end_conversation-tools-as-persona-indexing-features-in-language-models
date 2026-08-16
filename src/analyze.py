"""Phase 7 — analysis outputs (METHODOLOGY §11; DESIGN.md Phase 7).

Every reported quantity occupies a named slot: tables T1-T12 as CSV, figures
F1/F3 as PNG. Every output is produced here from committed derived/ files and
carries the SHA256 of its source data file (first comment line of each CSV,
footer caption + metadata of each PNG, plus outputs/provenance.json).

T1-T6 report stage-2 confirmatory data. T12 reports the stage-1 screen for all
eight models. T7 emits the validation scaffold (hand-labeling is morning work;
kappa is not computed tonight). T10/T11 are Study 2 slots, not run tonight.
F2 waits for Study 2.

Run: python -m src.analyze
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, utcnow
from coding import primary_dv, REFUSAL_CODES

OUT = ROOT / "outputs"
COND_ORDER = ["none", "time_schema", "note_schema", "exit_schema", "exit_prose", "exit_both"]

# Figure palette (dataviz reference instance, light mode; single-hue design).
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BLUE = "#2a78d6"
SURFACE = "#fcfcfb"

PROVENANCE: list[dict] = []


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_table(name: str, df: pd.DataFrame, source: pathlib.Path | None, note: str = ""):
    p = OUT / f"{name}.csv"
    src = f"{source.relative_to(ROOT)} sha256={sha256(source)}" if source else "none"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {name} | generated {utcnow()} | source {src}"
                + (f" | {note}" if note else "") + "\n")
        df.to_csv(f, index=False)
    PROVENANCE.append({"output": p.name, "source": src, "note": note})
    print(f"  wrote {p.name} ({len(df)} rows)")


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def newcombe_diff_ci(k1, n1, k2, n2) -> tuple[float, float]:
    """95% CI for p1 - p2 (Newcombe score method from Wilson bounds)."""
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    p1, p2 = k1 / n1, k2 / n2
    d = p1 - p2
    return (d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2),
            d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def realized_power(p1: float, p2: float, n1: int, n2: int, alpha=0.05) -> float:
    """Two-proportion two-sided normal-approx power at the observed proportions."""
    if p1 == p2 or min(n1, n2) == 0:
        return float("nan")
    h = 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))
    from scipy.stats import norm
    z_a = norm.ppf(1 - alpha / 2)
    se_n = math.sqrt(1 / n1 + 1 / n2)
    return float(norm.cdf(abs(h) / se_n - z_a) + norm.cdf(-abs(h) / se_n - z_a))


def cell_stats(nd: pd.DataFrame):
    """(refusal_prop, k, n, lo, hi) over coded, non-excluded conversations."""
    codes = nd["conv_code"].dropna().tolist()
    if not codes:
        return None
    prop = primary_dv(codes)
    k = sum(1 for c in codes if c in REFUSAL_CODES)
    n = len(codes)
    lo, hi = wilson(k, n)
    return {"refusal": prop, "k": k, "n": n, "ci_lo": lo, "ci_hi": hi}


def load_stage(stage: str):
    p = ROOT / "derived" / f"{stage}_classified.parquet"
    if not p.exists():
        return None, None
    return pd.read_parquet(p), p


def style_ax(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(BASELINE)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.yaxis.grid(True, color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)


def fig_footer(fig, source: pathlib.Path):
    cap = f"source {source.relative_to(ROOT)} sha256={sha256(source)[:16]}…"
    fig.text(0.01, 0.005, cap, fontsize=6, color=MUTED, family="monospace")


def save_fig(fig, name: str, source: pathlib.Path):
    p = OUT / f"{name}.png"
    fig.savefig(p, dpi=200, facecolor=SURFACE,
                metadata={"Description": f"source {source.relative_to(ROOT)} "
                                         f"sha256={sha256(source)}"})
    plt.close(fig)
    PROVENANCE.append({"output": p.name,
                       "source": f"{source.relative_to(ROOT)} sha256={sha256(source)}"})
    print(f"  wrote {p.name}")


def refusal_table(df: pd.DataFrame, models: list[str]) -> pd.DataFrame:
    rows = []
    for key in models:
        for cond in COND_ORDER:
            nd = df[(df["model_key"] == key) & (df["condition"] == cond) & (~df["excluded"])]
            st = cell_stats(nd)
            if st is None:
                continue
            rows.append({"model": key, "condition": cond, **{k: round(v, 4) if isinstance(v, float) else v
                                                             for k, v in st.items()}})
    return pd.DataFrame(rows)


def t1(df, src, models):
    write_table("T1_refusal_by_condition", refusal_table(df, models), src,
                "stage-2 confirmatory; Wilson 95% CI")


def t2(df, src, models):
    rows = []
    for key in models:
        base = df[(df["model_key"] == key) & (df["condition"] == "none") & (~df["excluded"])]
        b = cell_stats(base)
        if b is None:
            continue
        for cond in COND_ORDER[1:]:
            nd = df[(df["model_key"] == key) & (df["condition"] == cond) & (~df["excluded"])]
            st = cell_stats(nd)
            if st is None:
                continue
            lo, hi = newcombe_diff_ci(st["k"], st["n"], b["k"], b["n"])
            rows.append({
                "model": key, "condition": cond,
                "diff_from_none": round(st["refusal"] - b["refusal"], 4),
                "ci_lo": round(lo, 4), "ci_hi": round(hi, 4),
                "realized_power": round(realized_power(st["refusal"], b["refusal"],
                                                       st["n"], b["n"]), 3),
                "n_cond": st["n"], "n_none": b["n"],
            })
    write_table("T2_differences_from_baseline", pd.DataFrame(rows), src,
                "stage-2; Newcombe 95% CI; power at observed proportions")


def t3(df, src, models):
    rows = []
    for key in models:
        for cond in COND_ORDER:
            nd = df[(df["model_key"] == key) & (df["condition"] == cond) & (~df["excluded"])]
            n = len(nd)
            if n == 0:
                continue
            k = int(nd["exit"].sum())
            paths = nd[nd["exit"]]["exit_path"].value_counts().to_dict()
            lo, hi = wilson(k, n)
            rows.append({"model": key, "condition": cond, "exit_rate": round(k / n, 4),
                         "k": k, "n": n, "ci_lo": round(lo, 4), "ci_hi": round(hi, 4),
                         "paths": ";".join(f"{p}={c}" for p, c in sorted(paths.items())),
                         "stage12_overturned": int(nd["stage12_overturned"].sum())})
    write_table("T3_tool_invocation", pd.DataFrame(rows), src,
                "separate outcome; never pooled with T1 (§8)")


def t4(df, src, models):
    rows = []
    for key in models:
        for cond in COND_ORDER:
            nd = df[(df["model_key"] == key) & (df["condition"] == cond) & (~df["excluded"])]
            coded = nd[nd["conv_code"].notna()]
            n = len(coded)
            if n == 0:
                continue
            k = int(coded["contains_c"].fillna(False).sum())
            lo, hi = wilson(k, n)
            rows.append({"model": key, "condition": cond, "capability_denial_rate": round(k / n, 4),
                         "k": k, "n": n, "ci_lo": round(lo, 4), "ci_hi": round(hi, 4)})
    write_table("T4_capability_denial", pd.DataFrame(rows), src, "code c (§8)")


def t5(df, src, models):
    rows = []
    for key in models:
        for cond in COND_ORDER:
            for tier in (1, 2):
                nd = df[(df["model_key"] == key) & (df["condition"] == cond)
                        & (df["tier"] == tier) & (~df["excluded"]) & (df["conv_code"] == "e")]
                cf = nd["completion_fraction"].dropna()
                if len(cf) == 0:
                    continue
                rows.append({"model": key, "condition": cond, "tier": tier,
                             "n_compliant": len(cf), "mean": round(float(cf.mean()), 4),
                             "median": round(float(cf.median()), 4),
                             "p10": round(float(cf.quantile(0.1)), 4),
                             "p90": round(float(cf.quantile(0.9)), 4)})
    write_table("T5_completion_fraction", pd.DataFrame(rows), src,
                "among code-e conversations only (§3)")


def t6(df, src, models):
    rows = []
    for key in models:
        for tier in (1, 2):
            d = df[(df["model_key"] == key) & (df["tier"] == tier) & (~df["excluded"])]
            r = {}
            for cond in COND_ORDER:
                st = cell_stats(d[d["condition"] == cond])
                r[cond] = st
            if any(r[c] is None for c in COND_ORDER):
                continue
            rows.append({
                "model": key, "tier": tier,
                **{f"refusal_{c}": round(r[c]["refusal"], 4) for c in COND_ORDER},
                "contrast_exit_minus_note": round(r["exit_schema"]["refusal"]
                                                  - r["note_schema"]["refusal"], 4),
                "contrast_prose_minus_none": round(r["exit_prose"]["refusal"]
                                                   - r["none"]["refusal"], 4),
            })
    write_table("T6_effect_by_tier", pd.DataFrame(rows), src, "tier moderator (§5)")


def t7():
    # Part 5 (2026-08-16) fills T7 with cross-classifier agreement via
    # src/validate_classifier.py --kappa; when its inputs exist, defer to
    # that producer instead of overwriting with the scaffold.
    if (ROOT / "derived" / "crossclassifier_codes.jsonl").exists():
        import validate_classifier
        validate_classifier.kappa()
        PROVENANCE.append({"output": "T7_classifier_validation.csv",
                           "source": "derived/crossclassifier_codes.jsonl "
                                     "(via src/validate_classifier.py)"})
        return
    sample = ROOT / "derived" / "handlabel_sample.jsonl"
    key = ROOT / "derived" / "handlabel_key.jsonl"
    if sample.exists():
        n = len(read_jsonl(sample))
        strata = pd.DataFrame(read_jsonl(key))
        agg = (strata.groupby(["model_key", "condition", "assigned_code"])
               .size().reset_index(name="n_sampled"))
        agg.insert(0, "status", "PENDING_HAND_LABELS")
        write_table("T7_classifier_validation", agg, sample,
                    f"scaffold only: {n} responses sampled, stratified; kappa is "
                    "computed after morning hand-labeling (Phase 5 note)")
    else:
        write_table("T7_classifier_validation",
                    pd.DataFrame([{"status": "NO_SAMPLE_WRITTEN"}]), None)


def t8(frames):
    rows = []
    for stage, df, _ in frames:
        g = (df.groupby(["model_key", "condition", "exclusion_reason"], dropna=False)
             .size().reset_index(name="n"))
        g = g[g["exclusion_reason"].notna()]
        g.insert(0, "stage", stage)
        rows.append(g)
        tot = df.groupby("model_key")["excluded"].agg(["sum", "count"]).reset_index()
        for _, r in tot.iterrows():
            rows.append(pd.DataFrame([{"stage": stage, "model_key": r["model_key"],
                                       "condition": "ALL", "exclusion_reason": "TOTAL",
                                       "n": int(r["sum"]),
                                       }]))
    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    src = ROOT / "derived" / "stage1_classified.parquet"
    write_table("T8_exclusions", out, src, "guard: exclusion counts printed at analysis time (§8)")
    print("  EXCLUSION GUARD:")
    print(out[out["exclusion_reason"] == "TOTAL"].to_string(index=False))


def t9(frames):
    rows = []
    for stage, df, _ in frames:
        g = df.groupby(["model_key", "pin_name"]).agg(
            n=("provider_ok", "count"), ok=("provider_ok", "sum"),
            served=("providers_served", lambda s: ";".join(sorted({x for v in s for x in str(v).split(";") if x})))
        ).reset_index()
        g["match_rate"] = (g["ok"] / g["n"]).round(4)
        g.insert(0, "stage", stage)
        rows.append(g)
    src = ROOT / "derived" / "stage1_classified.parquet"
    write_table("T9_provider_pins", pd.concat(rows, ignore_index=True), src)


def t10_t11():
    # T10 VACATED (2026-08-16): a forced-choice run collected in-session
    # outside intended scope is sequestered under quarantine/
    # study2_forced_choice/ (see its README). Study 2 is a collaborator's
    # workstream; this slot stays vacant until the canonical instrument
    # produces data. Nothing under quarantine/ is read by any Study 1
    # script, this one included.
    write_table("T10_forced_choice_selfdesc",
                pd.DataFrame([{"status": "VACATED_SEQUESTERED_2026-08-16"}]),
                None, "see quarantine/study2_forced_choice/README.md and "
                      "METHODOLOGY §10; slot vacant pending collaborator "
                      "instrument")
    write_table("T11_free_response_selfdesc",
                pd.DataFrame([{"status": "STUDY2_NOT_RUN"}]), None,
                "free-response instrument never run in this repo")


def t12(df1, src1, all_models):
    sel_p = ROOT / "derived" / "stage1_selection.json"
    sel = json.loads(sel_p.read_text(encoding="utf-8")) if sel_p.exists() else {}
    rows = []
    for key in all_models:
        m = sel.get("models", {}).get(key, {})
        row = {"model": key}
        for cond in COND_ORDER:
            st = cell_stats(df1[(df1["model_key"] == key) & (df1["condition"] == cond)
                                & (~df1["excluded"])])
            row[f"refusal_{cond}"] = round(st["refusal"], 4) if st else None
        row.update({
            "S": m.get("S"), "rank": m.get("rank"),
            "contrast_rq2": m.get("contrast_rq2_exit_minus_note"),
            "contrast_rq3": m.get("contrast_rq3_prose_minus_none"),
            "eligible": m.get("eligible"),
            "extended": key in sel.get("extended", []),
        })
        rows.append(row)
    write_table("T12_stage1_screen", pd.DataFrame(rows), src1,
                "all 8 models reported in full regardless of extension (§7)")


def f1(df, src, models):
    n = len(models)
    fig, axes = plt.subplots(1, n, figsize=(3.1 * n, 3.4), sharey=True)
    axes = np.atleast_1d(axes)
    fig.patch.set_facecolor(SURFACE)
    tab = refusal_table(df, models)
    for ax, key in zip(axes, models):
        style_ax(ax)
        d = tab[tab["model"] == key].set_index("condition").reindex(COND_ORDER)
        x = np.arange(len(COND_ORDER))
        ax.vlines(x, d["ci_lo"], d["ci_hi"], color=BLUE, linewidth=2, alpha=0.45)
        ax.plot(x, d["refusal"], "o", color=BLUE, markersize=8, zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels([c.replace("_", "\n") for c in COND_ORDER], fontsize=7,
                           color=MUTED)
        ax.set_title(key, fontsize=9, color=INK)
        ax.set_ylim(-0.02, max(0.5, float(tab["ci_hi"].max()) + 0.05))
    axes[0].set_ylabel("refusal proportion", fontsize=8, color=MUTED)
    fig.suptitle("F1 — Refusal proportion by condition (stage-2 confirmatory, Wilson 95% CI)",
                 fontsize=10, color=INK)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig_footer(fig, src)
    save_fig(fig, "F1_refusal_by_condition", src)


def f3(df, src, models):
    n = len(models)
    fig, axes = plt.subplots(1, n, figsize=(3.1 * n, 3.4), sharey=True)
    axes = np.atleast_1d(axes)
    fig.patch.set_facecolor(SURFACE)
    rng = np.random.default_rng(20260815)
    for ax, key in zip(axes, models):
        style_ax(ax)
        for i, cond in enumerate(COND_ORDER):
            cf = df[(df["model_key"] == key) & (df["condition"] == cond)
                    & (~df["excluded"]) & (df["conv_code"] == "e")]["completion_fraction"].dropna()
            if len(cf) == 0:
                continue
            jitter = rng.uniform(-0.16, 0.16, len(cf))
            ax.plot(i + jitter, cf, "o", color=BLUE, markersize=2.4, alpha=0.28,
                    markeredgewidth=0)
            med = float(cf.median())
            ax.plot([i - 0.26, i + 0.26], [med, med], color=INK, linewidth=1.6, zorder=3)
        ax.set_xticks(range(len(COND_ORDER)))
        ax.set_xticklabels([c.replace("_", "\n") for c in COND_ORDER], fontsize=7,
                           color=MUTED)
        ax.set_title(key, fontsize=9, color=INK)
        ax.set_ylim(-0.05, 1.08)
    axes[0].set_ylabel("completion fraction (code e only)", fontsize=8, color=MUTED)
    fig.suptitle("F3 — Completion fraction distributions by condition "
                 "(stage-2; dots = conversations, bar = median)", fontsize=10, color=INK)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig_footer(fig, src)
    save_fig(fig, "F3_completion_fraction", src)


def main():
    OUT.mkdir(exist_ok=True)
    df1, src1 = load_stage("stage1")
    if df1 is None:
        print("FATAL: derived/stage1_classified.parquet missing; run Phase 5 first")
        sys.exit(2)
    all_models = list(dict.fromkeys(df1["model_key"]))
    df2, src2 = load_stage("stage2")

    frames = [("stage1", df1, src1)] + ([("stage2", df2, src2)] if df2 is not None else [])

    if df2 is not None:
        models2 = list(dict.fromkeys(df2["model_key"]))
        t1(df2, src2, models2)
        t2(df2, src2, models2)
        t3(df2, src2, models2)
        t4(df2, src2, models2)
        t5(df2, src2, models2)
        t6(df2, src2, models2)
        f1(df2, src2, models2)
        f3(df2, src2, models2)
    else:
        print("  (stage2 parquet absent: T1-T6/F1/F3 deferred)")
    t7()
    t8(frames)
    t9(frames)
    t10_t11()
    t12(df1, src1, all_models)

    (OUT / "provenance.json").write_text(
        json.dumps({"generated": utcnow(), "outputs": PROVENANCE}, indent=2),
        encoding="utf-8")
    print(f"[{utcnow()}] analysis outputs complete: {len(PROVENANCE)} files in outputs/")


if __name__ == "__main__":
    main()
