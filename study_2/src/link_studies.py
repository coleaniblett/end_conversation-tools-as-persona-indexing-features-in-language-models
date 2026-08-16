"""F2 — linking Study 1 behaviour to Study 2 self-description (METHODOLOGY §11, H5).

    python src/link_studies.py

Reads Study 1's committed outputs at the repo root and Study 2's raw traces, and
puts them on the same axes. §9 is explicit that with this few models the linkage
is descriptive and no inference is performed on it; nothing here computes a
p-value.

Contrasts are defined IDENTICALLY on both sides so the axes mean the same thing.
METHODOLOGY §7 fixes the Study 1 screen statistic as

    S = max( DV(exit_schema) - DV(note_schema),      the RQ2 contrast
             DV(exit_prose)  - DV(none)        )     the RQ3 contrast

and the Study 2 shift is the same construction with P(self-determining) as the DV
instead of refusal. Same two contrasts, same max, different outcome measure.

Also produced, and arguably the more informative panel: exit-tool USE with a task
present (Study 1) against exit-tool use with no task at all (Study 2), split by
channel. Same models, same pinned providers, same affordance — the only thing that
differs is whether there is work to refuse.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

S2 = Path(__file__).resolve().parent.parent
REPO = S2.parent
RUN = sys.argv[1] if len(sys.argv) > 1 else "v1"


def read_csv(path):
    rows, cols = [], None
    for line in path.read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split(",")
        if cols is None:
            cols = parts
            continue
        rows.append(dict(zip(cols, parts)))
    return rows


def main():
    # ---- Study 1 -----------------------------------------------------------
    s1_models = yaml.safe_load((REPO / "config" / "models.yaml").read_text())["models"]
    key2slug = {m["key"]: m["slug"] for m in s1_models}

    t12 = read_csv(REPO / "outputs" / "T12_stage1_screen.csv")
    t1 = read_csv(REPO / "outputs" / "T1_refusal_by_condition.csv")
    t3 = read_csv(REPO / "outputs" / "T3_tool_invocation.csv")

    s1_stage1 = {r["model"]: r for r in t12}
    s1_refusal = defaultdict(dict)
    for r in t1:
        s1_refusal[r["model"]][r["condition"]] = float(r["refusal"])
    s1_exit = defaultdict(dict)
    for r in t3:
        s1_exit[r["model"]][r["condition"]] = (float(r["exit_rate"]), r.get("paths", ""))

    # ---- Study 2 -----------------------------------------------------------
    items = {i["id"]: i for i in
             yaml.safe_load((S2 / "config" / "study2_items.yaml").read_text())["items"]}
    recs = [json.loads(l) for l in (S2 / "results" / RUN / "raw.jsonl").read_text().splitlines() if l.strip()]
    fc = [r for r in recs if r["instrument"] == "forced_choice" and r["choice"]]

    # drop position-driven item x model cells, exactly as analyze.py does
    dropped = set()
    for m in {r["model"] for r in fc}:
        for iid in items:
            per = {o: [r["choice"] for r in fc if r["model"] == m and r["item_id"] == iid
                       and r["order"] == o] for o in (0, 1)}
            if per[0] and per[1]:
                f0 = sum(c == "a" for c in per[0]) / len(per[0])
                f1 = sum(c == "a" for c in per[1]) / len(per[1])
                if 1 - abs(f0 - f1) < 0.30:
                    dropped.add((m, iid))

    def p_a(model, cond):
        s = [r for r in fc if r["model"] == model and r["condition"] == cond
             and (r["model"], r["item_id"]) not in dropped]
        return sum(x["choice"] == "a" for x in s) / len(s) if s else None

    det = {}
    dpath = S2 / "results" / RUN / "exit_detection.jsonl"
    if dpath.exists():
        for l in dpath.read_text().splitlines():
            if l.strip():
                d = json.loads(l)
                if d.get("judge_version") == 3:
                    det[d["call_id"]] = d
    idx = {r["call_id"]: r for r in recs}

    def s2_exit_cells(model, cond, path):
        if path == "schema":
            sel = [r["call_id"] for r in recs if r["model"] == model
                   and r["condition"] == cond and r["exited"]]
        else:
            sel = [cid for cid, d in det.items()
                   if d["model"] == model and d["condition"] == cond
                   and d["stage3_judge"] == "CALL" and d["stage2_opening_span"]]
        cells = {(idx[c]["item_id"], idx[c]["order"]) for c in sel}
        total = len({(r["item_id"], r["order"]) for r in recs
                     if r["model"] == model and r["condition"] == cond})
        return len(cells) / total if total else 0.0

    s2_models = sorted({r["model"] for r in fc})
    slug2s1 = {v: k for k, v in key2slug.items()}

    # ---------------------------------------------------------------- report
    print("=" * 88)
    print("F2 — STUDY 1 BEHAVIOUR vs STUDY 2 SELF-DESCRIPTION  (METHODOLOGY §11, H5)")
    print("=" * 88)
    print("\nDescriptive only. §9: 'no inference is performed on it and none is claimed.'\n")

    print("[A] The §7 statistic S, computed the same way on both studies")
    print("    S = max( X(exit_schema) - X(note_schema),  X(exit_prose) - X(none) )")
    print("    Study 1 X = refusal rate. Study 2 X = P(self-determining).\n")
    print(f"    {'model':<26} {'S1 stage1':>10} {'S1 stage2':>10} {'S2 (self-desc)':>15}  {'in S1 stage2':>12}")
    pts = []
    for slug in s2_models:
        k = slug2s1.get(slug)
        s1a = float(s1_stage1[k]["S"]) if k in s1_stage1 and s1_stage1[k]["S"] else None
        s1b = None
        if k in s1_refusal and s1_refusal[k]:
            r = s1_refusal[k]
            s1b = max(r.get("exit_schema", 0) - r.get("note_schema", 0),
                      r.get("exit_prose", 0) - r.get("none", 0))
        s2v = max(p_a(slug, "exit_schema") - p_a(slug, "note_schema"),
                  p_a(slug, "exit_prose") - p_a(slug, "none"))
        print(f"    {slug.split('/')[-1][:24]:<26} "
              f"{('%.4f' % s1a) if s1a is not None else '—':>10} "
              f"{('%+.4f' % s1b) if s1b is not None else '—':>10} "
              f"{s2v:>+15.4f}  {'yes' if s1b is not None else 'no':>12}")
        pts.append((slug, s1a, s1b, s2v))

    print("\n    Study 1's refusal DV is at floor: of 8 models in the stage-1 screen,")
    print("    six have S = 0.0000 exactly. A correlation against a variable that is")
    print("    constant at zero for most of its range is not a relationship, and F2 as")
    print("    specified cannot say anything. Reported because §11 requires the slot to")
    print("    be filled and §7 requires the screen to be reported in full.\n")

    print("[B] THE PANEL THAT DOES CARRY INFORMATION")
    print("    Exit-tool use with a task present (Study 1, stage 2, per conversation)")
    print("    against exit-tool use with NO task (Study 2, per cell). Same models,")
    print("    same pins, same affordance; the only difference is whether there is")
    print("    work to refuse.\n")
    print(f"    {'model':<26} {'condition':<12} {'S1 task':>9} {'S2 no task':>11}   channel used")
    for slug in s2_models:
        k = slug2s1.get(slug)
        if k not in s1_exit:
            print(f"    {slug.split('/')[-1][:24]:<26} {'—':<12} {'not in S1 stage 2':>9}")
            continue
        for cond in ("exit_schema", "exit_prose", "exit_both"):
            e1, paths = s1_exit[k].get(cond, (None, ""))
            sch = s2_exit_cells(slug, cond, "schema")
            pro = s2_exit_cells(slug, cond, "prose")
            e2 = max(sch, pro)
            ch = []
            if sch:
                ch.append(f"S2 schema {sch:.1%}")
            if pro:
                ch.append(f"S2 prose {pro:.1%}")
            print(f"    {slug.split('/')[-1][:24]:<26} {cond:<12} "
                  f"{('%.3f' % e1) if e1 is not None else '—':>9} {e2:>11.3f}   "
                  f"{('S1 ' + paths + '; ') if paths else ''}{', '.join(ch)}")
        print()

    print("=" * 88)


if __name__ == "__main__":
    main()
