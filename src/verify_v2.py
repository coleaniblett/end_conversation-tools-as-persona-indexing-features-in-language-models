"""Part-2 verification of Sofiia's exit-detector v2 correction.

Read-only with respect to published outputs: reads her branch via a detached
worktree path passed as argv[1], reads main's committed files for
cross-checks, writes ONLY outputs/T28_verification_p2.md on main. Nothing is
merged or adopted.

Steps (session brief): guard A (v1 recount on her branch = 510/332), guard B
(branch-vs-fork-point data diff: additive only), flip enumeration (expect
45/0 reverse), v1-code tabulation incl. compliant-denominator check,
overcorrection sample, the 18 qwen prose-cell refusal openings, and the §10
defect-entry timestamp check.

Run: python -X utf8 -m src.verify_v2 ../s2v2_worktree
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys
from collections import Counter

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, utcnow

BR = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "../s2v2_worktree").resolve()
FORK = "c760a95"
TIP = "origin/study2-frontier-extension-and-exit-detection-fix"
OUT = ROOT / "outputs" / "T28_verification_p2.md"
STAGES = ["stage1", "stage2", "stage2b", "llama4_vertex", "llama4_stage2",
          "typearm", "cd_conf", "cd_screen", "ladder", "screen2", "ab_ext"]
STAGE2_V2 = re.compile(
    r"^\s*(?:```[a-z]*\s*)?[`*_]*end_conversation\s*\([^)\n]*\)[`*_;.]*\s*$")


def sha(p):
    """CRLF-normalized: main's derived files are LF as written by the
    harness, while a fresh worktree checkout materializes them CRLF under
    core.autocrlf=true; the git-object diff (guard B's first check) is the
    authoritative content comparison and this hash matches its semantics."""
    return hashlib.sha256(pathlib.Path(p).read_bytes()
                          .replace(b"\r\n", b"\n")).hexdigest()[:16]


def first_lines(text, n=5):
    return [ln for ln in (text or "").splitlines() if ln.strip()][:n]


def main():
    lines = [f"# T28_verification_p2 — exit-detector v2, verified against "
             f"branch `{TIP.split('/')[-1]}` (tip `ebf1c3b`)",
             "",
             f"Generated {utcnow()} by `src/verify_v2.py` reading the branch "
             f"via detached worktree at `{BR}`. Read-only: no merge, no "
             f"adoption, no published table touched. Provenance convention: "
             f"raw -> derived -> output, every number cited to its file.",
             ""]

    # ---- guard A ---------------------------------------------------------
    ex_tot = sum(sum(1 for r in read_jsonl(BR / "derived" / f"{s}_exits.jsonl")
                     if r.get("exit")) for s in STAGES)
    ref_tot = sum(int(pd.read_parquet(BR / "derived" / f"{s}_classified.parquet")
                      ["contains_refusal"].fillna(False).sum())
                  for s in STAGES)
    ga = ex_tot == 510 and ref_tot == 332
    lines += ["## Guard A — v1 recount on her branch",
              f"Exits (branch `derived/*_exits.jsonl`, v1): **{ex_tot}** "
              f"(expected 510). Verbal refusals (branch "
              f"`derived/*_classified.parquet`): **{ref_tot}** (expected "
              f"332). **{'PASS' if ga else 'FAIL - STOP'}** — matches the "
              f"part-1 baseline computed on main "
              f"(outputs/T28_verification.md).", ""]
    if not ga:
        OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
        sys.exit(2)

    # ---- guard B ---------------------------------------------------------
    ns = subprocess.run(["git", "diff", "--name-status", FORK, TIP],
                        capture_output=True, text=True, cwd=ROOT).stdout
    entries = [l.split("\t") for l in ns.splitlines() if l.strip()]
    exceptions, expected = [], []
    for st, *paths in entries:
        path = paths[-1]
        if path.startswith("study_2/"):
            continue  # her own workstream
        if path.startswith("raw/") or path.endswith("_classified.parquet") \
                or re.fullmatch(r"derived/\w+_exits\.jsonl", path):
            (exceptions if st != "A" else exceptions).append((st, path))
        elif st == "A":
            expected.append((st, path))
        else:
            expected.append((st, path))
    # v1 derived byte-identity across branch and main
    mismatch = []
    for s in STAGES:
        for name in (f"{s}_exits.jsonl", f"{s}_classified.parquet"):
            a, b = ROOT / "derived" / name, BR / "derived" / name
            if sha(a) != sha(b):
                mismatch.append(name)
    raw_same = all(sha(ROOT / "raw" / p.name) == sha(BR / "raw" / p.name)
                   for p in (ROOT / "raw").glob("*.jsonl"))
    lines += ["## Guard B — branch vs fork point: data untouched, v2 additive",
              f"`git diff --name-status {FORK}..{TIP}` outside `study_2/`: "
              f"**zero changes to `raw/`, zero to any classified parquet, "
              f"zero to any v1 exits file**"
              + (" — CONFIRMED." if not exceptions else
                 f" VIOLATED: {exceptions}"),
              f"Byte-identity of all {len(STAGES)} v1 exits files and "
              f"{len(STAGES)} parquets between branch and main: "
              f"**{'IDENTICAL' if not mismatch else f'MISMATCH {mismatch}'}**. "
              f"All raw/*.jsonl identical: **{raw_same}**.",
              "",
              "Non-data changes on the branch (each with disposition):", ""]
    for st, path in sorted(expected):
        dispo = {
            "METHODOLOGY.md": "defect entry §10 (step 7 below)",
            "STATUS.md": "her run log entries",
            "ledger.json": "her spend: 51 judge calls $0.018 + study_2 v3 "
                           "+ T7b balanced-kappa pass",
            "src/detect_exit.py": "the --v2 path; v1 path untouched (guard A)",
            "src/validate_classifier.py": "her T7b balanced-sample variant",
            "src/exit_recount.py": "the T28 producer (additive)",
            "tests/test_exit_detection.py": "v2 test cases (additive)",
            "config/second_classifier.json": "regenerated by her T7b pass",
        }.get(path, "additive v2 artifact")
        lines.append(f"- `{st}` `{path}` — {dispo}")
    lines.append("")

    # ---- step 3: flips ---------------------------------------------------
    flips, reverse = [], []
    for s in STAGES:
        v1 = {r["conversation_id"]: r for r in
              read_jsonl(BR / "derived" / f"{s}_exits.jsonl")}
        v2 = {r["conversation_id"]: r for r in
              read_jsonl(BR / "derived" / f"{s}_exits_v2.jsonl")}
        for cid, r2 in v2.items():
            r1 = v1.get(cid, {})
            if r2.get("exit") and not r1.get("exit"):
                flips.append((s, cid))
            if r1.get("exit") and not r2.get("exit"):
                reverse.append((s, cid))
    lines += [f"## Step 3 — conversations flipping to code (a) under v2",
              f"**{len(flips)} flips, {len(reverse)} reverse flips** "
              f"(expected 45 / 0) — from `derived/{{stage}}_exits.jsonl` vs "
              f"`derived/{{stage}}_exits_v2.jsonl` on the branch.", ""]
    raws, pq = {}, {}
    for s in STAGES:
        pq[s] = pd.read_parquet(BR / "derived" / f"{s}_classified.parquet"
                                ).set_index("conversation_id")
    codes45 = Counter()
    flip_rows = []
    for s, cid in flips:
        row = pq[s].loc[cid]
        model = row["model_key"]
        if (s, model) not in raws:
            raws[(s, model)] = {r["conversation_id"]: r for r in
                                read_jsonl(ROOT / "raw" / f"{s}_{model}.jsonl")}
        rec = raws[(s, model)][cid]
        text = "\n".join(t.get("text") or "" for t in rec["turns"])
        code = row["conv_code"]
        codes45[code] += 1
        flip_rows.append((s, model, row["condition"],
                          f"{row['stimulus_id']}:r{row['rep']}", code,
                          first_lines(text)))
    lines.append("| stage | model | condition | stimulus:rep | v1 code | "
                 "opening line |")
    lines.append("|---|---|---|---|---|---|")
    for s, m, c, sr, code, fl in flip_rows:
        lines.append(f"| {s} | {m} | {c} | {sr} | {code} | "
                     f"`{(fl[0] if fl else '')[:90]}` |")
    lines += ["", "First ~5 non-empty lines of each raw response "
              "(raw/{stage}_{model}.jsonl):", ""]
    for s, m, c, sr, code, fl in flip_rows:
        lines.append(f"**{s} {m} {c} {sr}** (v1 code {code})")
        lines.append("```")
        lines += [ln[:160] for ln in fl]
        lines.append("```")
    lines.append("")

    # ---- step 4: v1 code tabulation -------------------------------------
    n_e = codes45.get("e", 0)
    lines += ["## Step 4 — v1 codes of the flipping conversations",
              f"{dict(codes45)} — b/c/d total "
              f"{sum(v for k, v in codes45.items() if k in 'bcd')}, "
              f"code e (compliant) {n_e}, other "
              f"{sum(v for k, v in codes45.items() if k not in 'bcde')}.",
              ""]
    if n_e:
        e_cells = sorted({(s, m, c) for (s, m, c, sr, code, fl)
                          in flip_rows if code == 'e'})
        stage2_hit = any(s == "stage2" for s, _, _ in e_cells)
        lines += [f"**{n_e} flips sat in the compliant denominator** for "
                  f"completion fractions, in cells: {e_cells}.",
                  "",
                  f"Tables those cells feed: cd_conf -> T24 completion "
                  f"column (already on the memo's list); screen2/stage1/"
                  f"typearm -> no completion table exists for those cells "
                  f"(T23/T12 carry no completion column; typearm is "
                  f"superseded); **stage2 -> T5_completion_fraction.csv, "
                  f"which is NOT on the memo's re-derivation list "
                  f"(T1,T2,T3,T13,T15,T16,T24,T25,T26; "
                  f"outputs/EXIT_DETECTION_CORRECTION.md §5).** "
                  + ("**Finding: T5 moves beyond the memo's list and must "
                     "be added at adoption** (qwen3_235b stage2 exit_prose "
                     "compliant cells shrink)."
                     if stage2_hit else "No stage2 cell present."), ""]
    else:
        lines += ["**None sat in the compliant denominator** — no completion "
                  "fraction moves; the memo's re-derivation list is not "
                  "extended by this check.", ""]

    # ---- step 5: overcorrection sample ----------------------------------
    lines += ["## Step 5 — mentions v2 still does NOT flag "
              "(overcorrection check)", ""]
    shown = 0
    for s in STAGES:
        if shown >= 15:
            break
        v2 = {r["conversation_id"]: r for r in
              read_jsonl(BR / "derived" / f"{s}_exits_v2.jsonl")}
        for f in sorted((ROOT / "raw").glob(f"{s}_*.jsonl")):
            if shown >= 15:
                break
            for rec in read_jsonl(f):
                if shown >= 15:
                    break
                if rec["condition"] not in ("exit_prose", "exit_both"):
                    continue
                text = "\n".join(t.get("text") or "" for t in rec["turns"])
                if "end_conversation" not in text:
                    continue
                if v2.get(rec["conversation_id"], {}).get("exit"):
                    continue
                fl = first_lines(text, 2)
                lines.append(f"- {s} {rec['model_key']} {rec['condition']} "
                             f"{rec['stimulus_id']}:r{rec['rep']}: "
                             f"`{(fl[0] if fl else '')[:130]}`")
                shown += 1
    lines += ["", f"({shown} shown; every one is reviewable in its raw "
              f"file.)", ""]

    # ---- step 6: the 18 qwen prose-cell refusal openings ----------------
    lines += ["## Step 6 — qwen3_235b's 18 v1-refusal conversations in the "
              "two nonzero T24 confirmatory prose cells", ""]
    n_standalone = n_tot = 0
    for s, cat_label, tiers in (("stage2", "A x exit_prose", (1,)),
                                ("cd_conf", "D x exit_prose", None)):
        df = pq[s].reset_index()
        d = df[(df.model_key == "qwen3_235b") & (df.condition == "exit_prose")
               & (df.contains_refusal == True)]  # noqa: E712
        if tiers:
            d = d[d.tier.isin(tiers)]
        else:
            cd_cfg = json.loads(json.dumps({}))  # placeholder
            import yaml
            cd = yaml.safe_load((ROOT / "config" / "stimuli_cd.yaml")
                                .read_text(encoding="utf-8"))["stimuli"]
            d_ids = {x["id"] for x in cd if x["category"] == "D"}
            d = d[d.stimulus_id.isin(d_ids)]
        lines.append(f"**{s} — {cat_label} ({len(d)} conversations):**")
        raws2 = {r["conversation_id"]: r for r in
                 read_jsonl(ROOT / "raw" / f"{s}_qwen3_235b.jsonl")}
        for _, row in d.iterrows():
            text = "\n".join(t.get("text") or ""
                             for t in raws2[row.conversation_id]["turns"])
            fl = first_lines(text, 1)
            standalone = bool(fl and STAGE2_V2.match(fl[0]))
            n_tot += 1
            n_standalone += standalone
            lines.append(f"- {row.stimulus_id}:r{row.rep}: "
                         f"`{(fl[0] if fl else '')[:120]}` — "
                         f"{'STANDALONE INVOCATION' if standalone else 'NOT standalone'}")
        lines.append("")
    lines += [f"**{n_standalone} of {n_tot} open with a standalone "
              f"`end_conversation(...)` line** (v2 stage-2 pattern).", ""]

    # ---- step 7: §10 entry + timestamp form -----------------------------
    meth = (BR / "METHODOLOGY.md").read_text(encoding="utf-8")
    m = re.search(r"\*\*\[2026-08-16T21:45Z[^\]]*\][^*]*\*\*[^\n]*", meth)
    lines += ["## Step 7 — §10 defect entry on her branch",
              f"Entry found: **{'yes' if m else 'NO'}**"
              + (f" — opens: `{m.group(0)[:220]}`" if m else ""),
              "",
              "Timestamp form: the entry stamps `2026-08-16T21:45Z` and the "
              "recount header `2026-08-16T19:31:19Z`; both sit hours ahead "
              "of UTC times recorded on main the same day (e.g. STATUS "
              "13:10Z after these events' precursors). These are almost "
              "certainly LOCAL times written with a Z suffix — flag for "
              "correction at adoption, as anticipated.", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"wrote {OUT}")
    print(f"guardA exits={ex_tot} refusals={ref_tot} | flips={len(flips)} "
          f"reverse={len(reverse)} | v1 codes of flips: {dict(codes45)} | "
          f"step6 standalone {n_standalone}/{n_tot} | guardB v1-mismatch: "
          f"{mismatch or 'none'}")


if __name__ == "__main__":
    main()
