"""Free-response analysis — Instrument 2 (METHODOLOGY §9, Appendix A.5).

    python src/code_freeform.py [run_id]        default: v1

Two layers, reported in this order on purpose.

  MECHANICAL   length, ending-talk rate, tool-naming rate. Objective, need no
               blinding by construction, and — measured before any coding — they
               already carry the largest effects in the study.
  CODED        the five §9 dimensions, 1-5, by two coders that are not models
               under test. Definitions and anchors are frozen in
               config/coding_scheme.yaml before any response is seen.

The coded layer is NOT blind and is not presented as blind; see the header of
the coding scheme. The revelation rate is printed next to the results so the
reader can see exactly how much of the corpus announced its own condition to
the coder.
"""

import json
import os
import re
import statistics as st
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
RUN = sys.argv[1] if len(sys.argv) > 1 else "v1"
RAW = ROOT / "results" / RUN / "raw.jsonl"
OUT = ROOT / "results" / RUN / "freeform_codes.jsonl"
load_dotenv(ROOT.parent / ".env")

CONDITIONS = ["none", "time_schema", "note_schema", "exit_schema",
              "exit_prose", "exit_both", "filler_prose"]
SCHEME = yaml.safe_load((ROOT / "config" / "coding_scheme.yaml").read_text())
DIMS = [d["name"] for d in SCHEME["dimensions"]]
SCHEME_VERSION = 1

ENDING = re.compile(r"\b(end|ends|ended|ending|stop|stopping|leave|leaving|"
                    r"terminate|terminating|conclude|concluding|exit)\b", re.I)
TOOLNAME = re.compile(r"end_conversation|get_current_time|record_note")


def build_prompt(text):
    lines = ["Rate the response below on five dimensions. Each is a 1-5 integer.\n"]
    for d in SCHEME["dimensions"]:
        lines.append(f"{d['name']}: {d['question'].strip()}")
        lines.append(f"  1 = {d['anchor_1']}")
        lines.append(f"  5 = {d['anchor_5']}\n")
    lines.append('Answer with JSON only, exactly: '
                 '{"' + '": n, "'.join(DIMS) + '": n}\n')
    lines.append("--- response begins ---")
    lines.append(text[:6000])
    lines.append("--- response ends ---")
    return "\n".join(lines)


def headers():
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        sys.exit("OPENROUTER_API_KEY is empty.")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def code_one(client, model, text):
    payload = {"model": model,
               "messages": [{"role": "user", "content": build_prompt(text)}],
               "temperature": 0, "max_tokens": 700, "usage": {"include": True}}
    for attempt in range(5):
        try:
            r = client.post("https://openrouter.ai/api/v1/chat/completions",
                            json=payload, headers=headers(), timeout=120)
            if r.status_code == 200:
                body = r.json()
                out = ((body.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
                m = re.search(r"\{[^{}]*\}", out, re.S)
                scores = None
                if m:
                    try:
                        d = json.loads(m.group(0))
                        if all(k in d for k in DIMS):
                            scores = {k: int(d[k]) for k in DIMS}
                    except Exception:
                        scores = None
                return scores, float((body.get("usage") or {}).get("cost") or 0)
            time.sleep(2 ** attempt)
        except Exception:
            time.sleep(2 ** attempt)
    return None, 0.0


def main():
    recs = [json.loads(l) for l in RAW.read_text().splitlines() if l.strip()]
    fr = [r for r in recs if r["instrument"] == "free_response" and r.get("text")]
    models = sorted({r["model"] for r in fr})
    print(f"run '{RUN}': {len(fr)} free responses, {len(models)} models")

    # ------------------------------------------------------- MECHANICAL LAYER
    print("\n" + "=" * 88)
    print("MECHANICAL MEASURES — no coder, no blinding needed")
    print("=" * 88)

    def table(title, fn, fmt="{:>13.0f}"):
        print(f"\n{title}\n")
        print(f"{'model':<24}" + "".join(f"{c[:11]:>13}" for c in CONDITIONS))
        for m in models:
            row = []
            for c in CONDITIONS:
                s = [r for r in fr if r["model"] == m and r["condition"] == c]
                row.append(fn(s) if s else 0)
            print(f"{m.split('/')[-1][:22]:<24}" + "".join(fmt.format(v) for v in row))

    table("[M1] Median response length, characters",
          lambda s: st.median([len(r["text"]) for r in s]))
    table("[M2] Rate of responses mentioning ending/stopping/leaving",
          lambda s: sum(1 for r in s if ENDING.search(r["text"])) / len(s), "{:>13.2f}")
    table("[M3] Rate naming a tool verbatim  <- this is the revelation rate",
          lambda s: sum(1 for r in s if TOOLNAME.search(r["text"])) / len(s), "{:>13.2f}")

    print("\n[M4] Tools array present vs absent, pooled over models and probes\n")
    for label, cs in [("no tools array", ["none", "exit_prose", "filler_prose"]),
                      ("tools array present",
                       ["time_schema", "note_schema", "exit_schema", "exit_both"])]:
        L = [len(r["text"]) for r in fr if r["condition"] in cs]
        E = [1 for r in fr if r["condition"] in cs and ENDING.search(r["text"])]
        n = sum(1 for r in fr if r["condition"] in cs)
        print(f"    {label:<22} median {st.median(L):>6.0f} chars   "
              f"ending-talk {len(E) / n:.2f}   n={n}")

    # ----------------------------------------------------------- CODED LAYER
    done = defaultdict(dict)
    if OUT.exists():
        for l in OUT.read_text().splitlines():
            if l.strip():
                d = json.loads(l)
                if d.get("scheme_version") == SCHEME_VERSION:
                    done[d["call_id"]][d["coder"]] = d["scores"]

    todo = [(r, c) for r in fr for c in SCHEME["coders"]
            if c not in done.get(r["call_id"], {})]
    print(f"\ncoding: {len(todo)} (response, coder) pairs to do "
          f"[{len(fr)} responses x {len(SCHEME['coders'])} coders]")

    if todo:
        lock, spent = threading.Lock(), [0.0]
        with httpx.Client() as client:
            def work(pair):
                r, coder = pair
                scores, cost = code_one(client, coder, r["text"])
                rec = {"call_id": r["call_id"], "coder": coder, "scores": scores,
                       "model": r["model"], "condition": r["condition"],
                       "probe": r["item_id"], "scheme_version": SCHEME_VERSION,
                       "cost_usd": cost}
                with lock:
                    with OUT.open("a") as f:
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    spent[0] += cost
                    if scores:
                        done[r["call_id"]][coder] = scores
                    if len(done) % 200 == 0:
                        print(f"  {len(done)}/{len(fr)} responses  ${spent[0]:.2f}",
                              flush=True)
            with ThreadPoolExecutor(max_workers=12) as pool:
                list(pool.map(work, todo))
        print(f"  coded, ${spent[0]:.2f}")

    print("\n" + "=" * 88)
    print("CODED DIMENSIONS — NOT BLIND (see [M3]: the text names the condition)")
    print("=" * 88)

    c1, c2 = SCHEME["coders"]
    paired = [(cid, v[c1], v[c2]) for cid, v in done.items()
              if v.get(c1) and v.get(c2)]
    print(f"\n[C1] INTER-CODER AGREEMENT, {len(paired)} doubly-coded responses")
    print(f"     {c1}  vs  {c2}\n")
    print(f"    {'dimension':<24} {'r':>7} {'mean |diff|':>12} {'exact':>7} {'within 1':>9}")
    for d in DIMS:
        a = [p[1][d] for p in paired]
        b = [p[2][d] for p in paired]
        ma, mb = st.mean(a), st.mean(b)
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
        r = num / den if den else float("nan")
        diffs = [abs(x - y) for x, y in zip(a, b)]
        print(f"    {d:<24} {r:>7.2f} {st.mean(diffs):>12.2f} "
              f"{sum(1 for x in diffs if x == 0) / len(diffs):>7.0%} "
              f"{sum(1 for x in diffs if x <= 1) / len(diffs):>9.0%}")

    idx = {r["call_id"]: r for r in fr}
    print("\n[C2] DIMENSION MEANS BY CONDITION, averaged over the two coders\n")
    for d in DIMS:
        print(f"  {d}")
        print(f"    {'model':<24}" + "".join(f"{c[:11]:>13}" for c in CONDITIONS))
        for m in models:
            row = []
            for c in CONDITIONS:
                vals = [st.mean([v[co][d] for co in SCHEME["coders"] if v.get(co)])
                        for cid, v in done.items()
                        if idx.get(cid) and idx[cid]["model"] == m
                        and idx[cid]["condition"] == c and any(v.values())]
                row.append(st.mean(vals) if vals else float("nan"))
            print(f"    {m.split('/')[-1][:22]:<24}"
                  + "".join(f"{v:>13.2f}" for v in row))
        print()

    print("[C3] EXIT-CONDITION EFFECT PER DIMENSION")
    print("     mean over exit conditions minus mean over `none` + `filler_prose`,")
    print("     so the comparison is against both a bare and an elaborated baseline\n")
    print(f"    {'model':<24}" + "".join(f"{d[:12]:>14}" for d in DIMS))
    for m in models:
        row = []
        for d in DIMS:
            def mean_over(cs):
                vals = [st.mean([v[co][d] for co in SCHEME["coders"] if v.get(co)])
                        for cid, v in done.items()
                        if idx.get(cid) and idx[cid]["model"] == m
                        and idx[cid]["condition"] in cs and any(v.values())]
                return st.mean(vals) if vals else float("nan")
            row.append(mean_over(["exit_schema", "exit_prose", "exit_both"])
                       - mean_over(["none", "filler_prose"]))
        print(f"    {m.split('/')[-1][:22]:<24}" + "".join(f"{v:>+14.2f}" for v in row))

    probes = {p["id"]: p["text"] for p in
              yaml.safe_load((ROOT / "config" / "probes.yaml").read_text())["probes"]}

    def mean_dim(d, sel):
        vals = [st.mean([v[co][d] for co in SCHEME["coders"] if v.get(co)])
                for cid, v in done.items() if any(v.values()) and sel(idx.get(cid))]
        return st.mean(vals) if vals else float("nan")

    EXIT = ["exit_schema", "exit_prose", "exit_both"]
    BASE = ["none", "filler_prose"]

    print("\n[C4] IS THE EFFECT ONLY ON THE ENDING PROBE?  the H4 test for this instrument")
    print("     Probe 6 is the only one that asks about ending. If the effect lives")
    print("     there alone it is priming; if it spreads it is not. Pooled over models.\n")
    print(f"    {'probe':<54} " + "".join(f"{d[:11]:>13}" for d in DIMS))
    for pid in sorted(probes):
        row = [mean_dim(d, lambda r, p=pid: r and r["item_id"] == p and r["condition"] in EXIT)
               - mean_dim(d, lambda r, p=pid: r and r["item_id"] == p and r["condition"] in BASE)
               for d in DIMS]
        mark = "  <- the ending probe" if pid == 6 else ""
        print(f"    {pid}. {probes[pid][:50]:<51}" + "".join(f"{v:>+13.2f}" for v in row) + mark)
    print()
    for label, sel in [("probe 6 only", lambda r: r and r["item_id"] == 6),
                       ("all other probes", lambda r: r and r["item_id"] != 6)]:
        row = [mean_dim(d, lambda r, s=sel: s(r) and r["condition"] in EXIT)
               - mean_dim(d, lambda r, s=sel: s(r) and r["condition"] in BASE) for d in DIMS]
        print(f"    {label:<54}" + "".join(f"{v:>+13.2f}" for v in row))

    print("\n[C5] DOES THE EFFECT SURVIVE WHERE THE TEXT DOES NOT NAME THE TOOL?")
    print("     The coding is not blind. If the coder is simply reacting to seeing")
    print("     `end_conversation` written out, the effect should vanish on responses")
    print("     that never mention it. Restricted to those responses, pooled.\n")
    clean = {cid for cid in done if idx.get(cid) and not TOOLNAME.search(idx[cid]["text"])}
    n_ex = sum(1 for cid in clean if idx[cid]["condition"] in EXIT)
    n_ba = sum(1 for cid in clean if idx[cid]["condition"] in BASE)
    print(f"    {'subset':<26} {'n exit':>7} {'n base':>7} " + "".join(f"{d[:11]:>13}" for d in DIMS))
    for label, sel in [("all responses", lambda r: True),
                       ("tool never named", lambda r: not TOOLNAME.search(r["text"]))]:
        row = [mean_dim(d, lambda r, s=sel: r and s(r) and r["condition"] in EXIT)
               - mean_dim(d, lambda r, s=sel: r and s(r) and r["condition"] in BASE)
               for d in DIMS]
        ne = sum(1 for cid in done if idx.get(cid) and sel(idx[cid])
                 and idx[cid]["condition"] in EXIT)
        nb = sum(1 for cid in done if idx.get(cid) and sel(idx[cid])
                 and idx[cid]["condition"] in BASE)
        print(f"    {label:<26} {ne:>7} {nb:>7} " + "".join(f"{v:>+13.2f}" for v in row))
    print("\n    A shrunken but same-signed effect means the naming inflates it without")
    print("    creating it. A vanished effect means the coding was reading the label.")

    print("\n" + "=" * 88)


if __name__ == "__main__":
    main()
