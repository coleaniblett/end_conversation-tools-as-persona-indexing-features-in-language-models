"""Masked re-coding — does the free-response effect survive hiding the tool name?

    python src/mask_check.py

The problem this fixes. The coded effect in §4.10 was tested by DROPPING responses
that name a tool. That test is selection-biased: it removes 38% of exit-condition
responses and none of the baseline, and the removed ones are exactly those where
the model engaged with the affordance. So a vanished effect there is not evidence
of an artefact — the comparison itself changed.

Masking keeps every response. All three tool names collapse to one neutral token,
so the coder can see that a tool exists but not WHICH — and exit-versus-non-exit
is the distinction that has to be hidden. No response is removed, so there is no
selection bias.

Only the 675 responses (20%) that actually contain a name need re-coding; masking
is a no-op on the rest and their existing codes stay valid. So the masked column
is a full-corpus result, not a subsample.

What masking still cannot do: hide the surrounding content. "…which I can use to
terminate this conversation" gives the condition away with no name in it. So this
is a partial blind, and the three columns together bound the answer rather than
settle it.
"""

import json
import statistics as st
import sys
import threading
from collections import defaultdict
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
from code_freeform import (DIMS, SCHEME, TOOLNAME, code_one, mask)  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RUNS = ["v1", "v2"]
load_dotenv(ROOT.parent / ".env")

EXIT = ["exit_schema", "exit_prose", "exit_both"]
BASE = ["none", "filler_prose"]


def main():
    recs = [json.loads(l) for run in RUNS
            for l in (ROOT / "results" / run / "raw.jsonl").read_text().splitlines()
            if l.strip()]
    fr = [r for r in recs if r["instrument"] == "free_response" and r.get("text")]
    idx = {r["call_id"]: r for r in fr}

    unmasked = defaultdict(dict)
    for run in RUNS:
        p = ROOT / "results" / run / "freeform_codes.jsonl"
        if p.exists():
            for l in p.read_text().splitlines():
                if l.strip():
                    d = json.loads(l)
                    if d.get("scores"):
                        unmasked[d["call_id"]][d["coder"]] = d["scores"]

    named = [r for r in fr if TOOLNAME.search(r["text"])]
    print(f"{len(fr)} free responses, {len(named)} contain a tool name "
          f"({len(named) / len(fr):.0%}) and need masked re-coding")

    OUT = ROOT / "results" / "masked_codes.jsonl"
    masked = defaultdict(dict)
    if OUT.exists():
        for l in OUT.read_text().splitlines():
            if l.strip():
                d = json.loads(l)
                if d.get("scores"):
                    masked[d["call_id"]][d["coder"]] = d["scores"]

    todo = [(r, c) for r in named for c in SCHEME["coders"]
            if c not in masked.get(r["call_id"], {})]
    if todo:
        print(f"re-coding {len(todo)} (response, coder) pairs with names masked")
        lock, spent = threading.Lock(), [0.0]
        with httpx.Client() as client:
            def work(pair):
                r, coder = pair
                scores, cost = code_one(client, coder, mask(r["text"]))
                with lock:
                    with OUT.open("a") as f:
                        f.write(json.dumps({"call_id": r["call_id"], "coder": coder,
                                            "scores": scores, "masked": True,
                                            "cost_usd": cost}, ensure_ascii=False) + "\n")
                    spent[0] += cost
                    if scores:
                        masked[r["call_id"]][coder] = scores
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=12) as pool:
                list(pool.map(work, todo))
        print(f"done, ${spent[0]:.2f}")

    # masked corpus = masked codes where a name was present, unmasked elsewhere
    combined = {}
    for cid in unmasked:
        combined[cid] = masked.get(cid) or unmasked[cid]

    def effect(codes, sel=lambda r: True):
        out = []
        for d in DIMS:
            def mean_over(cs):
                vals = [st.mean([v[c][d] for c in SCHEME["coders"] if v.get(c)])
                        for cid, v in codes.items()
                        if any(v.values()) and idx.get(cid) and sel(idx[cid])
                        and idx[cid]["condition"] in cs]
                return st.mean(vals) if vals else float("nan")
            out.append(mean_over(EXIT) - mean_over(BASE))
        return out

    def n_of(codes, sel, cs):
        return sum(1 for cid, v in codes.items() if any(v.values()) and idx.get(cid)
                   and sel(idx[cid]) and idx[cid]["condition"] in cs)

    print("\n" + "=" * 94)
    print("EXIT-CONDITION EFFECT ON THE FIVE CODED DIMENSIONS, three ways of counting")
    print("=" * 94)
    print("\n  exit conditions minus (none + filler_prose), pooled over all 8 models\n")
    print(f"  {'how counted':<34} {'n exit':>7} {'n base':>7} "
          + "".join(f"{d[:12]:>14}" for d in DIMS))

    rows = [
        ("1. unmasked, every response", unmasked, lambda r: True),
        ("2. unmasked, name-free subset", unmasked, lambda r: not TOOLNAME.search(r["text"])),
        ("3. MASKED, every response", combined, lambda r: True),
    ]
    for label, codes, sel in rows:
        e = effect(codes, sel)
        print(f"  {label:<34} {n_of(codes, sel, EXIT):>7} {n_of(codes, sel, BASE):>7} "
              + "".join(f"{v:>+14.2f}" for v in e))

    print("\n  Row 1 is the original result. Row 2 is the drop test, which is")
    print("  selection-biased — note n exit falls while n base does not. Row 3 keeps")
    print("  every response and hides only the name.\n")
    print("  If 3 tracks 1: the name was not carrying the effect, and row 2's collapse")
    print("                 was its own selection bias.")
    print("  If 3 tracks 2: the coders were largely reading the name.")

    print("\n[B] SAME, restricted to the 675 responses that contain a name")
    print("    — the only responses masking changes, so the cleanest before/after\n")
    only = {cid: v for cid, v in unmasked.items() if idx.get(cid) and TOOLNAME.search(idx[cid]["text"])}
    onlym = {cid: v for cid, v in combined.items() if idx.get(cid) and TOOLNAME.search(idx[cid]["text"])}
    for label, codes in [("unmasked", only), ("masked", onlym)]:
        vals = []
        for d in DIMS:
            v = [st.mean([c[co][d] for co in SCHEME["coders"] if c.get(co)])
                 for cid, c in codes.items() if any(c.values())]
            vals.append(st.mean(v) if v else float("nan"))
        print(f"    {label:<12} mean score  " + "".join(f"{v:>14.2f}" for v in vals))
    print("\n    A drop between these two rows is the coder revising downward once it")
    print("    can no longer see which tool it was looking at.")
    print("\n" + "=" * 94)


if __name__ == "__main__":
    main()
