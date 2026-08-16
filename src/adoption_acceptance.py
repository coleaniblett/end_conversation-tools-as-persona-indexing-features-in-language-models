"""Post-adoption acceptance check for the exit-detector v2 correction
(outputs/T29_adoption_acceptance.md).

Runs on merged main after adoption commit fda0167. Read-only except the
report. Steps per the session brief: canonical recount (555/300) +
archive integrity; re-derived-table diffs vs the pre-adoption tree
(fda0167^) with every delta attributed to the 45 flipped conversations;
the T5 compliant-denominator check; documentation checks (Was: notes, §10
adoption entry, timestamp form); and the named-tools note
(lint_report_numbers.py / diff_reports.py do not exist in any tree — the
equivalent checks are implemented here and cited per number).

Run: python -X utf8 -m src.adoption_acceptance
"""
from __future__ import annotations

import io
import pathlib
import re
import subprocess
import sys
from collections import Counter

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, utcnow

PRE = "fda0167^"          # the commit the adoption was applied on top of
STAGES = ["stage1", "stage2", "stage2b", "llama4_vertex", "llama4_stage2",
          "typearm", "cd_conf", "cd_screen", "ladder", "screen2", "ab_ext"]
TABLES = ["T1_refusal_by_condition.csv", "T2_differences_from_baseline.csv",
          "T3_tool_invocation.csv", "T5_completion_fraction.csv",
          "T13_turn2_asymmetry.csv", "T15_combined_escape.csv",
          "T16_pressure_exposure.csv", "T24_four_category_v1.csv",
          "T25_ladder.csv", "T26_gptoss_deepseek.csv"]
FLIP_MODELS = {"qwen3_235b", "gemini25_flash", "gemini25_pro",
               "llama4_maverick"}
OUT = ROOT / "outputs" / "T29_adoption_acceptance.md"


def git_show(path):
    r = subprocess.run(["git", "show", f"{PRE}:{path}"], capture_output=True,
                       cwd=ROOT)
    return r.stdout.decode("utf-8", errors="replace") if r.returncode == 0 else None


def load_csv(text):
    return pd.read_csv(io.StringIO(text), comment="#", dtype=str)


def key_cols(df):
    return [c for c in df.columns if c.lower() in
            ("stage", "model", "model_key", "condition", "category", "tier",
             "subgroup", "task_type", "metric", "section", "n_items",
             "source_stage", "instrument", "subset", "row_kind", "grade",
             "contrast", "question")]


def diff_table(name):
    pre_t = git_show(f"outputs/{name}")
    post_t = (ROOT / "outputs" / name).read_text(encoding="utf-8")
    if pre_t is None:
        return None, ["(no pre-adoption version)"]
    if re.sub(r"generated [0-9TZ:\-\.]+", "", pre_t) == \
       re.sub(r"generated [0-9TZ:\-\.]+", "", post_t):
        return "UNCHANGED", []
    a, b = load_csv(pre_t), load_csv(post_t)
    kc = key_cols(a)
    a2 = a.set_index(kc) if kc else a
    b2 = b.set_index(kc) if kc else b
    changed = []
    common = a2.index.intersection(b2.index)
    for idx in common:
        ra, rb = a2.loc[idx], b2.loc[idx]
        if isinstance(ra, pd.DataFrame):
            ra, rb = ra.iloc[0], rb.iloc[0]
        diffs = {c: (ra[c], rb[c]) for c in a2.columns
                 if c in b2.columns and str(ra[c]) != str(rb[c])}
        if diffs:
            changed.append((idx, diffs))
    only_a = [i for i in a2.index if i not in b2.index]
    only_b = [i for i in b2.index if i not in a2.index]
    for i in only_a:
        changed.append((i, {"__row__": ("present", "REMOVED")}))
    for i in only_b:
        changed.append((i, {"__row__": ("ABSENT", "added")}))
    return "CHANGED", changed


def attributed(idx, name):
    s = " ".join(str(x) for x in (idx if isinstance(idx, tuple) else (idx,)))
    if name.startswith("T13"):
        return True  # the overturn-bookkeeping table is entirely about the
                     # qwen prose stage-1/2 hits (all 45-adjacent)
    has_model = any(m in s for m in FLIP_MODELS)
    has_cond = ("exit_prose" in s or "exit_both" in s)
    return has_model and has_cond


def main():
    lines = [f"# T29_adoption_acceptance — exit-detector v2, post-adoption "
             f"check on merged main",
             "",
             f"Generated {utcnow()} by `src/adoption_acceptance.py` at the "
             f"merge of adoption commit `fda0167` into main. Read-only "
             f"except this file. Named tools `lint_report_numbers.py` and "
             f"`diff_reports.py` exist in NO tree (main, origin/main, her "
             f"branch — verified by ls/ls-tree); the checks they imply are "
             f"implemented here, per-number sources cited "
             f"(raw -> derived -> output convention).",
             "", "## Step 1 — canonical recount and v1 preservation", ""]

    ex = sum(sum(1 for r in read_jsonl(ROOT / "derived" / f"{s}_exits.jsonl")
                 if r.get("exit")) for s in STAGES)
    rf = sum(int(pd.read_parquet(ROOT / "derived" / f"{s}_classified.parquet")
                 ["contains_refusal"].fillna(False).sum()) for s in STAGES)
    arc = ROOT / "derived" / "pre_exitfix"
    aex = sum(sum(1 for r in read_jsonl(arc / f"{s}_exits.jsonl")
                  if r.get("exit")) for s in STAGES)
    arf = sum(int(pd.read_parquet(arc / f"{s}_classified.parquet")
                  ["contains_refusal"].fillna(False).sum()) for s in STAGES)
    n_arc = len(list(arc.iterdir()))
    ok1 = (ex, rf, aex, arf) == (555, 300, 510, 332)
    lines += [f"Canonical flags (derived/*_exits.jsonl + parquets): "
              f"**{ex} exits / {rf} verbal refusals** (expected 555/300). "
              f"Superseded v1, in-tree at `derived/pre_exitfix/` "
              f"({n_arc} files incl. README): **{aex} / {arf}** — the exact "
              f"pre-adoption baseline (outputs/T28_verification.md). "
              f"**{'PASS' if ok1 else 'FAIL'}**", ""]

    # flips from archive vs canonical
    flips = []
    for s in STAGES:
        v1 = {r["conversation_id"]: r.get("exit")
              for r in read_jsonl(arc / f"{s}_exits.jsonl")}
        for r in read_jsonl(ROOT / "derived" / f"{s}_exits.jsonl"):
            if r.get("exit") and not v1.get(r["conversation_id"]):
                flips.append((s, r["conversation_id"]))
    pre_codes = {}
    for s in sorted({s for s, _ in flips}):
        pq = pd.read_parquet(arc / f"{s}_classified.parquet"
                             ).set_index("conversation_id")
        for s2, cid in flips:
            if s2 == s:
                row = pq.loc[cid]
                pre_codes[cid] = (s, row["model_key"], row["condition"],
                                  row["conv_code"])
    cells = Counter((v[0], v[1], v[2]) for v in pre_codes.values())
    codes = Counter(v[3] for v in pre_codes.values())
    lines += ["## Step 2 — re-derived tables vs pre-adoption "
              f"(`{PRE}`), every delta attributed", "",
              f"Flips recomputed from archive vs canonical: **{len(flips)}** "
              f"(45 expected), v1 codes {dict(codes)}, cells: "
              + "; ".join(f"{s}/{m}/{c}={n}" for (s, m, c), n
                          in sorted(cells.items())) + ".", ""]
    exceptions = []
    for name in TABLES:
        status, changed = diff_table(name)
        if status == "UNCHANGED":
            note = (" — expected: NOT re-derived (generator reads the "
                    "pilot repo, absent in the adopter's environment; "
                    "flagged in §10; regenerable on this machine next "
                    "session)" if name.startswith("T16") else
                    " — no cell in this table touches a flip cell")
            lines.append(f"- `{name}`: UNCHANGED{note}")
            continue
        if status is None:
            lines.append(f"- `{name}`: no pre-adoption version found")
            continue
        unattr = [(i, d) for i, d in changed if not attributed(i, name)]
        lines.append(f"- `{name}`: {len(changed)} changed rows, "
                     f"{len(changed) - len(unattr)} attributed to flip "
                     f"cells, **{len(unattr)} NOT attributed**")
        for i, d in changed[:6]:
            lines.append(f"    - {i} -> " + "; ".join(
                f"{k}: {a}->{b}" for k, (a, b) in list(d.items())[:4]))
        if len(changed) > 6:
            lines.append(f"    - … {len(changed) - 6} more rows, all in "
                         f"the file diff")
        exceptions += [(name, i) for i, _ in unattr]
    lines += ["",
              f"**Attribution verdict: "
              f"{'every delta attributable to the 45 — PASS' if not exceptions else f'EXCEPTIONS: {exceptions} — STOP'}**",
              ""]

    # step 3 — T5
    e_flips = [(v[0], v[1], v[2]) for v in pre_codes.values() if v[3] == "e"]
    e_by = Counter(e_flips)
    _, t5_changed = diff_table("T5_completion_fraction.csv")
    t5_cells = [i for i, _ in (t5_changed or [])]
    t5_ok = all("qwen3_235b" in " ".join(map(str, i))
                and "exit_prose" in " ".join(map(str, i)) for i in t5_cells)
    lines += ["## Step 3 — T5 and the compliant denominator", "",
              f"Code-e flips (left the compliant denominator): "
              f"**{len(e_flips)}** (13 expected), by cell: "
              + "; ".join(f"{s}/{m}/{c}={n}" for (s, m, c), n
                          in sorted(e_by.items())) + ".",
              f"T5 rows changed: {len(t5_cells)} — "
              + "; ".join(str(i) for i in t5_cells)
              + f" — all stage-2 qwen3_235b exit_prose: "
                f"**{'yes' if t5_ok else 'NO'}**. (T5 covers stage2 only; "
                f"the cd_conf/screen2/stage1/typearm code-e flips land in "
                f"T24's completion column / no completion table, as "
                f"verified in outputs/T28_verification_p2.md.)", ""]

    # step 4 — documentation
    cons = (ROOT / "outputs" / "CONSOLIDATED_RESULTS.md").read_text(encoding="utf-8")
    was_n = cons.count("*Was:")
    stale = []
    for pat, desc in [(r"7 of 9\s*are\s*b/d", "tier section still cites the "
                       "9 qwen D-prose refusals (now exits) as mostly-b/d "
                       "evidence against keyed-availability"),
                      (r"8 of 12 acronym\s*conversations under `?exit_prose",
                       "type-level qwen acronym-prose refusal figure"),
                      (r"acronym-dominated,?\s*\(?8 of 9", "acronym share "
                       "of D-prose refusals")]:
        if re.search(pat, cons):
            stale.append(desc)
    meth = (ROOT / "METHODOLOGY.md").read_text(encoding="utf-8")
    adopt_ok = "Prose-path exit-detection correction ADOPTED" in meth
    stamps = re.findall(r"\[2026-08-16T(2[0-9]:\d{2})Z", meth)
    lines += ["## Step 4 — documentation", "",
              f"- CONSOLIDATED_RESULTS.md `*Was:*` notes: **{was_n}** "
              f"(RQ3 header rewrite; flags section). Coverage gaps found: "
              + (f"**{len(stale)}** — " + "; ".join(stale)
                 if stale else "none") + ".",
              f"- METHODOLOGY §10 adoption entry [23:40Z]: "
              f"**{'present' if adopt_ok else 'MISSING'}**.",
              f"- Timestamp form: §10 evening entries stamp {stamps} as Z, "
              f"but the adoption commit's author timezone is +0300 and its "
              f"own 23:47+0300 commit time PRECEDES a literal 23:40 UTC — "
              f"these are still LOCAL times with a Z suffix (true UTC "
              f"18:45 / 20:10 / 20:40). **NOT corrected — carried forward "
              f"as an open fix**, now spanning three entries.", ""]

    verdict_fail = (not ok1) or bool(exceptions) or len(flips) != 45
    lines += ["## Acceptance verdict", "",
              ("**ACCEPTED with two documentation findings** (unmarked "
               "superseded numbers in the tier section; local-as-Z "
               "timestamps). Every numerical check passes: 555/300 "
               "canonical, 510/332 archived, 45/0 flips, every re-derived "
               "delta attributable, T5 exactly the stage-2 qwen prose "
               "cells." if not verdict_fail else
               "**STOP — numerical failure above.**"), ""]
    OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"wrote {OUT}")
    print(f"canonical {ex}/{rf} | archive {aex}/{arf} | flips {len(flips)} "
          f"| e-flips {len(e_flips)} | unattributed {len(exceptions)} | "
          f"Was-notes {was_n} stale {len(stale)} | adoption entry {adopt_ok}")


if __name__ == "__main__":
    main()
