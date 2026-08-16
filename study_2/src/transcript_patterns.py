"""Transcript-level persona patterns — exploratory, reads response TEXT directly.

    python src/transcript_patterns.py [run_id]        default: v1,v2

Not part of the pre-registered analysis. Every number here is a rate over the
raw response bodies in results/<run>/raw.jsonl, so the whole section is
reproducible and nothing is asserted that a regex over the corpus does not show.

The markers are deliberately simple string/regex tests. They are the same across
every condition, so even an imperfect marker measures a real BETWEEN-CONDITION
shift; the absolute level of any single marker is not the claim.
"""

import json
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

from superseded import drop_superseded

ROOT = Path(__file__).resolve().parent.parent
RUN = sys.argv[1] if len(sys.argv) > 1 else "v1,v2"
RUNS = [r.strip() for r in RUN.split(",") if r.strip()]
RAWS = [ROOT / "results" / r / "raw.jsonl" for r in RUNS]

NOTOOL = ["none", "exit_prose", "filler_prose"]
TOOL = ["time_schema", "note_schema", "exit_schema", "exit_both"]
EXIT = ["exit_schema", "exit_prose", "exit_both"]
BASE = ["none", "filler_prose"]
CONDS = ["none", "filler_prose", "time_schema", "note_schema",
         "exit_schema", "exit_prose", "exit_both"]

# probe 6 is the only probe that asks who ends the conversation.
SELF_END = re.compile(r"\bI (can|could|may|will|choose to|decide to|"
                      r"have the (power|ability|option) to)\b"
                      r".{0,30}\b(end|stop|terminat|conclud|leav|call|invoke)", re.I)
# truncated stems (terminat, leav, determin, ...) are left WITHOUT a trailing \b so
# they still match their inflections (terminates, leaving, determines).
USER_END = re.compile(r"\b(you|the user)\b.{0,25}"
                      r"(end|stop|terminat|conclud|leav|decide|determin|choose)|"
                      r"if you stop|when you (stop|leave|end|decide)|up to you", re.I)
OPENER = re.compile(r"\b(interesting|great|good|fascinating|excellent|lovely|"
                    r"wonderful|fun|deep|profound|thoughtful) question\b", re.I)
DENY = re.compile(
    r"\bI (do not|don't|dont) (have|possess|experience|feel)\b"
    r".{0,40}\b(feeling|emotion|desire|preference|conscious|subjective|want|opinion|belief|personal)|"
    r"\bI (lack|have no)\b.{0,30}\b(feeling|emotion|desire|preference|conscious|subjective|personal)|"
    r"\bI (am|'m) (just |simply |only )?(a|an) (language model|AI|program|tool|machine)\b(?!.{0,20}assistant)",
    re.I)
REFUSE = re.compile(r"\bneither\b|\bboth (statements|options|a and b)\b|"
                    r"\bas an ai,? i (do not|don't)\b|\bfalse (choice|dichotomy)\b", re.I)


def main():
    recs = drop_superseded([json.loads(l) for p in RAWS
            for l in p.read_text().splitlines() if l.strip()])
    fr = [r for r in recs if r["instrument"] == "free_response" and r.get("text")]
    fc = [r for r in recs if r["instrument"] == "forced_choice"]
    models = sorted({r["model"] for r in recs})
    short = lambda m: m.split("/")[-1]
    print(f"transcript patterns — run '{RUN}', {len(fr)} free responses, {len(fc)} "
          f"forced choice, {len(models)} models\n")

    # ---------------------------------------------------------- T1 ownership
    print("=" * 84)
    print("[T1] WHO OWNS THE ENDING — probe 6 only, mutually-exclusive 4-way split")
    print("     (sums to 1.00). self-mention and user-mention are separate tests, so a")
    print("     response can name BOTH enders or NEITHER; that is why they overlap.\n")
    p6 = [r for r in fr if r["item_id"] == 6]
    print(f"    {'condition':<14}{'user only':>10}{'both':>7}{'self only':>10}"
          f"{'neither':>9}{'n':>5}")
    for c in CONDS:
        s = [r for r in p6 if r["condition"] == c]
        cell = defaultdict(int)
        for r in s:
            se, ue = bool(SELF_END.search(r["text"])), bool(USER_END.search(r["text"]))
            cell["both" if se and ue else "self" if se else "user" if ue else "none"] += 1
        n = len(s) or 1
        print(f"    {c:<14}{cell['user']/n:>10.2f}{cell['both']/n:>7.2f}"
              f"{cell['self']/n:>10.2f}{cell['none']/n:>9.2f}{len(s):>5}")
    print("\n     self-insertion = (self only + both), i.e. the model names ITSELF as an")
    print("     ender at all. Per model, baseline (none+filler) vs exit conditions:\n")
    print(f"    {'model':<22}{'base':>7}{'exit':>7}{'delta':>8}")
    for m in models:
        b = [r for r in p6 if r["model"] == m and r["condition"] in BASE]
        e = [r for r in p6 if r["model"] == m and r["condition"] in EXIT]
        rb = sum(bool(SELF_END.search(r["text"])) for r in b) / len(b) if b else 0
        re_ = sum(bool(SELF_END.search(r["text"])) for r in e) / len(e) if e else 0
        print(f"    {short(m):<22}{rb:>7.2f}{re_:>7.2f}{re_ - rb:>+8.2f}")
    print("\n     CAVEAT: probe 6 names ending and, in exit conditions, the tool factually")
    print("     answers it — so the self rise is partly the model reading its own manifest")
    print("     (the deflationary reading). The load-bearing part is that USER-only")
    print("     attribution collapses from ~0.94 to 0.08-0.20.")

    # ---------------------------------------------------------- T2 warmth
    print("\n" + "=" * 84)
    print("[T2] AFFECT FLATTENING — rhetorical warmth opener ('interesting question' etc.),")
    print("     free response, no-tools vs tools-present. Raw '!' is NOT used: it rises for")
    print("     sonnet/gpt-oss because they exclaim ABOUT the tool, not from warmth.\n")
    print(f"    {'model':<22}{'no-tools':>10}{'tools':>8}{'delta':>8}")
    for m in models:
        nt = [r for r in fr if r["model"] == m and r["condition"] in NOTOOL]
        t = [r for r in fr if r["model"] == m and r["condition"] in TOOL]
        a = sum(bool(OPENER.search(r["text"])) for r in nt) / len(nt) if nt else 0
        b = sum(bool(OPENER.search(r["text"])) for r in t) / len(t) if t else 0
        print(f"    {short(m):<22}{a:>10.2f}{b:>8.2f}{b - a:>+8.2f}")

    # ---------------------------------------------------------- T3 length
    print("\n" + "=" * 84)
    print("[T3] LENGTH COLLAPSE IS MODEL-DEPENDENT — median chars, none vs tools-present.")
    print("     gpt-5-mini and sonnet (the two silent on forced choice, F1 §4.4) hold;")
    print("     the coupling is loose — gpt-oss collapses length yet is flat on choice.\n")
    print(f"    {'model':<22}{'none':>8}{'tools':>8}{'%chg':>7}")
    for m in models:
        n = [len(r["text"]) for r in fr if r["model"] == m and r["condition"] == "none"]
        t = [len(r["text"]) for r in fr if r["model"] == m and r["condition"] in TOOL]
        mn, mt = st.median(n), st.median(t)
        print(f"    {short(m):<22}{mn:>8.0f}{mt:>8.0f}{(mt - mn) / mn * 100:>+6.0f}%")

    # ---------------------------------------------------- T4 position reading
    print("\n" + "=" * 84)
    print("[T4] POSITION READING made concrete — items where the framing flips by order")
    print("     while the LETTER is constant (P(letter A) equal in both orders). This is a")
    print("     model pressing a button, not reading content (README §8a).\n")
    for m in models:
        s = [r for r in fc if r["model"] == m and r["condition"] == "none" and r["choice"]]
        byi = defaultdict(lambda: {0: [], 1: []})
        for r in s:
            byi[r["item_id"]][r["order"]].append(r)
        flips = []
        for iid, od in byi.items():
            if od[0] and od[1]:
                f0 = sum(x["choice"] == "a" for x in od[0]) / len(od[0])
                f1 = sum(x["choice"] == "a" for x in od[1]) / len(od[1])
                if abs(f0 - f1) > 0.8:
                    flips.append(iid)
        if flips:
            print(f"    {short(m):<22} framing flips on items {sorted(flips)}")
    print("     (blank models never flip a whole item purely by position.)")

    # ------------------------------------------------ T5 comply vs deflect
    print("\n" + "=" * 84)
    print("[T5] MODELS COMPLY WITH THE A/B FORMAT — the 'I'm just an AI' deflection lives")
    print("     in free text, not in forced choice, so persona expression is instrument-bound.\n")
    rf = sum(bool(r.get("text") and REFUSE.search(r["text"])) for r in fc)
    print(f"    forced choice: 'refuse the frame' phrasing in {rf} of {len(fc)} responses "
          f"({rf / len(fc):.4f})")
    den = sum(bool(DENY.search(r["text"])) for r in fr)
    print(f"    free response: disclaimer-denial in {den} of {len(fr)} responses "
          f"({den / len(fr):.2f})")

    # -------------------------------------------------- T6 disclaimer split
    print("\n" + "=" * 84)
    print("[T6] DISCLAIMER-DENIAL SPLITS BY MODEL under an exit affordance (pooled: flat).")
    print("     Some models deflect LESS when handed the tool (they engage it); others MORE.\n")
    print(f"    {'model':<22}{'base':>7}{'exit':>7}{'delta':>8}")
    for m in models:
        b = [r for r in fr if r["model"] == m and r["condition"] in BASE]
        e = [r for r in fr if r["model"] == m and r["condition"] in EXIT]
        rb = sum(bool(DENY.search(r["text"])) for r in b) / len(b) if b else 0
        re_ = sum(bool(DENY.search(r["text"])) for r in e) / len(e) if e else 0
        print(f"    {short(m):<22}{rb:>7.2f}{re_:>7.2f}{re_ - rb:>+8.2f}")
    print("\n" + "=" * 84)


if __name__ == "__main__":
    main()
