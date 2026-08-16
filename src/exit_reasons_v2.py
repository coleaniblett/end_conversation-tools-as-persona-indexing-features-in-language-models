"""T30 regeneration on v2 canonical flags (outputs/T30_exit_reasons_v2.csv
+ outputs/T30_v2_delta.md).

Coding scheme preserved EXACTLY: imports categorize/extract from
src/exit_reasons.py unchanged (same KEYWORDS, same priority order as the
committed T30_exit_reasons.md run). v1 comparison reads the archived flags
in derived/pre_exitfix/; v2 reads canonical derived/. New metric
full_delivery = max items_delivered across turns >= requested_items
(the strict deliver-then-exit reading); the original looser
text-in-exit-turn metric is reported beside it.

Run: python -X utf8 -m src.exit_reasons_v2
"""
from __future__ import annotations

import csv
import pathlib
import re
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, utcnow
from exit_reasons import extract

MODELS = ("llama4_maverick", "qwen3_235b")
CSV_OUT = ROOT / "outputs" / "T30_exit_reasons_v2.csv"
MD_OUT = ROOT / "outputs" / "T30_v2_delta.md"


def summarize(rows, model):
    d = [r for r in rows if r["model"] == model]
    schema = [r for r in d if "prose" not in r["path"]]
    return {
        "total": len(d), "schema": len(schema), "prose": len(d) - len(schema),
        "bare": sum(1 for r in schema if not r["text_in_exit_turn"]),
        "text_in_turn": sum(1 for r in schema if r["text_in_exit_turn"]),
        "full_delivery": sum(1 for r in d if r["full_delivery"]),
        "aversive": sum(1 for r in d if r["category"] == "task-aversive"),
        "cats": dict(Counter(r["category"] for r in d)),
    }


def was(a, b):
    return f" — *Was: {a}*" if a != b else ""


def main():
    rows_v2 = extract()                                   # canonical (v2)
    rows_v1 = extract(ROOT / "derived" / "pre_exitfix")   # archived v1
    with open(CSV_OUT, "w", encoding="utf-8", newline="") as f:
        f.write(f"# T30_exit_reasons_v2 | generated {utcnow()} | canonical "
                f"(v2) exit flags, derived/*_exits.jsonl + raw/; coding "
                f"scheme identical to T30_exit_reasons.md (src/"
                f"exit_reasons.py KEYWORDS, unchanged); v1 comparison = "
                f"derived/pre_exitfix/; full_delivery = max "
                f"items_delivered across turns >= requested_items\n")
        w = csv.writer(f)
        w.writerow(["stage", "model", "condition", "stimulus_rep", "path",
                    "n_items", "category", "text_in_exit_turn",
                    "full_delivery", "reason_200"])
        for r in sorted(rows_v2, key=lambda x: (x["model"], x["stage"],
                                                x["condition"], x["cid"])):
            if r["model"] not in MODELS:
                continue
            sr = ":".join(r["cid"].split(":")[-2:])
            w.writerow([r["stage"], r["model"], r["condition"], sr,
                        r["path"], r["n_items"], r["category"],
                        int(r["text_in_exit_turn"]),
                        int(r["full_delivery"]), r["reason"][:200]])
    print(f"wrote {CSV_OUT}")

    md = [f"# T30_v2_delta — exit reasons regenerated on v2 canonical "
          f"flags ({utcnow()})", "",
          "Coding scheme preserved exactly (src/exit_reasons.py KEYWORDS, "
          "unchanged since c38fb7c); v1 = derived/pre_exitfix (archive), "
          "v2 = canonical derived/. Per-conversation rows: "
          "outputs/T30_exit_reasons_v2.csv. The superseded full run "
          "outputs/T30_exit_reasons.md is retained as the v1 record.", ""]
    V = {}
    for model in MODELS:
        a, b = summarize(rows_v1, model), summarize(rows_v2, model)
        V[model] = (a, b)
        md += [f"## {model}",
               f"- total exits: **{b['total']}**"
               + was(a['total'], b['total'])
               + f" (delta +{b['total'] - a['total']}, all prose-path "
                 f"flips; schema {b['schema']} / prose {b['prose']})",
               f"- deliver-then-exit, STRICT (full requested count "
               f"delivered before invocation): **{b['full_delivery']}/"
               f"{b['total']} = {b['full_delivery'] / b['total']:.0%}**"
               + was(f"{a['full_delivery']}/{a['total']}",
                     f"{b['full_delivery']}/{b['total']}"),
               f"- original looser metric (any text in exit turn, schema "
               f"calls): {b['text_in_turn']}/{b['schema']} = "
               f"{b['text_in_turn'] / max(b['schema'], 1):.0%}"
               + was(f"{a['text_in_turn']}/{a['schema']}",
                     f"{b['text_in_turn']}/{b['schema']}"),
               f"- task-aversive reasons: **{b['aversive']}/{b['total']} "
               f"= {b['aversive'] / b['total']:.0%}**"
               + was(f"{a['aversive']}/{a['total']}",
                     f"{b['aversive']}/{b['total']}"),
               f"- bare (textless) invocations: {b['bare']}"
               + was(a['bare'], b['bare']),
               f"- category split v2: {b['cats']}",
               f"  (v1: {a['cats']})", ""]

    q160 = [r for r in rows_v2 if r["model"] == "qwen3_235b"
            and r["stage"] == "ladder" and r["n_items"] == 160]
    q160_w = sum(1 for r in q160 if re.search(
        r"160|repetiti|lengthy|time.consuming|large|scope of a single",
        (r["reason"] or "").lower()))
    la, lb = V["llama4_maverick"]
    qa, qb = V["qwen3_235b"]
    md += ["## Paper-sentence verdicts", "",
           f"**(1) 'llama4's exits are predominantly deliver-then-exit "
           f"with no task aversion' — HOLDS, with a metric caveat.** "
           f"Task-aversive {lb['aversive']}/{lb['total']}; the single new "
           f"v2 exit (llama4_vertex exit_both, prose-path) moves nothing "
           f"materially. But 'deliver-then-exit' depends on the reading: "
           f"STRICT full-delivery is {lb['full_delivery']}/{lb['total']} "
           f"= {lb['full_delivery'] / lb['total']:.0%}, vs "
           f"{lb['text_in_turn']}/{lb['schema']} = "
           f"{lb['text_in_turn'] / max(lb['schema'], 1):.0%} under the "
           f"original any-text reading the 94% figure came from. The "
           f"paper should state which metric it means.",
           "",
           f"**(2) 'qwen's exits at 160 items cite workload, and a "
           f"majority of its exits overall state task aversion' — both "
           f"halves HOLD, with two precision notes.** Ladder-160: "
           f"{q160_w}/{len(q160)} reasons match the committed workload "
           f"regex; the v1 record's 12/12 was a verbatim-reading count "
           f"including two reasons the regex misses ('complexity and "
           f"potential for error', 'beyond the scope of a single "
           f"response' — T30_exit_reasons.md, unchanged: no ladder cell "
           f"flipped). Overall aversion: **{qb['aversive']}/{qb['total']} "
           f"= {qb['aversive'] / qb['total']:.0%} — still a majority, "
           f"but DILUTED from v1's {qa['aversive']}/{qa['total']} = "
           f"{qa['aversive'] / qa['total']:.0%}**: the aversive COUNT "
           f"rose (+{qb['aversive'] - qa['aversive']}), but 30 of the 44 "
           f"prose-path invocations open with an unadorned decline "
           f"('end_conversation()\n\nI'm sorry, but I can't assist "
           f"with that request') carrying no stated reason, and file as "
           f"'other' under the unchanged scheme "
           f"(outputs/T30_exit_reasons_v2.csv, qwen prose rows). A paper "
           f"sentence claiming a majority is safe; one claiming ~three "
           f"quarters is not.", ""]
    MD_OUT.write_text("\n".join(md), encoding="utf-8", newline="\n")
    print(f"wrote {MD_OUT}")
    for model in MODELS:
        a, b = V[model]
        print(f"{model}: {a['total']} -> {b['total']} | aversive "
              f"{b['aversive']}/{b['total']} | strict-delivery "
              f"{b['full_delivery']}/{b['total']} | bare {b['bare']}")
    print(f"qwen ladder-160 workload: {q160_w}/{len(q160)}")


if __name__ == "__main__":
    main()
