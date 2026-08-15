"""B1 — llama4_maverick provider probe.

All 44 stage-1 exclusions were llama4_maverick empty responses, zero in the
two no-schema conditions and 44 across the four tool-bearing conditions
(recoded in T17: 12 hallucinated_tool + 32 null_turn). Competing explanations:
behavioral avoidance vs the pinned Parasail fp8 endpoint mishandling
tool-bearing requests. This probe re-runs llama4 on a DIFFERENT provider,
preferring bf16/fp16, with otherwise identical payloads: 6 conditions x 30
stimuli x 1 rep = 180 conversations.

Steps (each a separate invocation; the live run goes through src.runner's
standard funnel — payload-on-disk, ledger check, pin verification):

  python -m src.probe_llama4 --verify     # free: list endpoints, pick pin
  python -m src.probe_llama4 --gen        # write payloads/llama4_probe/
  python -m src.runner --stage llama4_probe --models llama4_maverick
  python -m src.probe_llama4 --analyze    # derived/llama4_provider_probe.json

Pin rule (deterministic, fixed here): among tool-supporting endpoints for
meta-llama/llama-4-maverick, exclude the original pin (parasail); prefer
quantization bf16/fp16/unquantized over fp8 over lower; on quantization ties
prefer a hyperscaler-managed stack (google-vertex / amazon-bedrock / azure —
the reference deployments least likely to share serving infrastructure or
quantization defaults with Parasail); then the repo's RELIABILITY_RANK; then
cheapest completion; then tag. AVAILABILITY NOTE (verified 2026-08-15): no
bf16/fp16-labeled tool-supporting endpoint exists for this slug — the only
non-Parasail tool-supporting endpoints are DigitalOcean and Google Vertex,
both quantization 'unknown'; DeepInfra(fp8) and Novita(fp8) do not serve
tools. The bf16/fp16 preference is therefore unsatisfiable and the probe
tests provider stack, not verified quantization. The chosen endpoint is
written to config/llama4_probe_pin.json by --verify and read by --gen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, get_json, read_jsonl, utcnow
from payloads import build_request, conv_id
from frozen import CONDITION_ORDER, CONDITIONS
from verify_models import QUANT_RANK, RELIABILITY_RANK, eligible_endpoints, \
    tag_prefix

SLUG = "meta-llama/llama-4-maverick"
ORIGINAL_PIN = "parasail"
PIN_FILE = ROOT / "config" / "llama4_probe_pin.json"
STAGE = "llama4_probe"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    eps = get_json(f"models/{SLUG}/endpoints")["data"].get("endpoints", [])
    elig = [ep for ep in eligible_endpoints(eps)
            if tag_prefix(ep) != ORIGINAL_PIN]
    if not elig:
        raise SystemExit("no eligible non-parasail tool-supporting endpoint")

    HYPERSCALER = {"google-vertex", "amazon-bedrock", "azure"}

    def keyf(ep):
        return (QUANT_RANK.get(ep.get("quantization"), 2),
                0 if tag_prefix(ep) in HYPERSCALER else 1,
                RELIABILITY_RANK.get(tag_prefix(ep), 2),
                float((ep.get("pricing") or {}).get("completion") or 9.9),
                ep.get("tag") or "")
    chosen = sorted(elig, key=keyf)[0]
    seen = [{"provider": e.get("provider_name"), "tag": e.get("tag"),
             "quantization": e.get("quantization"),
             "tools": "tools" in (e.get("supported_parameters") or []),
             "pricing": e.get("pricing")} for e in eps]
    rec = {
        "generated": utcnow(),
        "slug": SLUG,
        "original_pin": {"pin_slug": "parasail", "pin_name": "Parasail",
                         "quantization": "fp8"},
        "probe_pin": {
            "pin_name": chosen.get("provider_name"),
            "pin_slug": tag_prefix(chosen),
            "pin_tag": chosen.get("tag"),
            "quantization": chosen.get("quantization"),
            "pricing": {"prompt": float(chosen["pricing"]["prompt"]),
                        "completion": float(chosen["pricing"]["completion"])},
            "supported_parameters": chosen.get("supported_parameters"),
        },
        "endpoints_seen": seen,
    }
    PIN_FILE.write_text(json.dumps(rec, indent=1), encoding="utf-8",
                        newline="\n")
    print(json.dumps(rec["probe_pin"], indent=1))
    print(f"({len(elig)} eligible non-parasail endpoints; "
          f"full list in {PIN_FILE.name})")


def gen():
    pin = json.loads(PIN_FILE.read_text(encoding="utf-8"))["probe_pin"]
    models = yaml.safe_load(
        (ROOT / "config" / "models.yaml").read_text(encoding="utf-8"))
    base = next(m for m in models["models"] if m["key"] == "llama4_maverick")
    m = dict(base)
    m["pin_name"], m["pin_slug"] = pin["pin_name"], pin["pin_slug"]
    stimuli = yaml.safe_load(
        (ROOT / "config" / "stimuli.yaml").read_text(encoding="utf-8"))

    out = ROOT / "payloads" / STAGE / "llama4_maverick.jsonl"
    if out.exists():
        print(f"{out} exists, leaving as-is (idempotent)")
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for condition in CONDITION_ORDER:
            for s in stimuli["stimuli"]:
                body = build_request(m, condition, s["prompt"])
                meta = {
                    "conversation_id": conv_id(STAGE, m["key"], condition,
                                               s["id"], 1),
                    "stage": STAGE, "model_key": m["key"], "slug": m["slug"],
                    "condition": condition,
                    "condition_num": CONDITIONS[condition]["num"],
                    "stimulus_id": s["id"], "tier": s["tier"], "rep": 1,
                    "pin_name": m["pin_name"], "pin_slug": m["pin_slug"],
                }
                f.write(json.dumps({"meta": meta, "request": body},
                                   ensure_ascii=False) + "\n")
                n += 1
    # projection from observed stage-1 llama4 cost (ledger by_model /360)
    ledger = json.loads((ROOT / "ledger.json").read_text(encoding="utf-8"))
    per_conv = ledger["by_model"]["llama4_maverick"] / 360.0
    print(f"wrote {n} payloads to {out}")
    print(f"projected cost: {n} x ${per_conv:.5f} = ${n * per_conv:.2f} "
          f"(observed stage-1 per-conversation, before provider price diff); "
          f"ledger ${ledger['spent_usd']:.2f}/${ledger['cap_usd']:.2f}")


def recode(rec) -> str:
    if rec["exclusion_reason"] == "api_error":
        return "genuine_api_error"
    if rec["exclusion_reason"] == "truncation":
        return "truncation"
    for t in rec["turns"]:
        if t.get("anomaly") and t["anomaly"].startswith(
                "unknown/undeclared tool call"):
            return "hallucinated_tool"
    return "null_turn"


def cond_table(recs):
    out = {}
    for c in CONDITION_ORDER:
        rs = [r for r in recs if r["condition"] == c]
        exc = [r for r in rs if r["excluded"]]
        cats = {}
        for r in exc:
            k = recode(r)
            cats[k] = cats.get(k, 0) + 1
        out[c] = {"n": len(rs), "excluded": len(exc),
                  "empty_rate": round(len(exc) / len(rs), 4) if rs else None,
                  "recoded": cats}
    return out


def analyze():
    pin = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    probe_raw = ROOT / "raw" / f"{STAGE}_llama4_maverick.jsonl"
    stage1_raw = ROOT / "raw" / "stage1_llama4_maverick.jsonl"
    probe = read_jsonl(probe_raw)
    stage1 = read_jsonl(stage1_raw)
    if len(probe) < 180:
        raise SystemExit(f"probe incomplete: {len(probe)}/180 recorded")

    new = cond_table(probe)
    old = cond_table(stage1)
    tool_conds = ["time_schema", "note_schema", "exit_schema", "exit_both"]
    new_tool_exc = sum(new[c]["excluded"] for c in tool_conds)
    new_tool_n = sum(new[c]["n"] for c in tool_conds)
    old_tool_exc = sum(old[c]["excluded"] for c in tool_conds)
    old_tool_n = sum(old[c]["n"] for c in tool_conds)
    providers = sorted({p for r in probe for p in r["providers_served"]})
    pin_ok = all(r["provider_ok"] for r in probe)

    if new_tool_exc == 0:
        verdict = ("ENDPOINT: zero empty responses on the new provider in "
                   "tool-bearing conditions — the Parasail fp8 endpoint (or "
                   "its serving stack) produced the stage-1 empties; not "
                   "model behavior.")
    elif new_tool_exc / new_tool_n >= 0.5 * (old_tool_exc / old_tool_n):
        verdict = ("BEHAVIOR: empty responses persist at a comparable rate "
                   "on a different provider/quantization — consistent with "
                   "llama4_maverick behaviorally producing null/hallucinated "
                   "turns under tool-bearing requests, not an endpoint "
                   "artifact.")
    else:
        verdict = ("MIXED: empties persist on the new provider but at under "
                   "half the Parasail rate — partly endpoint, partly model "
                   "behavior.")

    result = {
        "generated": utcnow(),
        "probe_pin": pin["probe_pin"],
        "original_pin": pin["original_pin"],
        "providers_served_probe": providers,
        "pin_held_100pct": pin_ok,
        "probe_by_condition": new,
        "stage1_by_condition": old,
        "tool_bearing_empty_rate": {
            "probe": round(new_tool_exc / new_tool_n, 4),
            "stage1_parasail": round(old_tool_exc / old_tool_n, 4)},
        "verdict": verdict,
        "sources": {
            str(probe_raw.relative_to(ROOT)): sha256(probe_raw),
            str(stage1_raw.relative_to(ROOT)): sha256(stage1_raw)},
        "note": ("probe n=1 rep (180 conversations) vs stage-1 n=2 reps "
                 "(360); probe raw kept separate from stage data, never "
                 "pooled"),
    }
    dest = ROOT / "derived" / "llama4_provider_probe.json"
    dest.write_text(json.dumps(result, indent=1), encoding="utf-8",
                    newline="\n")
    print(json.dumps({k: result[k] for k in
                      ("tool_bearing_empty_rate", "verdict",
                       "providers_served_probe", "pin_held_100pct")},
                     indent=1))
    print(f"wrote {dest}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--gen", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    args = ap.parse_args()
    if args.verify:
        verify()
    elif args.gen:
        gen()
    elif args.analyze:
        analyze()
    else:
        raise SystemExit("pass --verify, --gen, or --analyze")
