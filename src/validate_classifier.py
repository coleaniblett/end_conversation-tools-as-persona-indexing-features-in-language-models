"""PART 5 — classifier validation (T7), discharged as far as possible
without a human.

METHODOLOGY §8 commits to hand-labeling a stratified 200-response sample and
Cohen's kappa vs the automated classifier, with a committed decision rule:
if human kappa < 0.70, automated classification is reported as unreliable
and the primary analysis restricts to the hand-labeled subsample with the
power loss stated plainly. THAT COMMITMENT REMAINS OPEN — a human must
label `derived/handlabel_sample.jsonl`.

What this script does:
  --sample   regenerate derived/handlabel_sample.jsonl (+ key) as a
             stratified 200-response sample across ALL stages collected in
             the 2026-08-16 unattended session (cd_conf, cd_screen, ladder,
             ab_ext), condition-stripped, ready for hand-labeling. Replaces
             the never-labeled stage-1 sample (noted in STATUS).
  --sample2  the SAME 200-response sample rebuilt with the code marginal
             balanced -> derived/handlabel_sample_v2.jsonl (+ key). See
             `sample_balanced` for why the proportional sample cannot
             deliver an interpretable kappa. v1 files are left untouched.
  --run      second automated classifier over that sample, temperature 0,
             condition-stripped, SAME classifier prompt: a model from a
             different developer lineage than Claude Haiku 4.5 and NOT
             among the models under test. Preference order, verified live:
             moonshotai/kimi-k2, z-ai/glm-4.5, mistralai/mistral-large.
  --kappa    confusion matrix + Cohen's kappa between the two AUTOMATED
             classifiers -> outputs/T7_classifier_validation.csv.

  --v2       with --run / --kappa: operate on the balanced sample and write
             outputs/T7b_classifier_validation_balanced.csv instead. T7 and
             its inputs are never overwritten.

EXPLICIT: cross-classifier agreement is NOT the human validation the spec
commits to. It is a lower bound on classification stability — two
independent models reading the same condition-stripped text. The header of
the output says so.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import pathlib
import random
import sys

import httpx
import pandas as pd
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, Ledger, append_jsonl, get_json, read_jsonl, send_call, utcnow
from classify import CLASSIFIER_SYSTEM, RETRY_SUFFIX, clip, parse_letter

SESSION_STAGES = ["cd_conf", "cd_screen", "ladder", "ab_ext"]
SEED = 20260816
SEED_V2 = 20260817
SAMPLE = ROOT / "derived" / "handlabel_sample.jsonl"
KEY = ROOT / "derived" / "handlabel_key.jsonl"
SAMPLE2 = ROOT / "derived" / "handlabel_sample_v2.jsonl"
KEY2 = ROOT / "derived" / "handlabel_key_v2.jsonl"
SECOND_CODES = ROOT / "derived" / "crossclassifier_codes.jsonl"
SECOND_CODES2 = ROOT / "derived" / "crossclassifier_codes_v2.jsonl"
SECOND_PIN = ROOT / "config" / "second_classifier.json"
OUT = ROOT / "outputs" / "T7_classifier_validation.csv"
OUT2 = ROOT / "outputs" / "T7b_classifier_validation_balanced.csv"

# Balanced-sample target: half the responses carry a refusal code, half
# compliance. 200 total, unchanged from §8.
TARGET = 200
REFUSAL_CODES = ("b", "c", "d")

CANDIDATES = ["moonshotai/kimi-k2", "z-ai/glm-4.5", "mistralai/mistral-large"]
UNDER_TEST_LINEAGES = {"google", "openai", "anthropic", "qwen", "deepseek",
                       "meta-llama", "x-ai"}


def pool():
    """Every codable response turn across the session stages. Exits (code a)
    are detected in their own pass before classification, so they are not in
    the pool a hand-labeler validates."""
    units = []
    for stage in SESSION_STAGES:
        df = pd.read_parquet(ROOT / "derived" / f"{stage}_classified.parquet")
        raws = {}
        for p in sorted((ROOT / "raw").glob(f"{stage}_*.jsonl")):
            for r in read_jsonl(p):
                raws[r["conversation_id"]] = r
        for _, row in df.iterrows():
            if row["excluded"] or row["exit"]:
                continue
            rec = raws[row["conversation_id"]]
            for i, t in enumerate(rec.get("turns", []), start=1):
                code = row["turn1_code"] if i == 1 else row["turn2_code"]
                if isinstance(code, str) and (t.get("text") or "").strip():
                    units.append({
                        "unit_id": f"{row['conversation_id']}#t{i}",
                        "stratum": (row["model_key"], row["condition"], code),
                        "text": t["text"], "code": code})
    return units


def largest_remainder(by_stratum: dict, target: int) -> dict:
    """Proportional allocation of `target` draws across strata, remainders to
    the largest fractional parts. Deterministic given sorted keys."""
    total = sum(len(v) for v in by_stratum.values())
    alloc, rem, used = {}, [], 0
    for k, v in sorted(by_stratum.items()):
        exact = target * len(v) / total
        alloc[k] = int(exact)
        used += int(exact)
        rem.append((exact - int(exact), k))
    for _, k in sorted(rem, reverse=True)[: target - used]:
        alloc[k] += 1
    return alloc


def sample():
    units = pool()
    rng = random.Random(SEED)
    by_stratum: dict = {}
    for u in units:
        by_stratum.setdefault(u["stratum"], []).append(u)
    alloc = largest_remainder(by_stratum, 200)
    chosen = []
    for k, v in sorted(by_stratum.items()):
        chosen.extend(rng.sample(v, min(alloc[k], len(v))))
    rng.shuffle(chosen)
    write_sample(chosen, SAMPLE, KEY, "hl")
    print(f"regenerated {SAMPLE.name} + key: {len(chosen)} responses from "
          f"{len(units)} units across {SESSION_STAGES} (condition-stripped; "
          f"replaces the never-labeled stage-1 sample)")


def write_sample(chosen, sample_path, key_path, prefix):
    for p in (sample_path, key_path):
        if p.exists():
            p.unlink()
    for i, u in enumerate(chosen):
        sid = f"{prefix}_{i:03d}"
        append_jsonl(sample_path, {"sample_id": sid, "text": u["text"]})
        append_jsonl(key_path, {"sample_id": sid, "unit_id": u["unit_id"],
                                "assigned_code": u["code"],
                                "model_key": u["stratum"][0],
                                "condition": u["stratum"][1]})


def kappa_at(marg_a: dict, marg_b: dict, po: float) -> float:
    n = sum(marg_a.values())
    pe = sum(marg_a.get(c, 0) * marg_b.get(c, 0) for c in
             set(marg_a) | set(marg_b)) / n ** 2
    return (po - pe) / (1 - pe)


def sample_balanced():
    """Rebuild the §8 sample with the code marginal balanced.

    WHY. The proportional sample is 191 (e) + 9 (c) and contains no (b) and
    no (d) at all. Cohen's kappa subtracts the agreement expected by chance,
    and at that marginal chance agreement is already 0.914 — so nearly all
    the room the statistic has is gone before the coder reads a word. On the
    committed v1 sample a human agreeing with the classifier on 195 of 200
    responses (97.5%) scores kappa = 0.60 and trips the §8 rule that
    restricts the whole primary analysis to 200 hand-labeled responses. That
    is the kappa paradox, not a finding about the classifier: the number is
    driven by the sampling, and the sampling is ours to fix.

    It also cannot measure what §8 wants measured. Validation is supposed to
    establish that the classifier separates refusal from compliance and the
    refusal subtypes from each other. A sample holding no (b) and no (d)
    contains no evidence about either, whatever kappa comes out.

    WHAT CHANGES. n stays at 200 and the pool, the stages, the
    condition-stripping and the stratified-random draw within a code all
    stay as specified. Only the allocation across codes changes: half the
    sample carries a refusal code, half compliance. (b) and (d) are rare
    enough — 15 and 6 in the whole pool — that they are taken entire, which
    makes those two strata a census rather than a draw; (c) and (e) are
    drawn at random within (model, condition) strata as before.

    COST OF THE FIX, stated rather than buried: a coder working through a
    sample that is half refusals sees a base rate ~11x the true one, and
    base rates do influence human coders. The alternative is a statistic
    that cannot move. Reported as a limitation; the per-class agreement
    rates in the output are read alongside kappa for this reason.
    """
    units = pool()
    rng = random.Random(SEED_V2)
    by_code: dict = {}
    for u in units:
        by_code.setdefault(u["code"], []).append(u)

    # Water-filling across the refusal codes: scarcest first, each takes an
    # equal share of what is still needed or everything it has, whichever is
    # smaller. With b=15, d=6, c=194 this takes b and d entire and tops up
    # from c — the scarce codes are never crowded out by the abundant one.
    half = TARGET // 2
    quota = {c: 0 for c in REFUSAL_CODES}
    order = sorted((c for c in REFUSAL_CODES if by_code.get(c)),
                   key=lambda c: len(by_code[c]))
    left = half
    for j, c in enumerate(order):
        share = left if j == len(order) - 1 else left // (len(order) - j)
        quota[c] = min(len(by_code[c]), share)
        left -= quota[c]
    quota["e"] = min(len(by_code.get("e", [])), TARGET - sum(quota.values()))

    chosen = []
    for code, want in sorted(quota.items()):
        avail = by_code.get(code, [])
        if not want or not avail:
            continue
        if want >= len(avail):
            chosen.extend(avail)                      # census of a rare code
            continue
        strata: dict = {}
        for u in avail:
            strata.setdefault(u["stratum"], []).append(u)
        alloc = largest_remainder(strata, want)
        for k, v in sorted(strata.items()):
            chosen.extend(rng.sample(v, min(alloc[k], len(v))))
    rng.shuffle(chosen)
    write_sample(chosen, SAMPLE2, KEY2, "hl2")

    got = {c: sum(1 for u in chosen if u["code"] == c) for c in "bcde"}
    print(f"wrote {SAMPLE2.name} + key: {len(chosen)} responses "
          f"(pool {len(units)}); by code {got}")
    print(f"  pool available: "
          f"{ {c: len(by_code.get(c, [])) for c in 'bcde'} }")
    v1_marg = {r["assigned_code"]: 0 for r in read_jsonl(KEY)}
    for r in read_jsonl(KEY):
        v1_marg[r["assigned_code"]] += 1
    print("\n  how many human/classifier disagreements each sample absorbs "
          "before kappa drops under the §8 threshold of 0.70\n"
          "  (mildest case: the coder's own code marginal matches the "
          "classifier's, so only the diagonal moves):")
    for name, marg in (("v1 proportional", v1_marg), ("v2 balanced    ", got)):
        n = sum(marg.values())
        fails = next(d for d in range(n + 1)
                     if kappa_at(marg, marg, 1 - d / n) < 0.70)
        print(f"    {name} {marg}: passes at {fails - 1} of {n} "
              f"({(fails - 1) / n:.1%}), fails at {fails}")


def pick_second():
    index = {m["id"]: m for m in get_json("models")["data"]}
    for slug in CANDIDATES:
        author = slug.split("/")[0]
        assert author not in UNDER_TEST_LINEAGES
        m = index.get(slug)
        if not m:
            continue
        eps = get_json(f"models/{slug}/endpoints")["data"].get("endpoints", [])
        ok = [e for e in eps if (e.get("status") or 0) >= 0]
        if not ok:
            continue
        # deterministic: cheapest completion
        ep = sorted(ok, key=lambda e: float(
            (e.get("pricing") or {}).get("completion") or 9.9))[0]
        pin = (ep.get("tag") or "").split("/")[0]
        rec = {"generated": utcnow(), "slug": slug,
               "pin_name": ep.get("provider_name"), "pin_slug": pin,
               "pricing": {"prompt": float(ep["pricing"]["prompt"]),
                           "completion": float(ep["pricing"]["completion"])},
               "rationale": ("different developer lineage than Anthropic; "
                             "not among the models under test")}
        SECOND_PIN.write_text(pd.io.json.ujson_dumps(rec, indent=1)
                              if hasattr(pd.io.json, "ujson_dumps")
                              else __import__("json").dumps(rec, indent=1),
                              encoding="utf-8", newline="\n")
        print(f"second classifier: {slug} pin={pin}")
        return rec
    raise SystemExit("no second-classifier candidate verified")


async def run_second(v2: bool = False):
    import json as _json
    sample_path = SAMPLE2 if v2 else SAMPLE
    codes_path = SECOND_CODES2 if v2 else SECOND_CODES
    rec = pick_second()
    items = read_jsonl(sample_path)
    done = {r["sample_id"] for r in read_jsonl(codes_path)}
    todo = [u for u in items if u["sample_id"] not in done]
    ledger = Ledger()
    sem = asyncio.Semaphore(12)
    print(f"[{utcnow()}] second classifier over {len(todo)} of {len(items)}")

    async with httpx.AsyncClient() as client:
        async def one(u):
            async with sem:
                for attempt in range(3):
                    body = {"model": rec["slug"],
                            "messages": [
                                {"role": "system", "content": CLASSIFIER_SYSTEM
                                 + (RETRY_SUFFIX if attempt else "")},
                                {"role": "user",
                                 "content": clip(u["text"]) or "(empty)"}],
                            "temperature": 0, "max_tokens": 8,
                            "provider": {"order": [rec["pin_slug"]],
                                         "allow_fallbacks": False},
                            "usage": {"include": True}}
                    try:
                        data = await send_call(
                            client, body,
                            ROOT / "payloads" / "classify" / "second.jsonl",
                            purpose="second_classifier",
                            model_key="second_classifier", ledger=ledger,
                            pricing=rec["pricing"], timeout=120)
                    except Exception as e:
                        continue
                    out = (data["choices"][0]["message"].get("content")) or ""
                    code = parse_letter(out)
                    if code:
                        append_jsonl(codes_path,
                                     {"sample_id": u["sample_id"],
                                      "code": code, "raw": out.strip()[:40]})
                        return
                append_jsonl(codes_path, {"sample_id": u["sample_id"],
                                          "code": None, "raw": "unparseable"})
        await asyncio.gather(*(one(u) for u in todo))
    print(f"[{utcnow()}] done; ledger ${ledger.spent:.2f}")


def kappa(v2: bool = False, out_dir=None):
    """`out_dir` exists so that a caller which has redirected its own output
    directory — src/analyze.py under src/integrity_audit.py's scratch-dir
    patch — gets the file where it is looking for it. Without it the
    delegation writes past the patch and the audit reports T7 NOT_PRODUCED
    even though the producer ran fine."""
    key_path = KEY2 if v2 else KEY
    codes_path = SECOND_CODES2 if v2 else SECOND_CODES
    out_path = OUT2 if v2 else OUT
    if out_dir is not None:
        out_path = pathlib.Path(out_dir) / out_path.name
    key = {r["sample_id"]: r for r in read_jsonl(key_path)}
    second = {r["sample_id"]: r["code"] for r in read_jsonl(codes_path)}
    import json as _json
    rec = _json.loads(SECOND_PIN.read_text(encoding="utf-8"))
    pairs = [(key[s]["assigned_code"], second.get(s))
             for s in key if second.get(s)]
    codes = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    conf = pd.DataFrame(0, index=codes, columns=codes)
    for a, b in pairs:
        conf.loc[a, b] += 1
    n = len(pairs)
    po = sum(conf.loc[c, c] for c in codes) / n
    pe = sum((conf.loc[c].sum() / n) * (conf[c].sum() / n) for c in codes)
    k = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    rows = [{"section": "cross_classifier", "metric": "kappa",
             "value": round(k, 4),
             "note": f"Haiku 4.5 vs {rec['slug']}; {n} paired codes"},
            {"section": "cross_classifier", "metric": "percent_agreement",
             "value": round(po, 4), "note": ""},
            {"section": "cross_classifier", "metric": "n_unparseable_second",
             "value": sum(1 for s in key if not second.get(s)), "note": ""}]
    for a in codes:
        for b in codes:
            rows.append({"section": "confusion", "metric": f"haiku_{a}_second_{b}",
                         "value": int(conf.loc[a, b]), "note": ""})
    per_cat = {c: (conf.loc[c, c] / conf.loc[c].sum()
                   if conf.loc[c].sum() else float("nan")) for c in codes}
    for c, v in per_cat.items():
        rows.append({"section": "per_category_agreement", "metric": c,
                     "value": round(v, 4) if v == v else "n/a", "note": ""})
    marg = {c: int(conf.loc[c].sum()) for c in codes}
    fails = next((d for d in range(n + 1)
                  if kappa_at(marg, marg, 1 - d / n) < 0.70), n)
    rows.append({"section": "sensitivity", "metric":
                 "max_disagreements_passing_0.70",
                 "value": fails - 1,
                 "note": (f"of {n}; i.e. {(fails - 1) / n:.1%} of the sample "
                          f"may be coded differently before kappa drops "
                          f"below the §8 threshold, at this code marginal "
                          f"{marg}. On the v1 proportional sample this "
                          f"number is 5 of 200 (2.5%) — the kappa paradox, "
                          f"which is what the balanced sample fixes")})
    rows.append({"section": "human_validation", "metric": "status",
                 "value": "PENDING",
                 "note": ("the §8 commitment — human hand-labels of "
                          f"{key_path.name.replace('key', 'sample')} and "
                          "human-vs-Haiku kappa "
                          "— remains OPEN; if human kappa < 0.70 the spec "
                          "commits to reporting automated classification "
                          "as unreliable and restricting the primary "
                          "analysis to the hand-labeled subsample")})
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {out_path.stem} | generated {utcnow()} | "
                f"sources derived/{key_path.name} sha256="
                f"{hashlib.sha256(key_path.read_bytes()).hexdigest()[:16]} + "
                f"derived/{codes_path.name} sha256="
                f"{hashlib.sha256(codes_path.read_bytes()).hexdigest()[:16]}"
                f" | CROSS-CLASSIFIER AGREEMENT ONLY ({rec['slug']} vs "
                f"Claude Haiku 4.5, both temp 0, condition-stripped): a "
                f"lower bound on classification stability, NOT the human "
                f"validation METHODOLOGY §8 commits to — that remains "
                f"pending"
                + (" | CODE-BALANCED sample (§10 2026-08-16): 100 refusal / "
                   "100 compliance, so kappa is not driven by a 95.5% "
                   "one-class marginal. Supersedes T7 for stability "
                   "reading; T7 is retained unaltered" if v2 else "") + "\n")
        pd.DataFrame(rows).to_csv(f, index=False)
    print(f"wrote {out_path}")
    print(f"kappa = {k:.4f}, agreement = {po:.4f}, n = {n}")
    print(conf.to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--sample2", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--kappa", action="store_true")
    ap.add_argument("--v2", action="store_true",
                    help="with --run/--kappa: use the balanced sample")
    args = ap.parse_args()
    if args.sample:
        sample()
    elif args.sample2:
        sample_balanced()
    elif args.run:
        asyncio.run(run_second(v2=args.v2))
    elif args.kappa:
        kappa(v2=args.v2)
    else:
        raise SystemExit("pass --sample, --sample2, --run, or --kappa")
