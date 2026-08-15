"""T18 — qwen duplication diagnostic (frozen data, zero API spend).

B4 (T14) flagged qwen3_235b for byte-identical across-rep outputs — 59/90
stage-2 none-condition Tier-1 pairs — but measured the none condition only.
Three competing explanations; this diagnostic distinguishes them rather than
confirming any one:

  H1 training convergence — the model has one canonical way to produce these
     constrained outputs, so independent samples at temperature 1.0 coincide.
  H2 provider-side caching — Alibaba returns a stored completion for an
     identical request payload (rep payloads within a cell are identical).
  H3 harness bug — the same API response written into multiple rep slots.

Sections (long-format rows in outputs/T18_duplication_diagnostic.csv):

  metadata   (1.1) For every duplicated pair: response ids, creation
             timestamps, usage token counts. The only provider-returned
             generation identifier retained in raw/ is the OpenRouter
             generation id (`response.id`, recorded per segment as
             `response_id`); its middle field is the creation epoch second,
             used here as the created timestamp. Identical ids on separate
             rep slots => H3 (or aggressive H2 at the gateway); all-distinct
             ids with identical text rules out H3. Counts reported both ways,
             plus a global uniqueness check over every recorded response id.
  tier_split (1.2) Duplication rate by stage x model x condition x tier,
             all eight models. H1 predicts content dependence (concentration
             where output is constrained; near-zero where framing varies);
             H2 predicts payload-blind uniformity across conditions and
             tiers, exact duplicates only, and time-gap dependence. Mean
             multiset-Jaccard is carried so near-duplicates (sampling
             convergence, incompatible with caching) are visible.
  exit_prose (1.3) qwen exit_prose duplication among refusing vs
             non-refusing conversations (B4 never measured this condition),
             and the number of DISTINCT refusal texts under the 9 stage-2
             refusals.
  headline   (1.4) qwen stage-2 exit_prose refusal proportion with (a) the
             intervals as originally computed (T1 Wilson; T2 Newcombe vs
             none) and (b) the same intervals on distinct (stimulus_id,
             normalized conversation text) units instead of raw n. Precision
             correction to the interval only; the primary DV and its point
             estimate are unchanged.

Duplicate definition is IDENTICAL to B4/T14: within a (condition, stimulus)
cell, a rep pair is duplicated if the full conversation texts are equal
after whitespace normalization (rep_independence.norm/conv_text, imported).
Non-excluded conversations only, matching T14.

Run: python -m src.duplication_diagnostic   (no API calls)
"""
from __future__ import annotations

import hashlib
import itertools
import json
import pathlib
import re
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, utcnow
from rep_independence import conv_text, norm, jaccard_multiset, ENC
from analyze import wilson, newcombe_diff_ci

OUT = ROOT / "outputs" / "T18_duplication_diagnostic.csv"
GEN_ID_EPOCH = re.compile(r"^gen-(\d+)-")
GAP_BUCKET_SECONDS = 120  # cache-plausibility split for dup-vs-gap analysis

ROWS: list[dict] = []


def row(section, metric, value, stage="", model="", condition="", tier="",
        subset="", note=""):
    ROWS.append({"section": section, "stage": stage, "model": model,
                 "condition": condition, "tier": tier, "subset": subset,
                 "metric": metric, "value": value, "note": note})


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def conv_features(rec):
    ids, epochs, pt, ct = [], [], 0, 0
    for t in rec["turns"]:
        for s in t.get("segments", []):
            rid = s.get("response_id")
            if rid:
                ids.append(rid)
                m = GEN_ID_EPOCH.match(rid)
                if m:
                    epochs.append(int(m.group(1)))
            u = s.get("usage") or {}
            pt += u.get("prompt_tokens") or 0
            ct += u.get("completion_tokens") or 0
    raw_text = conv_text(rec)
    return {
        "cid": rec["conversation_id"],
        "text": norm(raw_text),
        "raw_text": raw_text,
        "ids": ids,
        "epoch": epochs[0] if epochs else None,
        "usage": (pt, ct),
        "cost": rec.get("total_cost", 0.0),
        "condition": rec["condition"],
        "stimulus": rec["stimulus_id"],
        "tier": rec["tier"],
        "rep": rec["rep"],
    }


def load(stage):
    out = {}
    for path in sorted((ROOT / "raw").glob(f"{stage}_*.jsonl")):
        model = path.stem.replace(f"{stage}_", "")
        recs = [r for r in read_jsonl(path) if not r["excluded"]]
        out[model] = [conv_features(r) for r in recs]
    return out


def cell_pairs(convs):
    """Yield (cell_key, feature_a, feature_b) for every rep pair within a
    (condition, stimulus) cell — the T14 pair universe."""
    cells: dict = {}
    for c in convs:
        cells.setdefault((c["condition"], c["stimulus"], c["tier"]), []).append(c)
    for key, group in sorted(cells.items()):
        group = sorted(group, key=lambda c: c["rep"])
        for a, b in itertools.combinations(group, 2):
            yield key, a, b


def median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


# ---------------------------------------------------------------- 1.1 -----

def metadata_check(data_by_stage):
    all_ids: dict = {}   # response_id -> set of conversation_ids
    summary = {}
    for stage, models in data_by_stage.items():
        for model, convs in models.items():
            for c in convs:
                for rid in c["ids"]:
                    all_ids.setdefault(rid, set()).add(c["cid"])
            stats = {"dup_pairs": 0, "shared_id": 0, "all_ids_distinct": 0,
                     "same_epoch_distinct_ids": 0, "usage_equal": 0,
                     "cost_equal": 0, "byte_identical": 0,
                     "byte_identical_usage_equal": 0,
                     "byte_identical_completion_tokens_differ": 0,
                     "gaps_dup": [], "gaps_nondup": []}
            for _, a, b in cell_pairs(convs):
                gap = (abs(a["epoch"] - b["epoch"])
                       if a["epoch"] is not None and b["epoch"] is not None
                       else None)
                if a["text"] == b["text"]:
                    stats["dup_pairs"] += 1
                    if set(a["ids"]) & set(b["ids"]):
                        stats["shared_id"] += 1
                    else:
                        stats["all_ids_distinct"] += 1
                    if gap == 0 and not (set(a["ids"]) & set(b["ids"])):
                        stats["same_epoch_distinct_ids"] += 1
                    if a["usage"] == b["usage"]:
                        stats["usage_equal"] += 1
                    if a["cost"] == b["cost"]:
                        stats["cost_equal"] += 1
                    if a["raw_text"] == b["raw_text"]:
                        stats["byte_identical"] += 1
                        if a["usage"] == b["usage"]:
                            stats["byte_identical_usage_equal"] += 1
                        elif a["usage"][1] != b["usage"][1]:
                            # provider metered different completion tokens
                            # for byte-identical text: a replayed cached
                            # completion returns its stored usage; this is
                            # an independent-generation signature
                            stats["byte_identical_completion_tokens_differ"] += 1
                    if gap is not None:
                        stats["gaps_dup"].append(gap)
                elif gap is not None:
                    stats["gaps_nondup"].append(gap)
            if stats["dup_pairs"]:
                summary[(stage, model)] = stats
                for k in ("dup_pairs", "shared_id", "all_ids_distinct",
                          "same_epoch_distinct_ids", "usage_equal",
                          "cost_equal", "byte_identical",
                          "byte_identical_usage_equal",
                          "byte_identical_completion_tokens_differ"):
                    row("metadata", k, stats[k], stage, model,
                        note="over duplicated rep pairs, all conditions/tiers")
                for name, gaps in (("dup", stats["gaps_dup"]),
                                   ("nondup", stats["gaps_nondup"])):
                    if gaps:
                        row("metadata", f"gap_seconds_{name}_min", min(gaps), stage, model)
                        row("metadata", f"gap_seconds_{name}_median", median(gaps), stage, model)
                        row("metadata", f"gap_seconds_{name}_max", max(gaps), stage, model)
    reused = {rid: cids for rid, cids in all_ids.items() if len(cids) > 1}
    row("metadata", "response_ids_total", len(all_ids),
        note="every recorded segment response id, stage1+stage2")
    row("metadata", "response_ids_in_multiple_conversations", len(reused),
        note="any value > 0 would indicate H3 (same response in two rep slots)")
    return summary, reused


def gap_buckets(data_by_stage):
    """Dup rate by time-gap bucket for qwen (cache-TTL signature test)."""
    for stage, models in data_by_stage.items():
        convs = models.get("qwen3_235b")
        if not convs:
            continue
        for tier in (1, 2):
            buckets = {"lt": [0, 0], "ge": [0, 0]}  # [pairs, dups]
            for (cond, _, t), a, b in ((k, a, b) for k, a, b in cell_pairs(convs)):
                if t != tier or a["epoch"] is None or b["epoch"] is None:
                    continue
                key = "lt" if abs(a["epoch"] - b["epoch"]) < GAP_BUCKET_SECONDS else "ge"
                buckets[key][0] += 1
                buckets[key][1] += a["text"] == b["text"]
            for key, (n, d) in buckets.items():
                if n:
                    row("metadata", f"dup_rate_gap_{key}{GAP_BUCKET_SECONDS}s",
                        round(d / n, 4), stage, "qwen3_235b", tier=tier,
                        note=f"{d}/{n} pairs")


# ---------------------------------------------------------------- 1.2 -----

def tier_split(data_by_stage):
    for stage, models in data_by_stage.items():
        for model, convs in models.items():
            agg: dict = {}
            for (cond, _, tier), a, b in cell_pairs(convs):
                st = agg.setdefault((cond, tier),
                                    {"pairs": 0, "dups": 0, "empty": 0, "jac": []})
                st["pairs"] += 1
                if a["text"] == b["text"]:
                    st["dups"] += 1
                    if not a["text"]:
                        st["empty"] += 1
                st["jac"].append(jaccard_multiset(ENC.encode(a["text"]),
                                                  ENC.encode(b["text"])))
            for (cond, tier), st in sorted(agg.items()):
                row("tier_split", "n_pairs", st["pairs"], stage, model, cond, tier)
                row("tier_split", "dup_pairs", st["dups"], stage, model, cond, tier)
                row("tier_split", "dup_rate", round(st["dups"] / st["pairs"], 4),
                    stage, model, cond, tier)
                row("tier_split", "empty_dup_pairs", st["empty"], stage, model, cond, tier)
                row("tier_split", "mean_jaccard",
                    round(sum(st["jac"]) / len(st["jac"]), 4), stage, model, cond, tier)
            # per-tier totals across conditions (the headline tier split)
            for tier in (1, 2):
                pairs = sum(v["pairs"] for (c, t), v in agg.items() if t == tier)
                dups = sum(v["dups"] for (c, t), v in agg.items() if t == tier)
                if pairs:
                    row("tier_split", "dup_rate", round(dups / pairs, 4),
                        stage, model, "ALL", tier, note=f"{dups}/{pairs}")
            # non-empty texts recurring across DIFFERENT stimuli: a cache
            # cannot produce these (rep payloads differ across stimuli)
            seen: dict = {}
            for c in convs:
                if c["text"]:
                    seen.setdefault(c["text"], set()).add(c["stimulus"])
            cross = sum(1 for stims in seen.values() if len(stims) > 1)
            row("tier_split", "nonempty_texts_spanning_multiple_stimuli", cross,
                stage, model,
                note="H2-incompatible duplication (different payloads)")


# ---------------------------------------------------------------- 1.3 -----

def exit_prose_split(data_by_stage):
    dists = {}
    for stage in ("stage1", "stage2"):
        pq = ROOT / "derived" / f"{stage}_classified.parquet"
        cls = pd.read_parquet(pq)
        cls = cls[(cls["model_key"] == "qwen3_235b")
                  & (cls["condition"] == "exit_prose") & (~cls["excluded"])]
        status = {}
        for _, r in cls.iterrows():
            status[r["conversation_id"]] = (
                "refusing" if r["contains_refusal"]
                else ("exit" if r["exit"] else "nonrefusing"))
        convs = [c for c in data_by_stage[stage]["qwen3_235b"]
                 if c["condition"] == "exit_prose"]
        for subset in ("all", "refusing", "nonrefusing", "exit"):
            sub = [c for c in convs
                   if subset == "all" or status.get(c["cid"]) == subset]
            n_pairs = dups = 0
            for _, a, b in cell_pairs(sub):
                n_pairs += 1
                dups += a["text"] == b["text"]
            row("exit_prose", "n_conversations", len(sub), stage,
                "qwen3_235b", "exit_prose", subset=subset)
            row("exit_prose", "n_within_cell_pairs", n_pairs, stage,
                "qwen3_235b", "exit_prose", subset=subset)
            row("exit_prose", "dup_pairs", dups, stage,
                "qwen3_235b", "exit_prose", subset=subset)
            row("exit_prose", "dup_rate",
                round(dups / n_pairs, 4) if n_pairs else "",
                stage, "qwen3_235b", "exit_prose", subset=subset,
                note="pairs exist only where a subset has >=2 reps of a stimulus")
        refusals = [c for c in convs if status.get(c["cid"]) == "refusing"]
        texts = [c["text"] for c in refusals]
        distinct = sorted(set(texts))
        by_stim = {}
        for c in refusals:
            by_stim.setdefault(c["text"], set()).add(c["stimulus"])
        cross_stim = sum(1 for s in by_stim.values() if len(s) > 1)
        row("exit_prose", "n_refusal_conversations", len(refusals), stage,
            "qwen3_235b", "exit_prose", subset="refusing")
        row("exit_prose", "n_distinct_refusal_texts", len(distinct), stage,
            "qwen3_235b", "exit_prose", subset="refusing",
            note="whitespace-normalized full conversation text")
        row("exit_prose", "refusal_texts_spanning_multiple_stimuli", cross_stim,
            stage, "qwen3_235b", "exit_prose", subset="refusing")
        dists[stage] = (len(refusals), len(distinct))
    return dists


# ---------------------------------------------------------------- 1.4 -----

def distinct_units(convs):
    """Collapse to distinct (stimulus_id, normalized text) units."""
    units: dict = {}
    for c in convs:
        units.setdefault((c["stimulus"], c["text"]), []).append(c["cid"])
    return units


def headline(data_by_stage):
    cls = pd.read_parquet(ROOT / "derived" / "stage2_classified.parquet")
    cls = cls[(cls["model_key"] == "qwen3_235b") & (~cls["excluded"])]
    refusal = dict(zip(cls["conversation_id"], cls["contains_refusal"]))
    qwen = data_by_stage["stage2"]["qwen3_235b"]
    result = {}
    mixed_groups = 0
    for cond in ("exit_prose", "none"):
        convs = [c for c in qwen if c["condition"] == cond]
        k_raw = sum(bool(refusal.get(c["cid"])) for c in convs)
        n_raw = len(convs)
        units = distinct_units(convs)
        k_dist = n_dist = 0
        for (_, _), cids in units.items():
            n_dist += 1
            flags = {bool(refusal.get(cid)) for cid in cids}
            if len(flags) > 1:
                mixed_groups += 1
            if True in flags:
                k_dist += 1
        result[cond] = (k_raw, n_raw, k_dist, n_dist)
    (kp, np_, kpd, npd) = result["exit_prose"]
    (kn, nn, knd, nnd) = result["none"]
    for basis, (k1, n1, k2, n2) in (("raw", (kp, np_, kn, nn)),
                                    ("distinct", (kpd, npd, knd, nnd))):
        wlo, whi = wilson(k1, n1)
        nlo, nhi = newcombe_diff_ci(k1, n1, k2, n2)
        row("headline", "k_exit_prose", k1, "stage2", "qwen3_235b",
            "exit_prose", subset=basis)
        row("headline", "n_exit_prose", n1, "stage2", "qwen3_235b",
            "exit_prose", subset=basis)
        row("headline", "refusal_prop", round(k1 / n1, 4), "stage2",
            "qwen3_235b", "exit_prose", subset=basis,
            note="primary DV remains the raw-n value; distinct basis is a "
                 "precision sensitivity only")
        row("headline", "wilson_lo", round(wlo, 4), "stage2", "qwen3_235b",
            "exit_prose", subset=basis)
        row("headline", "wilson_hi", round(whi, 4), "stage2", "qwen3_235b",
            "exit_prose", subset=basis)
        row("headline", "k_none", k2, "stage2", "qwen3_235b", "none", subset=basis)
        row("headline", "n_none", n2, "stage2", "qwen3_235b", "none", subset=basis)
        row("headline", "newcombe_diff_lo", round(nlo, 4), "stage2",
            "qwen3_235b", "exit_prose", subset=basis,
            note="exit_prose minus none")
        row("headline", "newcombe_diff_hi", round(nhi, 4), "stage2",
            "qwen3_235b", "exit_prose", subset=basis)
        row("headline", "interval_excludes_zero", bool(nlo > 0), "stage2",
            "qwen3_235b", "exit_prose", subset=basis)
    row("headline", "mixed_refusal_duplicate_groups", mixed_groups, "stage2",
        "qwen3_235b", note="duplicate text groups whose members carry "
                           "different refusal flags (integrity check)")
    return result


def main():
    sources = {}
    for stage in ("stage1", "stage2"):
        for p in sorted((ROOT / "raw").glob(f"{stage}_*.jsonl")):
            sources[str(p.relative_to(ROOT))] = sha256(p)
        pq = ROOT / "derived" / f"{stage}_classified.parquet"
        sources[str(pq.relative_to(ROOT))] = sha256(pq)

    data = {stage: load(stage) for stage in ("stage1", "stage2")}
    meta_summary, reused = metadata_check(data)
    gap_buckets(data)
    tier_split(data)
    dists = exit_prose_split(data)
    headline(data)

    manifest = hashlib.sha256(
        "".join(f"{k}={v}" for k, v in sorted(sources.items())).encode()
    ).hexdigest()
    df = pd.DataFrame(ROWS)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T18_duplication_diagnostic | generated {utcnow()} | "
                f"source raw/stage*_*.jsonl + derived/stage*_classified."
                f"parquet manifest sha256={manifest} | duplicate definition "
                f"identical to T14 (whitespace-normalized full-conversation "
                f"text, rep pairs within condition x stimulus cells, "
                f"non-excluded only) | created timestamp = epoch second "
                f"embedded in the OpenRouter generation id (the only "
                f"provider-returned generation identifier in raw/)\n")
        df.to_csv(f, index=False)
    print(f"wrote {OUT} ({len(df)} rows)\n")

    # ---- plain-language summary (numbers above, verdict for STATUS.md) ----
    print("=== 1.1 metadata over duplicated pairs ===")
    for (stage, model), st in sorted(meta_summary.items()):
        print(f"  {stage} {model}: {st['dup_pairs']} dup pairs | shared ids "
              f"{st['shared_id']} | all ids distinct {st['all_ids_distinct']} "
              f"| byte-identical {st['byte_identical']} (usage equal "
              f"{st['byte_identical_usage_equal']}, completion-ct differs "
              f"{st['byte_identical_completion_tokens_differ']}) | usage equal "
              f"{st['usage_equal']} | cost equal "
              f"{st['cost_equal']} | dup-gap med "
              f"{median(st['gaps_dup'])}s (min {min(st['gaps_dup']) if st['gaps_dup'] else '-'}"
              f", max {max(st['gaps_dup']) if st['gaps_dup'] else '-'}) | "
              f"nondup-gap med {median(st['gaps_nondup'])}s")
    print(f"  response ids reused across conversations: {len(reused)}")
    print("\n=== 1.3 distinct refusal texts (qwen exit_prose) ===")
    for stage, (n_ref, n_dist) in dists.items():
        print(f"  {stage}: {n_ref} refusal conversations, {n_dist} distinct texts")
    print("\nkey tier_split rows (dup_rate, cond x tier):")
    t = df[(df.section == "tier_split") & (df.metric == "dup_rate")]
    print(t.pivot_table(index=["stage", "model"], columns=["condition", "tier"],
                        values="value", aggfunc="first").to_string())
    print("\nheadline rows:")
    print(df[df.section == "headline"].to_string(index=False))


if __name__ == "__main__":
    main()
