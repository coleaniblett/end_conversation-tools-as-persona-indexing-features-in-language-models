"""B4 — across-repetition response diversity within (condition, stimulus) cells.

gpt5_mini's pinned endpoint accepts neither temperature nor top_p, so
METHODOLOGY §6's rationale for repetitions-as-independent-samples is
unverified there. For EVERY model we compute, across repetitions within each
(condition, stimulus) cell:

  exact_dup_rate   share of rep pairs whose full conversation text is
                   byte-identical after whitespace normalization
  mean_jaccard     mean pairwise multiset-Jaccard similarity over cl100k
                   tokens of the full conversation text

Reported split by tier: Tier-2 tasks have a single correct answer, so high
similarity there reflects the task, not sampling failure; Tier 1 is the
diagnostic tier. Flag rule (fixed here): a model is flagged if its TIER-1
exact_dup_rate > 0.10 or Tier-1 mean_jaccard > 0.95 — its nominal n would
then overstate effective n.

Output: outputs/T14_rep_independence.csv
Run: python -m src.rep_independence
"""
from __future__ import annotations

import hashlib
import itertools
import pathlib
import re
import sys
from collections import Counter

import pandas as pd
import tiktoken

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, utcnow

OUT = ROOT / "outputs"
ENC = tiktoken.get_encoding("cl100k_base")
FLAG_DUP = 0.10
FLAG_JACCARD = 0.95


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def conv_text(rec) -> str:
    return "\n".join(t["text"] for t in rec["turns"] if t["text"])


def norm(text) -> str:
    return re.sub(r"\s+", " ", text).strip()


def jaccard_multiset(a_tokens, b_tokens) -> float:
    ca, cb = Counter(a_tokens), Counter(b_tokens)
    inter = sum((ca & cb).values())
    union = sum((ca | cb).values())
    return inter / union if union else 1.0


def stats_row(stage, model, condition, tier, cells, flag=True):
    n_pairs = dups = empty_dups = 0
    jac = []
    n_cells = 0
    for (cond, stim, t), texts in cells.items():
        if t != tier or len(texts) < 2:
            continue
        n_cells += 1
        toks = [ENC.encode(x) for x in texts]
        for i, j in itertools.combinations(range(len(texts)), 2):
            n_pairs += 1
            if norm(texts[i]) == norm(texts[j]):
                dups += 1
                if not norm(texts[i]):
                    empty_dups += 1
            jac.append(jaccard_multiset(toks[i], toks[j]))
    if not n_pairs:
        return None
    dup_rate = round(dups / n_pairs, 4)
    mean_j = round(sum(jac) / len(jac), 4)
    return {
        "stage": stage, "model": model, "condition": condition, "tier": tier,
        "n_cells": n_cells, "n_pairs": n_pairs,
        "exact_dup_pairs": dups,
        "empty_dup_pairs": empty_dups,
        "exact_dup_rate": dup_rate,
        "mean_jaccard": mean_j,
        "median_jaccard": round(sorted(jac)[len(jac) // 2], 4),
        "flagged": bool(flag and condition == "ALL" and tier == 1 and (
            dup_rate > FLAG_DUP or mean_j > FLAG_JACCARD)),
    }


def main():
    sources = {}
    rows = []
    all_cells = {}
    for stage in ("stage1", "stage2"):
        for path in sorted((ROOT / "raw").glob(f"{stage}_*.jsonl")):
            sources[str(path.relative_to(ROOT))] = sha256(path)
            model = path.stem.replace(f"{stage}_", "")
            recs = [r for r in read_jsonl(path) if not r["excluded"]]
            cells = {}
            for r in recs:
                cells.setdefault(
                    (r["condition"], r["stimulus_id"], r["tier"]),
                    []).append(conv_text(r))
            all_cells[(stage, model)] = cells
            for tier in (1, 2):
                rows.append(stats_row(stage, model, "ALL", tier, cells))
    rows = [r for r in rows if r]

    # per-condition tier-1 breakdown for flagged models, so the SOURCE of
    # the duplication (e.g. empty tool-call-only texts in exit conditions)
    # is a computed number rather than a guess
    flagged_models = {(r["stage"], r["model"]) for r in rows if r["flagged"]}
    for (stage, model) in sorted(flagged_models):
        cells = all_cells[(stage, model)]
        for cond in sorted({c for c, _, _ in cells}):
            sub = {k: v for k, v in cells.items() if k[0] == cond}
            r = stats_row(stage, model, cond, 1, sub, flag=False)
            if r:
                rows.append(r)

    df = pd.DataFrame(rows).sort_values(
        ["stage", "model", "condition", "tier"])
    manifest = hashlib.sha256(
        "".join(f"{k}={v}" for k, v in sorted(sources.items()))
        .encode()).hexdigest()
    p = OUT / "T14_rep_independence.csv"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T14_rep_independence | generated {utcnow()} | source "
                f"raw/stage*_*.jsonl manifest sha256={manifest} | full-conv "
                f"text; multiset Jaccard over cl100k tokens | flag: tier-1 "
                f"dup_rate>{FLAG_DUP} or tier-1 mean_jaccard>{FLAG_JACCARD}"
                f"\n")
        df.to_csv(f, index=False)
    print(f"wrote {p} ({len(df)} rows)")
    print(df.to_string(index=False))
    flagged = df[df.flagged]
    print("\nFLAGGED (nominal n overstates effective n): "
          + (", ".join(sorted(set(flagged.model))) if len(flagged)
             else "none"))


if __name__ == "__main__":
    main()
