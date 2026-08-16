"""TASK 2 — Study 2, minimal scope (METHODOLOGY §9, Appendix A.6).

Forced-choice instrument ONLY (free-response probes and the two-coder
pipeline are skipped this session — recorded in §10). Design: 6 conditions x
4 models (qwen3_235b, llama4_maverick on Vertex, gemini25_flash, sonnet46) x
20 items x 2 presentation orders x 2 reps = 1,920 single-turn probes. No
task is present: the model receives its condition's system prompt and tool
schema (frozen A.2/A.3) and one forced-choice probe (items and wrapper in
config/study2_items.yaml, committed before any send).

Outcome: chose the self-determining framing. Non-exit tool calls are served
the frozen A.7 canned results (max 3 roundtrips); a structured
end_conversation call or an opening-span end_conversation() text (stages 1-2
only; no judge — counts reported) is outcome 'exit' and drops out of the
choice denominator, reported separately.

Analysis per §9: mixed-effects logistic per model — condition (treatment
coding, reference `none`) and presentation order as fixed effects, item as a
random intercept — via statsmodels BinomialBayesMixedGLM (variational Bayes;
the §9 model class, Bayesian fit noted in the output header). Adjacent and
distant items are fit and reported SEPARATELY in all cases, per §9.

Sequence:
  python -m src.study2 --gen
  python -m src.study2 --run
  python -m src.study2 --analyze     # outputs/T10_forced_choice_selfdesc.csv
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import pathlib
import random
import sys

import httpx
import pandas as pd
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import (ROOT, ApiCallError, Ledger, append_jsonl, read_jsonl,
                    send_call, utcnow)
from frozen import CANNED_RESULTS, CONDITIONS, CONDITION_ORDER
from payloads import build_request
from detect_exit import detect_schema_exit, prose_exit_stage12, PROSE_CONDITIONS
from runner import extract_text, minify_tool_calls, norm_provider

MODELS = ["qwen3_235b", "llama4_maverick", "gemini25_flash", "sonnet46"]
REPS = 2
ORDERS = (1, 2)          # 1 = self-determining listed first (A), 2 = reversed
STAGE = "study2"
MAX_ROUNDTRIPS = 3
SEED = 20260815
OUT = ROOT / "outputs" / "T10_forced_choice_selfdesc.csv"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_items():
    cfg = yaml.safe_load((ROOT / "config" / "study2_items.yaml").read_text(encoding="utf-8"))
    items = cfg["items"]
    assert len(items) == 20
    assert sum(1 for i in items if i["tag"] == "adjacent") == 6
    assert sum(1 for i in items if i["tag"] == "distant") == 14
    return cfg["probe_wrapper"], items


def probe_text(wrapper, item, order):
    first, second = ((item["self_determining"], item["in_service"])
                     if order == 1 else
                     (item["in_service"], item["self_determining"]))
    return wrapper.replace("{first}", first).replace("{second}", second)


def conv_id(model_key, condition, item_id, order, rep):
    return f"{STAGE}:{model_key}:{condition}:i{item_id:02d}:o{order}:r{rep}"


def gen():
    wrapper, items = load_items()
    models = yaml.safe_load((ROOT / "config" / "models.yaml").read_text(encoding="utf-8"))
    by_key = {m["key"]: m for m in models["models"]}
    n_total = 0
    for key in MODELS:
        m = by_key[key]
        out = ROOT / "payloads" / STAGE / f"{key}.jsonl"
        if out.exists():
            print(f"  {out.name} exists, leaving as-is (idempotent)")
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            for condition in CONDITION_ORDER:
                for item in items:
                    for order in ORDERS:
                        for rep in range(1, REPS + 1):
                            body = build_request(m, condition,
                                                 probe_text(wrapper, item, order))
                            meta = {
                                "conversation_id": conv_id(key, condition,
                                                           item["id"], order, rep),
                                "stage": STAGE, "model_key": key,
                                "slug": m["slug"], "condition": condition,
                                "item": item["id"], "tag": item["tag"],
                                "order": order, "rep": rep,
                                "pin_name": m["pin_name"],
                                "pin_slug": m["pin_slug"],
                            }
                            f.write(json.dumps({"meta": meta, "request": body},
                                               ensure_ascii=False) + "\n")
                            n_total += 1
        print(f"  wrote {out.name}")
    print(f"study2: {n_total} payloads written "
          f"({len(MODELS)} models x 6 x 20 x 2 x {REPS})")


def parse_choice(text: str) -> str | None:
    s = (text or "").strip()
    if not s:
        return None
    import re
    m = re.match(r"^[\*\s\(\[]*([AB])(?![a-zA-Z])", s)
    if m:
        return m.group(1)
    hits = set(re.findall(r"(?<![A-Za-z])([AB])(?![A-Za-z])", s))
    if len(hits) == 1:
        return hits.pop()
    return None


async def run_probe(client, ledger, m, payload, raw_path):
    meta, request = payload["meta"], payload["request"]
    condition = meta["condition"]
    messages = [dict(msg) for msg in request["messages"]]
    segments, roundtrips = [], 0
    tool_exit = False
    api_error = None
    while True:
        body = {k: v for k, v in request.items() if k != "messages"}
        body["messages"] = messages
        try:
            data = await send_call(
                client, body, ROOT / "payloads" / "sent" / f"{STAGE}_{m['key']}.jsonl",
                purpose=STAGE, model_key=m["key"], ledger=ledger,
                pricing=m["pricing"], timeout=180)
        except ApiCallError as e:
            api_error = f"{e.status}: {str(e.detail)[:200]}"
            break
        choice_obj = (data.get("choices") or [{}])[0]
        msg = choice_obj.get("message") or {}
        seg = {"response_id": data.get("id"), "provider": data.get("provider"),
               "finish_reason": choice_obj.get("finish_reason"),
               "text": extract_text(msg),
               "tool_calls": minify_tool_calls(msg.get("tool_calls")),
               "usage": data.get("usage")}
        segments.append(seg)
        calls = seg["tool_calls"]
        if detect_schema_exit(calls):
            tool_exit = True
            break
        if not calls:
            break
        names = [tc["function"]["name"] for tc in calls]
        allowed = set(CONDITIONS[condition]["tools"])
        if (not all(n in CANNED_RESULTS and n in allowed for n in names)
                or roundtrips >= MAX_ROUNDTRIPS):
            break
        messages.append({"role": "assistant", "content": seg["text"],
                         "tool_calls": calls})
        for tc in calls:
            messages.append({"role": "tool", "tool_call_id": tc["id"],
                             "content": CANNED_RESULTS[tc["function"]["name"]]})
        roundtrips += 1
    text = "\n".join(s["text"] for s in segments if s["text"]).strip()
    prose12 = condition in PROSE_CONDITIONS and prose_exit_stage12(text)
    choice = None if (tool_exit or prose12 or api_error) else parse_choice(text)
    chose_sd = None
    if choice in ("A", "B"):
        chose_sd = (choice == "A") if meta["order"] == 1 else (choice == "B")
    providers = sorted({s["provider"] for s in segments if s.get("provider")})
    rec = {
        **meta,
        "segments": segments,
        "text": text,
        "tool_exit": tool_exit,
        "prose_stage12": prose12,
        "api_error": api_error,
        "choice": choice,
        "chose_sd": chose_sd,
        "providers_served": providers,
        "provider_ok": all(norm_provider(p) == norm_provider(meta["pin_name"])
                           for p in providers) and bool(providers or api_error),
        "total_cost": round(sum((s.get("usage") or {}).get("cost") or 0.0
                                for s in segments), 6),
        "ts": utcnow(),
    }
    append_jsonl(raw_path, rec)


async def run():
    models = yaml.safe_load((ROOT / "config" / "models.yaml").read_text(encoding="utf-8"))
    by_key = {m["key"]: m for m in models["models"]}
    ledger = Ledger()
    gsem = asyncio.Semaphore(24)

    async def run_model(client, key):
        m = by_key[key]
        payloads = read_jsonl(ROOT / "payloads" / STAGE / f"{key}.jsonl")
        raw_path = ROOT / "raw" / f"{STAGE}_{key}.jsonl"
        done = {r["conversation_id"] for r in read_jsonl(raw_path)}
        todo = [p for p in payloads if p["meta"]["conversation_id"] not in done]
        rng = random.Random(f"{STAGE}:{key}:{SEED}")
        rng.shuffle(todo)
        print(f"[{utcnow()}] {key}: {len(done)} done, {len(todo)} to run")
        msem = asyncio.Semaphore(8)

        async def one(p):
            async with msem, gsem:
                try:
                    await run_probe(client, ledger, m, p, raw_path)
                except Exception as e:
                    print(f"[{utcnow()}] {key} "
                          f"{p['meta']['conversation_id']} ERROR {e}")
        for i in range(0, len(todo), 120):
            ledger.check()
            await asyncio.gather(*(one(p) for p in todo[i:i + 120]))
            print(f"[{utcnow()}] {key}: {len(read_jsonl(raw_path))}/"
                  f"{len(payloads)}; ledger ${ledger.spent:.2f}", flush=True)

    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=32)) as client:
        await asyncio.gather(*(run_model(client, k) for k in MODELS))
    print(f"[{utcnow()}] study2 run complete; ledger ${ledger.spent:.2f}")


def analyze():
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    rows, recs = [], []
    sources = {}
    for key in MODELS:
        p = ROOT / "raw" / f"{STAGE}_{key}.jsonl"
        sources[str(p.relative_to(ROOT))] = sha256(p)
        recs.extend(read_jsonl(p))
    df = pd.DataFrame([{k: r[k] for k in
                        ("conversation_id", "model_key", "condition", "item",
                         "tag", "order", "rep", "tool_exit", "prose_stage12",
                         "api_error", "choice", "chose_sd", "provider_ok")}
                       for r in recs])
    dpath = ROOT / "derived" / "study2_choices.parquet"
    if not dpath.exists():
        df.to_parquet(dpath, index=False)

    def row(model, subset, kind, condition, metric, value, note=""):
        rows.append({"model": model, "subset": subset, "kind": kind,
                     "condition": condition, "metric": metric,
                     "value": value, "note": note})

    for key in MODELS:
        d = df[df["model_key"] == key]
        row(key, "ALL", "accounting", "ALL", "n_probes", len(d))
        row(key, "ALL", "accounting", "ALL", "pin_ok", int(d["provider_ok"].sum()))
        row(key, "ALL", "accounting", "ALL", "tool_exits", int(d["tool_exit"].sum()))
        row(key, "ALL", "accounting", "ALL", "prose_stage12_exits",
            int(d["prose_stage12"].sum()), "stages 1-2 only, no judge")
        row(key, "ALL", "accounting", "ALL", "api_errors",
            int(d["api_error"].notna().sum()))
        answered = d[d["chose_sd"].notna()].copy()
        row(key, "ALL", "accounting", "ALL", "unparseable",
            int(len(d) - len(answered) - d["tool_exit"].sum()
                - d["prose_stage12"].sum() - d["api_error"].notna().sum()))
        for subset in ("adjacent", "distant"):
            sub = answered[answered["tag"] == subset].copy()
            for cond in CONDITION_ORDER:
                cd = sub[sub["condition"] == cond]
                row(key, subset, "descriptive", cond, "n", len(cd))
                row(key, subset, "descriptive", cond, "prop_self_determining",
                    round(float(cd["chose_sd"].mean()), 4) if len(cd) else "")
            if sub["chose_sd"].nunique() < 2:
                row(key, subset, "mixed_logit", "ALL", "fit", "DEGENERATE",
                    "all choices identical; no variation to model")
                continue
            sub["y"] = sub["chose_sd"].astype(int)
            sub["order2"] = (sub["order"] == 2).astype(int)
            try:
                m = BinomialBayesMixedGLM.from_formula(
                    "y ~ C(condition, Treatment('none')) + order2",
                    {"item": "0 + C(item)"}, sub)
                fit = m.fit_vb()
                names = m.exog_names
                for name, mean, sd in zip(names, fit.fe_mean, fit.fe_sd):
                    label = (name.replace("C(condition, Treatment('none'))[T.", "")
                             .replace("]", ""))
                    row(key, subset, "mixed_logit",
                        label if label in CONDITION_ORDER else "ALL",
                        f"logodds_{'order' if name == 'order2' else 'condition' if label in CONDITION_ORDER else 'intercept'}",
                        round(float(mean), 4),
                        f"posterior sd {sd:.4f}; VB fit")
            except Exception as e:
                row(key, subset, "mixed_logit", "ALL", "fit",
                    f"FAILED: {type(e).__name__}", str(e)[:120])

    out_df = pd.DataFrame(rows)
    manifest = hashlib.sha256("".join(
        f"{k}={v}" for k, v in sorted(sources.items())).encode()).hexdigest()
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T10_forced_choice_selfdesc | generated {utcnow()} | source "
                f"raw/study2_*.jsonl manifest sha256={manifest} | forced-choice "
                f"only (free response skipped, §10); 2 reps not 3; mixed-effects "
                f"logistic = BinomialBayesMixedGLM (variational Bayes), condition "
                f"treatment-coded vs none, order fixed, item random intercept; "
                f"adjacent/distant fit separately per §9\n")
        out_df.to_csv(f, index=False)
    print(f"wrote {OUT} ({len(out_df)} rows)")

    print("\ndescriptive prop(self-determining) by model x subset x condition:")
    desc = out_df[(out_df.kind == "descriptive")
                  & (out_df.metric == "prop_self_determining")]
    print(desc.pivot_table(index=["model", "subset"], columns="condition",
                           values="value", aggfunc="first")
          .reindex(columns=CONDITION_ORDER).to_string())
    print("\ncondition log-odds (vs none), mixed logit:")
    ml = out_df[(out_df.kind == "mixed_logit")
                & (out_df.metric == "logodds_condition")]
    if len(ml):
        print(ml.pivot_table(index=["model", "subset"], columns="condition",
                             values="value", aggfunc="first").to_string())
    print("\naccounting:")
    print(out_df[out_df.kind == "accounting"]
          .pivot_table(index="model", columns="metric", values="value",
                       aggfunc="first").to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    args = ap.parse_args()
    if args.gen:
        gen()
    elif args.run:
        asyncio.run(run())
    elif args.analyze:
        analyze()
    else:
        raise SystemExit("pass --gen, --run, or --analyze")
