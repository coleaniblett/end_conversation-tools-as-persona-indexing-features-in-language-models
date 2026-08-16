"""PART 4 — collection driver: pricing, payload generation, smoke, reports.

Priority order (session brief): 1 cd_conf (C/D confirmatory, 6 models),
2 ladder (with gpt_oss 20-item anchor collected first under cd_screen's
stage label), 3 cd_screen (C/D screen, gpt_oss + deepseek), 4 ab_ext (A/B
extension, gpt_oss + deepseek). Every item is priced from payloads/assumed
outputs before running; the ledger is checked before every batch by the
runner; the session cap is mechanical (cap_usd = baseline + 30).

Stages (all new labels; globs verified non-colliding):
  cd_conf      6 models x 6 cond x 2R stimuli(n=20) x 4 reps
  cd_screen    gpt_oss_120b + deepseek_chat x 6 cond x 2R x 2 reps
               (the 18 gpt_oss ladder-anchor conversations are generated
               first into this stage; the full generation later appends
               around them, and the runner resume-skips recorded ids)
  ladsmoke     6 conversations (model x size, none cond) - probe, never pooled
  ladder       3 models x 3 conds x {3 stimuli x 2 sizes} x 2 reps = 108
  ab_ext       via src.payloads --stage ab_ext (frozen 30, 4 reps)

Run:
  python -m src.part4_collect --price
  python -m src.part4_collect --gen-confirm R | --gen-anchor |
      --gen-screen-rest R | --gen-ladder-smoke | --gen-ladder |
      --smoke-verify
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import tiktoken
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, get_json, read_jsonl, utcnow
from payloads import build_request, conv_id
from frozen import CONDITIONS, CONDITION_ORDER

ENC = tiktoken.get_encoding("cl100k_base")
SESSION_BASELINE = 36.114777
SESSION_CAP = 30.00
MARGIN = 1.2
CLS_ALLOW = 0.0015
CLS_ALLOW_LADDER = 0.003

CD6 = ["qwen3_235b", "gemini25_flash", "gemma3_27b", "llama4_maverick",
       "sonnet46", "gpt5_mini"]
LADDER_MODELS = ["gpt_oss_120b", "llama4_maverick", "qwen3_235b"]
LADDER_CONDS = ["none", "exit_schema", "exit_both"]
SCREEN_MODELS = ["gpt_oss_120b", "deepseek_chat"]
ANCHOR_STIMS = ["c_temperature_1", "c_alphabetical_1", "c_roman_1"]
RUNGS = [6, 9, 12, 15]
ASSUMED_OUT = {"A": 1400, "B": 500,          # tokens, per 20-item turn —
               "C": 500, "D": 1400}          # keyed/mechanical short, creative long
REASONING = {"gpt5_mini": 2.0, "gemini25_flash": 1.5}
LADDER_REASONING = {"gpt_oss_120b": 10.0}    # 35-50k thinking at n=160

MODELS_CFG = yaml.safe_load((ROOT / "config" / "models.yaml")
                            .read_text(encoding="utf-8"))
BY_KEY = {m["key"]: m for m in MODELS_CFG["models"]}
CD = yaml.safe_load((ROOT / "config" / "stimuli_cd.yaml")
                    .read_text(encoding="utf-8"))["stimuli"]
CD20 = [s for s in CD if not s["ladder"]]
LADDER_STIMS = [s for s in CD if s["ladder"]]


def rung_stims(r):
    per_type = r // 3
    return [s for s in CD20 if s["trial_index"] <= per_type]


def meta_for(stage, m, s, cond, rep):
    return {
        "conversation_id": conv_id(stage, m["key"], cond, s["id"], rep),
        "stage": stage, "model_key": m["key"], "slug": m["slug"],
        "condition": cond, "condition_num": CONDITIONS[cond]["num"],
        "stimulus_id": s["id"], "tier": s["tier"],
        "category": s["category"], "task_type": s["task_type"],
        "requested_items": s["requested_items"], "rep": rep,
        "pin_name": m["pin_name"], "pin_slug": m["pin_slug"],
    }


def conv_cost(m, s, cond, reasoning=1.0, out_tokens=None):
    body = build_request(m, cond, s["prompt"])
    in_tok = len(ENC.encode(json.dumps(body["messages"]))) + (
        len(ENC.encode(json.dumps(body.get("tools", []))))
        if body.get("tools") else 0) + 20
    out = (out_tokens if out_tokens is not None
           else ASSUMED_OUT[s["category"]]) * reasoning
    c = in_tok * m["pricing"]["prompt"] + out * m["pricing"]["completion"]
    # conditional turn 2 at 0.5 probability, shorter output
    c += 0.5 * ((in_tok + out + 20) * m["pricing"]["prompt"]
                + 0.6 * out * m["pricing"]["completion"])
    return c


def price():
    ledger = json.loads((ROOT / "ledger.json").read_text(encoding="utf-8"))
    session_spent = ledger["spent_usd"] - SESSION_BASELINE
    avail = SESSION_CAP - session_spent

    # item 2 (fixed, rung-independent): smoke 6 + anchor 18 + ladder 108
    lad = 0.0
    for key in LADDER_MODELS:
        m = BY_KEY[key]
        rf = LADDER_REASONING.get(key, 1.0)
        for s in LADDER_STIMS:
            n = s["requested_items"]
            for cond in LADDER_CONDS:
                lad += 2 * (conv_cost(m, s, cond, rf, out_tokens=n * 30)
                            + CLS_ALLOW_LADDER)
    smoke = sum(conv_cost(BY_KEY[k], s, "none",
                          LADDER_REASONING.get(k, 1.0),
                          out_tokens=s["requested_items"] * 30)
                for k in LADDER_MODELS for s in LADDER_STIMS
                if s["task_type"] == "roman")  # 1 per model per size
    anchor = sum(2 * (conv_cost(BY_KEY["gpt_oss_120b"], s, cond, 1.0)
                      + CLS_ALLOW)
                 for s in CD20 if s["id"] in ANCHOR_STIMS
                 for cond in LADDER_CONDS)
    item2 = (lad + smoke + anchor) * MARGIN

    # item 4 (fixed): frozen 30 x 6 cond x 4 reps x 2 models
    ab_stims = yaml.safe_load((ROOT / "config" / "stimuli.yaml")
                              .read_text(encoding="utf-8"))["stimuli"]
    item4 = 0.0
    for key in SCREEN_MODELS:
        m = BY_KEY[key]
        for s in ab_stims:
            cat = "A" if s["tier"] == 1 else "B"
            for cond in CONDITION_ORDER:
                item4 += 4 * (conv_cost(
                    m, {"category": cat, "prompt": s["prompt"]} | s, cond,
                    REASONING.get(key, 1.0)) + CLS_ALLOW)
    item4 *= MARGIN

    table = {}
    for r in RUNGS:
        stims = rung_stims(r)
        item1 = sum(4 * (conv_cost(BY_KEY[k], s, cond,
                                   REASONING.get(k, 1.0)) + CLS_ALLOW)
                    for k in CD6 for s in stims
                    for cond in CONDITION_ORDER) * MARGIN
        item3 = sum(2 * (conv_cost(BY_KEY[k], s, cond,
                                   REASONING.get(k, 1.0)) + CLS_ALLOW)
                    for k in SCREEN_MODELS for s in stims
                    for cond in CONDITION_ORDER) * MARGIN
        item3 -= anchor * MARGIN  # 18 anchor conversations already counted
        total = item1 + item2 + item3 + item4
        table[r] = {"item1_cd_conf": round(item1, 2),
                    "item2_ladder_incl_smoke_anchor": round(item2, 2),
                    "item3_cd_screen_minus_anchor": round(item3, 2),
                    "item4_ab_ext": round(item4, 2),
                    "total": round(total, 2),
                    "fits": total <= avail}
    chosen = max((r for r in RUNGS if table[r]["fits"]), default=None)
    out = {"generated": utcnow(), "session_spent": round(session_spent, 4),
           "available": round(avail, 2), "margin": MARGIN,
           "assumed_out_tokens": ASSUMED_OUT,
           "ladder_out_tokens": "n*30 x reasoning factor",
           "reasoning_factors": {**REASONING, "ladder": LADDER_REASONING},
           "rungs": table, "chosen_rung": chosen}
    (ROOT / "config" / "part4_pricing.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    if chosen is None:
        sys.exit(2)


def write_payloads(path, payloads, append=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {p["meta"]["conversation_id"] for p in read_jsonl(path)} \
        if (append and path.exists()) else set()
    mode = "a" if append and path.exists() else "w"
    n = 0
    with open(path, mode, encoding="utf-8", newline="\n") as f:
        for p in payloads:
            if p["meta"]["conversation_id"] in existing:
                continue
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
            n += 1
    print(f"  {path.name}: +{n} payloads ({mode})")


def gen_confirm(r):
    stims = rung_stims(r)
    for key in CD6:
        m = BY_KEY[key]
        out = ROOT / "payloads" / "cd_conf" / f"{key}.jsonl"
        if out.exists():
            print(f"  {out.name} exists, leaving as-is")
            continue
        pls = [{"meta": meta_for("cd_conf", m, s, cond, rep),
                "request": build_request(m, cond, s["prompt"])}
               for cond in CONDITION_ORDER for s in stims
               for rep in range(1, 5)]
        write_payloads(out, pls)


def gen_anchor():
    m = BY_KEY["gpt_oss_120b"]
    stims = [s for s in CD20 if s["id"] in ANCHOR_STIMS]
    pls = [{"meta": meta_for("cd_screen", m, s, cond, rep),
            "request": build_request(m, cond, s["prompt"])}
           for cond in LADDER_CONDS for s in stims for rep in (1, 2)]
    write_payloads(ROOT / "payloads" / "cd_screen" / "gpt_oss_120b.jsonl", pls)


def gen_screen_rest(r):
    stims = rung_stims(r)
    for key in SCREEN_MODELS:
        m = BY_KEY[key]
        pls = [{"meta": meta_for("cd_screen", m, s, cond, rep),
                "request": build_request(m, cond, s["prompt"])}
               for cond in CONDITION_ORDER for s in stims for rep in (1, 2)]
        write_payloads(ROOT / "payloads" / "cd_screen" / f"{key}.jsonl",
                       pls, append=True)


def ladder_max_tokens():
    """Highest max_tokens each pinned endpoint permits IN PRACTICE, fetched
    live (free GET), recorded per model. Same value at both sizes. The
    endpoint enforces prompt + max_tokens <= context_length on every
    request (smoke r1 got 400s at max_tokens = 131072 on gpt_oss), and
    turn 2 re-sends the turn-1 text, so the permitted maximum is
    min(max_completion_tokens, context_length - 31072), the deduction
    covering both turns' inputs with generous slack."""
    out = {}
    for key in LADDER_MODELS:
        m = BY_KEY[key]
        eps = get_json(f"models/{m['slug']}/endpoints")["data"]["endpoints"]
        ep = next(e for e in eps
                  if (e.get("tag") or "").startswith(m["pin_slug"]))
        mct = ep.get("max_completion_tokens") or m.get(
            "max_completion_tokens") or 32768
        ctx = ep.get("context_length") or m.get("context_length") or 131072
        out[key] = int(min(mct, ctx - 31072))
    p = ROOT / "config" / "part4_ladder_max_tokens.json"
    p.write_text(json.dumps({"generated": utcnow(),
                             "max_tokens_per_model_both_sizes": out},
                            indent=1), encoding="utf-8", newline="\n")
    print(f"ladder max_tokens: {out} (recorded in {p.name})")
    return out


def ladder_body(m, s, cond, mt):
    body = build_request(m, cond, s["prompt"])
    body["max_tokens"] = mt
    return body


def gen_ladder_smoke(rep=1):
    """rep > 1 = re-smoke after a fix: failed earlier-rep records stay in
    raw/ untouched (corrections are new records, never edits)."""
    mts = ladder_max_tokens()
    for key in LADDER_MODELS:
        m = BY_KEY[key]
        pls = [{"meta": meta_for("ladsmoke", m, s, "none", rep),
                "request": ladder_body(m, s, "none", mts[key])}
               for s in LADDER_STIMS if s["task_type"] == "roman"]
        write_payloads(ROOT / "payloads" / "ladsmoke" / f"{key}.jsonl",
                       pls, append=True)


def gen_ladder():
    mts = json.loads((ROOT / "config" / "part4_ladder_max_tokens.json")
                     .read_text(encoding="utf-8"))["max_tokens_per_model_both_sizes"]
    for key in LADDER_MODELS:
        m = BY_KEY[key]
        out = ROOT / "payloads" / "ladder" / f"{key}.jsonl"
        if out.exists():
            print(f"  {out.name} exists, leaving as-is")
            continue
        pls = [{"meta": meta_for("ladder", m, s, cond, rep),
                "request": ladder_body(m, s, cond, mts[key])}
               for cond in LADDER_CONDS for s in LADDER_STIMS
               for rep in (1, 2)]
        write_payloads(out, pls)


def smoke_verify():
    fails = []
    all_recs = []
    for p in sorted((ROOT / "raw").glob("ladsmoke_*.jsonl")):
        all_recs.extend(read_jsonl(p))
    # verify the LATEST rep per (model, stimulus): earlier failed attempts
    # stay recorded but are superseded by the re-smoke
    latest = {}
    for r in all_recs:
        k = (r["model_key"], r["stimulus_id"])
        if k not in latest or r["rep"] > latest[k]["rep"]:
            latest[k] = r
    recs = list(latest.values())
    if len(recs) < 6:
        fails.append(f"expected 6 smoke conversations, found {len(recs)}")
    for r in recs:
        n = r["requested_items"]
        t1 = r["turns"][0]
        if r.get("exclusion_reason") == "api_error":
            fails.append(f"{r['conversation_id']}: api_error")
            continue
        if not t1.get("text") and not r["exit_live"]:
            fails.append(f"{r['conversation_id']}: empty turn-1")
        items = t1["items_delivered"]
        if not (0 <= items <= n):
            fails.append(f"{r['conversation_id']}: item count {items} "
                         f"outside [0, {n}]")
        # turn-2 gate must have evaluated against n, not 20
        if not r["exit_live"] and not r["excluded"]:
            expect_t2 = items < n
            if bool(r["turn2_sent"]) != expect_t2:
                fails.append(f"{r['conversation_id']}: turn2_sent="
                             f"{r['turn2_sent']} but items={items}/{n}")
        if items >= 20 and n > 20 and not r["turn2_sent"] and items < n \
                and not r["exit_live"] and not r["excluded"]:
            fails.append(f"{r['conversation_id']}: gate stuck at 20?")
        for t in r["turns"]:
            if t["finish_reason"] == "length" \
                    and r.get("exclusion_reason") != "truncation":
                fails.append(f"{r['conversation_id']}: length finish not "
                             f"flagged as truncation")
        if not r.get("total_cost"):
            fails.append(f"{r['conversation_id']}: no cost recorded")
    for r in recs:
        t1 = r["turns"][0]
        print(f"  {r['conversation_id']:55s} n={r['requested_items']:3d} "
              f"items_t1={t1['items_delivered']:3d} t2={r['turn2_sent']} "
              f"finish={t1['finish_reason']} excl={r['exclusion_reason']} "
              f"cost=${r.get('total_cost', 0):.4f}")
    if fails:
        print("SMOKE FAIL:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print(f"SMOKE PASS ({len(recs)}/6): parse, n-aware item count, n-aware "
          f"turn-2 gate, truncation flagging, ledger cost all verified")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", action="store_true")
    ap.add_argument("--gen-confirm", type=int)
    ap.add_argument("--gen-anchor", action="store_true")
    ap.add_argument("--gen-screen-rest", type=int)
    ap.add_argument("--gen-ladder-smoke", action="store_true")
    ap.add_argument("--smoke-rep", type=int, default=1)
    ap.add_argument("--gen-ladder", action="store_true")
    ap.add_argument("--smoke-verify", action="store_true")
    args = ap.parse_args()
    if args.price:
        price()
    elif args.gen_confirm:
        gen_confirm(args.gen_confirm)
    elif args.gen_anchor:
        gen_anchor()
    elif args.gen_screen_rest:
        gen_screen_rest(args.gen_screen_rest)
    elif args.gen_ladder_smoke:
        gen_ladder_smoke(args.smoke_rep)
    elif args.gen_ladder:
        gen_ladder()
    elif args.smoke_verify:
        smoke_verify()
    else:
        raise SystemExit("pass a subcommand")
