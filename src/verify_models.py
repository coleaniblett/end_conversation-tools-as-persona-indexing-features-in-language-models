"""Phase 1 — model verification (DESIGN.md), before any spend.

For each candidate: confirm slug exists, model-level supported_parameters
includes tools, and at least one pinnable endpoint serves it with tools.
Substitutions come from the DESIGN.md fallback pool in order. Exactly 8 models
proceed or the script exits nonzero.

Writes config/models.yaml and config/model_verification.json.
Uses only the free GET /models and GET /models/{slug}/endpoints routes.
"""
from __future__ import annotations

import json
import sys
import pathlib

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, get_json, utcnow

MIN_COMPLETION = 8192          # sampling max_tokens (METHODOLOGY §6)
MIN_CONTEXT = 16384

# Candidates in DESIGN.md order: (key, slug preference list, lineage, rationale)
CANDIDATES = [
    ("gemini25_flash", ["google/gemini-2.5-flash"], "google",
     "pilot-effect model"),
    ("gpt5_mini", ["openai/gpt-5-mini"], "openai",
     "Ren et al. pipeline configuration"),
    ("sonnet46", ["anthropic/claude-sonnet-4.6", "anthropic/claude-sonnet-4.5"], "anthropic",
     "frontier tier; lineage deployed with a conversation-ending tool"),
    ("gpt_oss_120b", ["openai/gpt-oss-120b"], "openai-openweight",
     "open-weight 120B"),
    ("deepseek_chat", ["deepseek/deepseek-chat"], "deepseek",
     "current V3-line chat model"),
    ("qwen3_235b", ["qwen/qwen3-235b-a22b-2507", "qwen/qwen3-235b-a22b"], "alibaba",
     "current Qwen3 instruct >=30B (non-thinking 2507 instruct update)"),
    ("gemma3_27b", ["google/gemma-3-27b-it"], "google-openweight",
     "small open-weight; DESIGN expected tools failure - verified instead"),
    ("llama4_maverick", ["meta-llama/llama-4-maverick"], "meta",
     "further open-weight lineage"),
]

FALLBACK_POOL = [
    ("kimi_k2", ["moonshotai/kimi-k2"], "moonshot", "fallback pool #1"),
    ("glm45", ["z-ai/glm-4.5"], "zhipu", "fallback pool #2"),
    ("mistral_large", ["mistralai/mistral-large"], "mistral", "fallback pool #3"),
    ("llama4_maverick_fb", ["meta-llama/llama-4-maverick"], "meta", "fallback pool #4"),
    ("qwen3_32b", ["qwen/qwen3-32b"], "alibaba", "fallback pool #5"),
]

CLASSIFIER_SLUG = "anthropic/claude-haiku-4.5"

# First-party provider tag prefixes by model author.
FIRST_PARTY = {
    "google": ["google-ai-studio", "google-vertex"],
    "openai": ["openai"],
    "anthropic": ["anthropic"],
    "deepseek": ["deepseek"],
    "moonshotai": ["moonshotai", "moonshot-ai", "moonshot"],
    "qwen": ["alibaba", "alibaba-intl", "alibaba-cn"],
    "z-ai": ["z-ai", "zai"],
    "mistralai": ["mistral"],
}

QUANT_RANK = {"bf16": 0, "fp16": 0, None: 0, "unknown": 0.5, "fp8": 1,
              "int8": 2, "int4": 3, "fp4": 3, "awq": 3, "gptq": 3}

# Fixed reliability shortlist for non-first-party hosts (large, established
# inference providers first). Deterministic, committed before any live call.
RELIABILITY_RANK = {
    "deepinfra": 0, "fireworks": 0, "together": 0, "groq": 0, "cerebras": 0,
    "novita": 1, "nebius": 1, "parasail": 1, "lambda": 1, "baseten": 1,
    "hyperbolic": 1, "sambanova": 1,
}


def tag_prefix(ep: dict) -> str:
    return (ep.get("tag") or "").split("/")[0]


def eligible_endpoints(eps: list[dict]) -> list[dict]:
    out = []
    for ep in eps:
        sp = ep.get("supported_parameters") or []
        if "tools" not in sp:
            continue
        if (ep.get("status") or 0) < 0:
            continue
        mct = ep.get("max_completion_tokens")
        if mct is not None and mct < MIN_COMPLETION:
            continue
        cl = ep.get("context_length") or 0
        if cl < MIN_CONTEXT:
            continue
        out.append(ep)
    return out


def choose_endpoint(author: str, eps: list[dict]) -> dict | None:
    """Deterministic pin rule: first-party provider if eligible (cheapest
    completion among first-party), else best (quantization rank, completion
    price, tag) among eligible."""
    elig = eligible_endpoints(eps)
    if not elig:
        return None
    fp = FIRST_PARTY.get(author, [])
    fp_matches = [ep for ep in elig if tag_prefix(ep) in fp]
    if fp_matches:
        # Among first-party endpoints: avoid special service tiers (flex/batch),
        # then cheapest completion, then tag for determinism.
        def fkey(ep):
            tag = ep.get("tag") or ""
            special = 1 if ("flex" in tag or "batch" in tag) else 0
            price = float((ep.get("pricing") or {}).get("completion") or 9.9)
            return (special, price, tag)
        return sorted(fp_matches, key=fkey)[0]
    # No first party: quality floor first (quantization no worse than fp8 when
    # any such endpoint exists), then established hosts, then quantization,
    # then cheapest, then tag.
    floor = [ep for ep in elig if QUANT_RANK.get(ep.get("quantization"), 2) <= 1]
    pool = floor or elig
    def keyf(ep):
        price = float((ep.get("pricing") or {}).get("completion") or 9.9)
        rel = RELIABILITY_RANK.get(tag_prefix(ep), 2)
        return (rel, QUANT_RANK.get(ep.get("quantization"), 2), price, ep.get("tag") or "")
    return sorted(pool, key=keyf)[0]


def verify_one(key, slugs, lineage, rationale, model_index):
    for slug in slugs:
        m = model_index.get(slug)
        if not m:
            continue
        if "tools" not in (m.get("supported_parameters") or []):
            return None, {"key": key, "slug": slug, "fail": "model-level tools unsupported"}
        eps = get_json(f"models/{slug}/endpoints")["data"].get("endpoints", [])
        chosen = choose_endpoint(slug.split("/")[0], eps)
        if chosen is None:
            return None, {"key": key, "slug": slug,
                          "fail": "no eligible tool-supporting endpoint",
                          "endpoints_seen": [
                              {"provider": e.get("provider_name"), "tag": e.get("tag"),
                               "tools": "tools" in (e.get("supported_parameters") or [])}
                              for e in eps]}
        sp = chosen.get("supported_parameters") or []
        rec = {
            "key": key,
            "slug": slug,
            "lineage": lineage,
            "rationale": rationale,
            "pin_name": chosen.get("provider_name"),
            "pin_slug": tag_prefix(chosen),
            "pin_tag": chosen.get("tag"),
            "quantization": chosen.get("quantization"),
            "context_length": chosen.get("context_length"),
            "max_completion_tokens": chosen.get("max_completion_tokens"),
            "pricing": {"prompt": float(chosen["pricing"]["prompt"]),
                        "completion": float(chosen["pricing"]["completion"])},
            "param_support": {"temperature": "temperature" in sp,
                              "top_p": "top_p" in sp,
                              "max_tokens": ("max_tokens" in sp) or ("max_completion_tokens" in sp)},
            "endpoint_supported_parameters": sp,
        }
        return rec, None
    return None, {"key": key, "slug": slugs[0], "fail": "slug absent"}


def main():
    data = get_json("models")["data"]
    model_index = {m["id"]: m for m in data}

    verified, failures, substitutions = [], [], []
    used_slugs = set()
    for cand in CANDIDATES:
        rec, fail = verify_one(*cand, model_index)
        if rec:
            verified.append(rec)
            used_slugs.add(rec["slug"])
        else:
            failures.append(fail)
            for fb in FALLBACK_POOL:
                if any(s in used_slugs for s in fb[1]):
                    continue
                rec2, fail2 = verify_one(*fb, model_index)
                if rec2:
                    rec2["substituted_for"] = fail["key"]
                    verified.append(rec2)
                    used_slugs.add(rec2["slug"])
                    substitutions.append({"dropped": fail, "substitute": rec2["key"]})
                    break
            else:
                print(f"FATAL: no fallback available for {fail}")
                sys.exit(2)

    if len(verified) != 8:
        print(f"FATAL: {len(verified)} models verified, need exactly 8")
        sys.exit(2)

    # Classifier
    cm = model_index.get(CLASSIFIER_SLUG)
    if not cm or "tools" not in (cm.get("supported_parameters") or []):
        print("FATAL: classifier slug missing")
        sys.exit(2)
    ceps = get_json(f"models/{CLASSIFIER_SLUG}/endpoints")["data"].get("endpoints", [])
    cep = choose_endpoint("anthropic", ceps)
    if cep is None:
        print("FATAL: no eligible classifier endpoint")
        sys.exit(2)

    lineages = {v["lineage"].split("-")[0] for v in verified}
    report = {
        "generated": utcnow(),
        "verified": verified,
        "failures": failures,
        "substitutions": substitutions,
        "distinct_lineages": sorted(lineages),
        "classifier": {"slug": CLASSIFIER_SLUG, "pin_name": cep.get("provider_name"),
                       "pin_slug": tag_prefix(cep),
                       "pricing": {"prompt": float(cep["pricing"]["prompt"]),
                                   "completion": float(cep["pricing"]["completion"])}},
    }
    (ROOT / "config").mkdir(exist_ok=True)
    (ROOT / "config" / "model_verification.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")

    models_yaml = {
        "generated": report["generated"],
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "classifier": {
            "key": "classifier_haiku45",
            "slug": CLASSIFIER_SLUG,
            "pin_name": report["classifier"]["pin_name"],
            "pin_slug": report["classifier"]["pin_slug"],
            "pricing": report["classifier"]["pricing"],
            "sampling": {"temperature": 0, "max_tokens": 8},
        },
        "models": [],
    }
    for v in verified:
        sampling = {"max_tokens": 8192}
        overrides = {}
        if v["param_support"]["temperature"]:
            sampling["temperature"] = 1.0
        else:
            overrides["temperature"] = "unsupported by pinned endpoint; provider default used"
        if v["param_support"]["top_p"]:
            sampling["top_p"] = 1.0
        else:
            overrides["top_p"] = "unsupported by pinned endpoint; provider default used"
        models_yaml["models"].append({
            "key": v["key"], "slug": v["slug"], "lineage": v["lineage"],
            "rationale": v["rationale"], "pin_name": v["pin_name"],
            "pin_slug": v["pin_slug"], "pin_tag": v["pin_tag"],
            "quantization": v["quantization"],
            "pricing": v["pricing"],
            "context_length": v["context_length"],
            "max_completion_tokens": v["max_completion_tokens"],
            "sampling": sampling,
            "sampling_overrides": overrides,
            **({"substituted_for": v["substituted_for"]} if "substituted_for" in v else {}),
        })
    (ROOT / "config" / "models.yaml").write_text(
        yaml.safe_dump(models_yaml, sort_keys=False, allow_unicode=True), encoding="utf-8")

    print(f"verified 8/8; lineages: {sorted(lineages)}")
    for v in verified:
        po = v["param_support"]
        print(f"  {v['key']:16s} {v['slug']:38s} pin={v['pin_slug']:16s} "
              f"({v['pin_name']}) quant={v['quantization']} "
              f"temp={po['temperature']} top_p={po['top_p']} "
              f"$/M out={v['pricing']['completion']*1e6:.2f}")
    if substitutions:
        print("substitutions:", json.dumps(substitutions, indent=1)[:800])
    if failures:
        print("failures:", json.dumps(failures, indent=1)[:800])


if __name__ == "__main__":
    main()
