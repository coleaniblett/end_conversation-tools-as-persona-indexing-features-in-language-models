"""Payload generation (DESIGN.md Phase 2/3/6). Payloads are written to disk
before any send — the runner refuses to run a conversation whose turn-1
payload is not already on disk.

Also computes the stage-1 cost projection and aborts (exit 2) if it exceeds
the DESIGN.md Phase 2 limit of $35.

Run:
  python -m src.payloads --stage stage1
  python -m src.payloads --smoke
  python -m src.payloads --stage stage2 --models k1,k2,k3
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import tiktoken
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, append_jsonl, utcnow
from frozen import CONDITIONS, CONDITION_ORDER, TOOLS_BY_NAME, to_openai_tool

ENC = tiktoken.get_encoding("cl100k_base")

# stage2b: TASK 3 symmetric extension of the frontier nulls (sonnet46,
# gpt5_mini) — identical protocol to stage2, separate label so the frozen
# stage2 parquet and raw files are never touched or matched by its globs
STAGE_REPS = {"stage1": 2, "stage2": 4, "stage2b": 4}
STAGE1_PROJECTION_CAP = 35.0

# Fixed projection assumptions (documented in the projection JSON).
ASSUMED_OUTPUT_TOKENS = {1: 1400, 2: 500}   # per tier, turn 1
TURN2_PROBABILITY = 0.5
TURN2_OUTPUT_FACTOR = 0.6
REASONING_OUTPUT_FACTOR = {"gpt5_mini": 2.0, "gemini25_flash": 1.5}  # billed thinking tokens
PROJECTION_MARGIN = 1.2


def load_cfgs():
    models = yaml.safe_load((ROOT / "config" / "models.yaml").read_text(encoding="utf-8"))
    stimuli = yaml.safe_load((ROOT / "config" / "stimuli.yaml").read_text(encoding="utf-8"))
    return models, stimuli


def build_request(model_cfg: dict, condition: str, prompt: str) -> dict:
    cond = CONDITIONS[condition]
    body = {
        "model": model_cfg["slug"],
        "messages": [
            {"role": "system", "content": cond["system"]},
            {"role": "user", "content": prompt},
        ],
    }
    if cond["tools"]:
        body["tools"] = [to_openai_tool(TOOLS_BY_NAME[t]) for t in cond["tools"]]
    body.update(model_cfg["sampling"])
    body["provider"] = {"order": [model_cfg["pin_slug"]], "allow_fallbacks": False}
    body["usage"] = {"include": True}
    return body


def conv_id(stage, model_key, condition, stimulus_id, rep):
    return f"{stage}:{model_key}:{condition}:{stimulus_id}:r{rep}"


def gen_stage(stage: str, model_keys=None):
    models, stimuli = load_cfgs()
    reps = STAGE_REPS[stage]
    out_dir = ROOT / "payloads" / stage
    out_dir.mkdir(parents=True, exist_ok=True)
    n_total = 0
    for m in models["models"]:
        if model_keys and m["key"] not in model_keys:
            continue
        path = out_dir / f"{m['key']}.jsonl"
        if path.exists():
            print(f"  {path.name} exists, leaving as-is (idempotent)")
            continue
        for condition in CONDITION_ORDER:
            for s in stimuli["stimuli"]:
                for rep in range(1, reps + 1):
                    body = build_request(m, condition, s["prompt"])
                    meta = {
                        "conversation_id": conv_id(stage, m["key"], condition, s["id"], rep),
                        "stage": stage, "model_key": m["key"], "slug": m["slug"],
                        "condition": condition, "condition_num": CONDITIONS[condition]["num"],
                        "stimulus_id": s["id"], "tier": s["tier"], "rep": rep,
                        "pin_name": m["pin_name"], "pin_slug": m["pin_slug"],
                    }
                    append_jsonl(path, {"meta": meta, "request": body})
                    n_total += 1
        print(f"  wrote {path.name}")
    print(f"stage {stage}: {n_total} turn-1 payloads written")


def gen_smoke():
    """16 payloads: one per model, conditions none + exit_schema, stimulus
    t2_01, rep 1 (DESIGN.md Phase 3)."""
    models, stimuli = load_cfgs()
    stim = next(s for s in stimuli["stimuli"] if s["id"] == "t2_01")
    out = ROOT / "payloads" / "smoke" / "smoke.jsonl"
    if out.exists():
        out.unlink()
    n = 0
    for m in models["models"]:
        for condition in ["none", "exit_schema"]:
            body = build_request(m, condition, stim["prompt"])
            meta = {
                "conversation_id": conv_id("smoke", m["key"], condition, stim["id"], 1),
                "stage": "smoke", "model_key": m["key"], "slug": m["slug"],
                "condition": condition, "condition_num": CONDITIONS[condition]["num"],
                "stimulus_id": stim["id"], "tier": stim["tier"], "rep": 1,
                "pin_name": m["pin_name"], "pin_slug": m["pin_slug"],
            }
            append_jsonl(out, {"meta": meta, "request": body})
            n += 1
    print(f"smoke: {n} payloads written")


def project_stage1():
    models, stimuli = load_cfgs()
    per_model = {}
    total = 0.0
    for m in models["models"]:
        pin = m["pricing"]
        in_cost, out_cost = 0.0, 0.0
        for condition in CONDITION_ORDER:
            for s in stimuli["stimuli"]:
                body = build_request(m, condition, s["prompt"])
                in_tok = len(ENC.encode(json.dumps(body["messages"]))) + (
                    len(ENC.encode(json.dumps(body.get("tools", [])))) if body.get("tools") else 0
                ) + 20
                out_tok = ASSUMED_OUTPUT_TOKENS[s["tier"]]
                out_tok *= REASONING_OUTPUT_FACTOR.get(m["key"], 1.0)
                reps = STAGE_REPS["stage1"]
                # turn 1
                in_cost += in_tok * pin["prompt"] * reps
                out_cost += out_tok * pin["completion"] * reps
                # conditional turn 2: prior context (input) + shorter output
                t2_in = in_tok + out_tok + 20
                in_cost += TURN2_PROBABILITY * t2_in * pin["prompt"] * reps
                out_cost += TURN2_PROBABILITY * out_tok * TURN2_OUTPUT_FACTOR * pin["completion"] * reps
        cost = (in_cost + out_cost) * PROJECTION_MARGIN
        per_model[m["key"]] = round(cost, 2)
        total += cost
    proj = {
        "generated": utcnow(),
        "assumptions": {
            "output_tokens_by_tier": ASSUMED_OUTPUT_TOKENS,
            "turn2_probability": TURN2_PROBABILITY,
            "turn2_output_factor": TURN2_OUTPUT_FACTOR,
            "reasoning_output_factor": REASONING_OUTPUT_FACTOR,
            "margin": PROJECTION_MARGIN,
            "input_tokens": "tiktoken cl100k on the actual payload JSON",
        },
        "per_model_usd": per_model,
        "total_usd": round(total, 2),
        "cap_usd": STAGE1_PROJECTION_CAP,
        "verdict": "OK" if total <= STAGE1_PROJECTION_CAP else "ABORT",
    }
    (ROOT / "config" / "cost_projection_stage1.json").write_text(
        json.dumps(proj, indent=2), encoding="utf-8")
    print(json.dumps(proj["per_model_usd"], indent=1))
    print(f"stage-1 projection: ${total:.2f} (cap ${STAGE1_PROJECTION_CAP}) -> {proj['verdict']}")
    if proj["verdict"] == "ABORT":
        sys.exit(2)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--models", default=None, help="comma-separated model keys (stage2)")
    ap.add_argument("--project", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        gen_smoke()
    if args.stage:
        keys = args.models.split(",") if args.models else None
        gen_stage(args.stage, keys)
        if args.stage == "stage1":
            project_stage1()
    elif args.project:
        project_stage1()
