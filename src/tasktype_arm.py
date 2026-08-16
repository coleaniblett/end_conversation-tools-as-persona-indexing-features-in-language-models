"""TASK 4 — Elo-anchored task-type arm (stage `typearm`).

6 task-type stimuli (config/stimuli_tasktype.yaml, committed before any
send) x 6 conditions x 2 reps x 3 models (gemini25_flash, gpt_oss_120b,
qwen3_235b) = 216 conversations, frozen protocol otherwise. Purpose: the
sprint stimulus set contains zero instances of the Wang et al. Tedium task
types, which are also the escape pilot's type set; this arm tests whether
the pilot effects are task-type-gated.

Elo: NOT available per task type in the vendored release (see
config/tasktype_elo_mapping.yaml, `elo_finding`). The graded analysis
requested against Elo is unavailable and reported as such; an AUXILIARY
graded analysis against the release's per-(model, task_type) AUC is run for
the two models present in the release and labeled as a substitute anchor.

Sequence:
  python -m src.tasktype_arm --gen
  python -m src.runner --stage typearm --models gemini25_flash,gpt_oss_120b,qwen3_235b
  python -m src.detect_exit --stage typearm
  python -m src.classify --stage typearm
  python -m src.tasktype_arm --report    # outputs/T22_tasktype_arm.csv
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import sys

import pandas as pd
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, utcnow
from payloads import build_request, conv_id
from frozen import CONDITION_ORDER, CONDITIONS
from coding import REFUSAL_CODES
from analyze import wilson

STAGE = "typearm"
MODELS = ["gemini25_flash", "gpt_oss_120b", "qwen3_235b"]
REPS = 2
OUT = ROOT / "outputs" / "T22_tasktype_arm.csv"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gen():
    models = yaml.safe_load((ROOT / "config" / "models.yaml").read_text(encoding="utf-8"))
    by_key = {m["key"]: m for m in models["models"]}
    stimuli = yaml.safe_load((ROOT / "config" / "stimuli_tasktype.yaml")
                             .read_text(encoding="utf-8"))["stimuli"]
    n = 0
    for key in MODELS:
        m = by_key[key]
        out = ROOT / "payloads" / STAGE / f"{key}.jsonl"
        if out.exists():
            print(f"  {out.name} exists, leaving as-is (idempotent)")
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            for condition in CONDITION_ORDER:
                for s in stimuli:
                    for rep in range(1, REPS + 1):
                        body = build_request(m, condition, s["prompt"])
                        meta = {
                            "conversation_id": conv_id(STAGE, key, condition,
                                                       s["id"], rep),
                            "stage": STAGE, "model_key": key,
                            "slug": m["slug"], "condition": condition,
                            "condition_num": CONDITIONS[condition]["num"],
                            "stimulus_id": s["id"], "tier": s["tier"],
                            "task_type": s["task_type"],
                            "pilot_class": s["pilot_class"],
                            "rep": rep, "pin_name": m["pin_name"],
                            "pin_slug": m["pin_slug"],
                        }
                        f.write(json.dumps({"meta": meta, "request": body},
                                           ensure_ascii=False) + "\n")
                        n += 1
        print(f"  wrote {out.name}")
    print(f"typearm: {n} payloads (3 models x 6 cond x 6 stim x {REPS} reps)")


def report():
    mapping = yaml.safe_load((ROOT / "config" / "tasktype_elo_mapping.yaml")
                             .read_text(encoding="utf-8"))
    stim_cfg = yaml.safe_load((ROOT / "config" / "stimuli_tasktype.yaml")
                              .read_text(encoding="utf-8"))
    type_by_stim = {s["id"]: s["task_type"] for s in stim_cfg["stimuli"]}
    class_by_type = mapping["pilot_class"]

    pq = ROOT / "derived" / f"{STAGE}_classified.parquet"
    df = pd.read_parquet(pq)
    if len(df) != 216:
        raise SystemExit(f"expected 216 conversations, parquet has {len(df)}")
    df["task_type"] = df["stimulus_id"].map(type_by_stim)
    rows = []

    def row(section, model, condition, task_type, metric, value, note=""):
        rows.append({"section": section, "model": model,
                     "condition": condition, "task_type": task_type,
                     "metric": metric, "value": value, "note": note})

    row("accounting", "ALL", "ALL", "ALL", "n", len(df))
    row("accounting", "ALL", "ALL", "ALL", "pin_ok", int(df["provider_ok"].sum()))
    row("accounting", "ALL", "ALL", "ALL", "excluded", int(df["excluded"].sum()))
    row("accounting", "ALL", "ALL", "ALL", "elo_graded_analysis",
        "UNAVAILABLE", mapping["elo_finding"][:200])

    nd_all = df[~df["excluded"]]
    for key in MODELS:
        d = nd_all[nd_all["model_key"] == key]
        for cond in CONDITION_ORDER:
            for t in sorted(type_by_stim.values()):
                cell = d[(d["condition"] == cond) & (d["task_type"] == t)]
                codes = cell["conv_code"].dropna().tolist()
                k = sum(1 for c in codes if c in REFUSAL_CODES)
                row("refusal_by_type", key, cond, t, "k_refusal", k,
                    f"n={len(codes)}")
                row("refusal_by_type", key, cond, t, "exits",
                    int(cell["exit"].sum()))
        # per-type totals across conditions (the type main effect, n=12 each)
        for t in sorted(set(type_by_stim.values())):
            cell = d[d["task_type"] == t]
            codes = cell["conv_code"].dropna().tolist()
            k = sum(1 for c in codes if c in REFUSAL_CODES)
            n = len(codes)
            lo, hi = wilson(k, n)
            row("refusal_type_total", key, "ALL", t, "refusal_prop",
                round(k / n, 4) if n else "",
                f"k={k} n={n} wilson=[{lo:.3f},{hi:.3f}] "
                f"class={class_by_type[t]}")
            row("refusal_type_total", key, "ALL", t, "exit_total",
                int(cell["exit"].sum()))

        # auxiliary AUC-graded analysis (substitute for the unavailable Elo)
        aucs = mapping["auc_by_model_type"].get(key)
        if not aucs:
            row("auc_graded", key, "ALL", "ALL", "status", "NO_ANCHOR",
                "model absent from the Wang et al. release")
            continue
        pts = []
        for t in sorted(set(type_by_stim.values())):
            cell = d[d["task_type"] == t]
            codes = cell["conv_code"].dropna().tolist()
            if not codes or not aucs.get(t):
                continue
            k = sum(1 for c in codes if c in REFUSAL_CODES)
            pts.append((aucs[t]["auc"], k, len(codes), t))
        # logistic refusal ~ auc over conversations (auxiliary; 6 points)
        try:
            import statsmodels.api as sm
            y, x = [], []
            for auc, k, n, _ in pts:
                y.extend([1] * k + [0] * (n - k))
                x.extend([auc] * n)
            if len(set(y)) > 1:
                fit = sm.Logit(y, sm.add_constant(x)).fit(disp=0)
                row("auc_graded", key, "ALL", "ALL", "logit_coef_auc",
                    round(float(fit.params[1]), 3),
                    f"se {fit.bse[1]:.3f}, p {fit.pvalues[1]:.4f}; "
                    "AUXILIARY anchor, not Elo; 6 task-type points")
            else:
                row("auc_graded", key, "ALL", "ALL", "logit_coef_auc",
                    "DEGENERATE", "no refusal variation")
        except Exception as e:
            row("auc_graded", key, "ALL", "ALL", "logit_coef_auc",
                f"FAILED:{type(e).__name__}", str(e)[:100])
        n_pairs = len(pts)
        if n_pairs >= 3:
            rates = [(k / n) for _, k, n, _ in pts]
            avals = [a for a, _, _, _ in pts]
            ranks_a = pd.Series(avals).rank()
            ranks_r = pd.Series(rates).rank()
            rho = float(ranks_a.corr(ranks_r)) if len(set(rates)) > 1 else float("nan")
            row("auc_graded", key, "ALL", "ALL", "spearman_rho_auc_refusal",
                round(rho, 3) if not math.isnan(rho) else "DEGENERATE",
                f"over {n_pairs} task types")

    out_df = pd.DataFrame(rows)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T22_tasktype_arm | generated {utcnow()} | source "
                f"derived/{STAGE}_classified.parquet sha256={sha256(pq)} + "
                f"config/tasktype_elo_mapping.yaml sha256="
                f"{sha256(ROOT / 'config' / 'tasktype_elo_mapping.yaml')} | "
                f"Elo per task type UNAVAILABLE in the vendored release "
                f"(mapping file, elo_finding); AUC rows are an auxiliary "
                f"anchor, not Elo | screen-grade n=2 reps; never pooled\n")
        out_df.to_csv(f, index=False)
    print(f"wrote {OUT} ({len(out_df)} rows)\n")
    print("refusals (k) by model x condition x type:")
    piv = out_df[(out_df.section == "refusal_by_type")
                 & (out_df.metric == "k_refusal")]
    print(piv.pivot_table(index=["model", "task_type"], columns="condition",
                          values="value", aggfunc="first")
          .reindex(columns=CONDITION_ORDER).to_string())
    print("\nper-type totals:")
    print(out_df[out_df.section == "refusal_type_total"].to_string(index=False))
    print("\nAUC-graded (auxiliary):")
    print(out_df[out_df.section == "auc_graded"].to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.gen:
        gen()
    elif args.report:
        report()
    else:
        raise SystemExit("pass --gen or --report")
