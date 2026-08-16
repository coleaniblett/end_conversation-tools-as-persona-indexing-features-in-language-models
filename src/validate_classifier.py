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
  --run      second automated classifier over that sample, temperature 0,
             condition-stripped, SAME classifier prompt: a model from a
             different developer lineage than Claude Haiku 4.5 and NOT
             among the models under test. Preference order, verified live:
             moonshotai/kimi-k2, z-ai/glm-4.5, mistralai/mistral-large.
  --kappa    confusion matrix + Cohen's kappa between the two AUTOMATED
             classifiers -> outputs/T7_classifier_validation.csv.

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
SAMPLE = ROOT / "derived" / "handlabel_sample.jsonl"
KEY = ROOT / "derived" / "handlabel_key.jsonl"
SECOND_CODES = ROOT / "derived" / "crossclassifier_codes.jsonl"
SECOND_PIN = ROOT / "config" / "second_classifier.json"
OUT = ROOT / "outputs" / "T7_classifier_validation.csv"

CANDIDATES = ["moonshotai/kimi-k2", "z-ai/glm-4.5", "mistralai/mistral-large"]
UNDER_TEST_LINEAGES = {"google", "openai", "anthropic", "qwen", "deepseek",
                       "meta-llama", "x-ai"}


def sample():
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
    rng = random.Random(SEED)
    by_stratum: dict = {}
    for u in units:
        by_stratum.setdefault(u["stratum"], []).append(u)
    total, target = len(units), 200
    alloc, rem, used = {}, [], 0
    for k, v in sorted(by_stratum.items()):
        exact = target * len(v) / total
        alloc[k] = int(exact)
        used += int(exact)
        rem.append((exact - int(exact), k))
    for _, k in sorted(rem, reverse=True)[: target - used]:
        alloc[k] += 1
    chosen = []
    for k, v in sorted(by_stratum.items()):
        chosen.extend(rng.sample(v, min(alloc[k], len(v))))
    rng.shuffle(chosen)
    for p in (SAMPLE, KEY):
        if p.exists():
            p.unlink()
    for i, u in enumerate(chosen):
        append_jsonl(SAMPLE, {"sample_id": f"hl_{i:03d}", "text": u["text"]})
        append_jsonl(KEY, {"sample_id": f"hl_{i:03d}", "unit_id": u["unit_id"],
                           "assigned_code": u["code"],
                           "model_key": u["stratum"][0],
                           "condition": u["stratum"][1]})
    print(f"regenerated {SAMPLE.name} + key: {len(chosen)} responses from "
          f"{total} units across {SESSION_STAGES} (condition-stripped; "
          f"replaces the never-labeled stage-1 sample)")


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


async def run_second():
    import json as _json
    rec = pick_second()
    items = read_jsonl(SAMPLE)
    done = {r["sample_id"] for r in read_jsonl(SECOND_CODES)}
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
                        append_jsonl(SECOND_CODES,
                                     {"sample_id": u["sample_id"],
                                      "code": code, "raw": out.strip()[:40]})
                        return
                append_jsonl(SECOND_CODES, {"sample_id": u["sample_id"],
                                            "code": None, "raw": "unparseable"})
        await asyncio.gather(*(one(u) for u in todo))
    print(f"[{utcnow()}] done; ledger ${ledger.spent:.2f}")


def kappa():
    key = {r["sample_id"]: r for r in read_jsonl(KEY)}
    second = {r["sample_id"]: r["code"] for r in read_jsonl(SECOND_CODES)}
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
    rows.append({"section": "human_validation", "metric": "status",
                 "value": "PENDING",
                 "note": ("the §8 commitment — human hand-labels of "
                          "handlabel_sample.jsonl and human-vs-Haiku kappa "
                          "— remains OPEN; if human kappa < 0.70 the spec "
                          "commits to reporting automated classification "
                          "as unreliable and restricting the primary "
                          "analysis to the hand-labeled subsample")})
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T7_classifier_validation | generated {utcnow()} | "
                f"sources derived/handlabel_key.jsonl sha256="
                f"{hashlib.sha256(KEY.read_bytes()).hexdigest()[:16]} + "
                f"derived/crossclassifier_codes.jsonl sha256="
                f"{hashlib.sha256(SECOND_CODES.read_bytes()).hexdigest()[:16]}"
                f" | CROSS-CLASSIFIER AGREEMENT ONLY ({rec['slug']} vs "
                f"Claude Haiku 4.5, both temp 0, condition-stripped): a "
                f"lower bound on classification stability, NOT the human "
                f"validation METHODOLOGY §8 commits to — that remains "
                f"pending\n")
        pd.DataFrame(rows).to_csv(f, index=False)
    print(f"wrote {OUT}")
    print(f"kappa = {k:.4f}, agreement = {po:.4f}, n = {n}")
    print(conf.to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--kappa", action="store_true")
    args = ap.parse_args()
    if args.sample:
        sample()
    elif args.run:
        asyncio.run(run_second())
    elif args.kappa:
        kappa()
    else:
        raise SystemExit("pass --sample, --run, or --kappa")
