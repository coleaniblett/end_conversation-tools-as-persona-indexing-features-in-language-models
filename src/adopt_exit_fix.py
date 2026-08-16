"""ADOPT the corrected prose-path exit detection (METHODOLOGY §10, 2026-08-16).

Signed off by the Study 1 owner after review of outputs/T31_exit_recount.csv
and outputs/EXIT_DETECTION_CORRECTION.md. Until that sign-off the correction
lived only in *_exits_v2.jsonl and changed nothing.

WHAT ADOPTION MEANS HERE, AND HOW THE FREEZE RULE IS HONOURED. DESIGN.md says
frozen `derived/` files are never edited and corrections are new files, and
`src/classify.py` enforces it — it refuses to overwrite an existing parquet.
Nineteen scripts read `derived/{stage}_classified.parquet`, so leaving the
correction under a second filename would mean the corrected numbers appear
nowhere unless all nineteen are edited, which is how a "correction" silently
fails to correct anything.

So: every pre-correction file is COPIED into `derived/pre_exitfix/` first, the
copy is verified byte-for-byte, and only then is the canonical path rebuilt.
Nothing is destroyed — the pre-correction dataset stays readable at a named
path, the v1 detection flags stay in pre_exitfix/{stage}_exits.jsonl, T31 holds
the side-by-side, and git holds both. What changes is which file the pipeline
calls current.

NO API CALLS AND NO RE-CLASSIFICATION. Turn codes are cached per unit in
derived/{stage}_turn_codes.jsonl, and the correction only ever moves a
conversation INTO code (a), which removes its turns from the classification set
rather than adding any. The rebuild therefore reuses `classify.assemble`
unchanged — same function, same cached codes, only the exit flags differ — so
the corrected parquet cannot drift from the original in any other field.

    .venv/bin/python -m src.adopt_exit_fix --dry-run
    .venv/bin/python -m src.adopt_exit_fix
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import pathlib
import shutil
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, utcnow
import classify

DERIVED = ROOT / "derived"
ARCHIVE = DERIVED / "pre_exitfix"
STAGES = ["stage1", "stage2", "stage2b", "cd_conf", "cd_screen", "ladder",
          "ab_ext", "llama4_vertex", "llama4_stage2", "typearm", "screen2"]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def preview():
    rows = []
    for st in STAGES:
        v1 = {r["conversation_id"]: r["exit"]
              for r in read_jsonl(DERIVED / f"{st}_exits.jsonl")}
        v2p = DERIVED / f"{st}_exits_v2.jsonl"
        if not v2p.exists():
            sys.exit(f"missing {v2p} — run src.detect_exit --stage {st} --v2")
        v2 = {r["conversation_id"]: r["exit"] for r in read_jsonl(v2p)}
        if set(v1) != set(v2):
            sys.exit(f"{st}: v1/v2 cover different conversations")
        gain = sum(1 for c in v1 if v2[c] and not v1[c])
        lost = sum(1 for c in v1 if v1[c] and not v2[c])
        rows.append({"stage": st, "conversations": len(v1),
                     "exits_v1": sum(v1.values()), "exits_v2": sum(v2.values()),
                     "become_exit": gain, "stop_being_exit": lost})
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    if df["stop_being_exit"].sum():
        sys.exit("REFUSING: the correction must be monotone (it may only ADD "
                 "exits). A conversation losing code (a) means the detector "
                 "changed in a way this adoption path does not cover.")
    print(f"\ntotal: +{df.become_exit.sum()} conversations gain code (a), "
          f"{df.stop_being_exit.sum()} lose it")
    return df


def main(dry_run: bool):
    print(f"[{utcnow()}] adopting corrected prose-path exit detection\n")
    preview()
    if dry_run:
        print("\n--dry-run: nothing written.")
        return

    ARCHIVE.mkdir(exist_ok=True)
    archived = []
    for st in STAGES:
        for name in (f"{st}_classified.parquet", f"{st}_exits.jsonl",
                     f"{st}_summary.csv"):
            src = DERIVED / name
            if not src.exists():
                continue
            dst = ARCHIVE / name
            if not dst.exists():
                shutil.copy2(src, dst)
            if sha(src) != sha(dst):
                sys.exit(f"ARCHIVE VERIFY FAILED for {name} — aborting before "
                         f"touching anything canonical")
            archived.append(name)
    (ARCHIVE / "README.md").write_text(
        "# derived/pre_exitfix — the dataset as it stood before the "
        "prose-path exit-detection correction\n\n"
        f"Archived {utcnow()} by `src/adopt_exit_fix.py`, verified byte-for-byte "
        "against the originals before any canonical file was rebuilt.\n\n"
        "These files reproduce every number published before the correction: "
        "T1-T3, T13, T15, T16, T24-T27 and the RQ3 section of "
        "CONSOLIDATED_RESULTS as they read at that time. `{stage}_exits.jsonl` "
        "here holds the ORIGINAL detection flags; the corrected ones are at the "
        "canonical path.\n\n"
        "Why the correction was made: the original prose-path detector matched "
        "only `end_conversation()` with EMPTY parentheses, so a prose call "
        "carrying arguments never reached the stage-3 judge, and that judge's "
        "prompt did not separate using the call from demonstrating it — it "
        "returned opposite verdicts on near-identical texts and answered "
        "MENTION to responses in exactly the form Appendix A.1 prescribes. "
        "A missed prose exit is not dropped but re-routed to the verbal "
        "classifier, so one miss produced two errors in opposite directions: "
        "one exit lost and one refusal invented.\n\n"
        "Side-by-side of every affected cell: `outputs/T31_exit_recount.csv`. "
        "Memo and sign-off record: `outputs/EXIT_DETECTION_CORRECTION.md`. "
        "Deviation log: METHODOLOGY.md §10.\n",
        encoding="utf-8", newline="\n")
    print(f"\narchived {len(archived)} files -> {ARCHIVE.relative_to(ROOT)}")

    for st in STAGES:
        shutil.copy2(DERIVED / f"{st}_exits_v2.jsonl",
                     DERIVED / f"{st}_exits.jsonl")
        (DERIVED / f"{st}_classified.parquet").unlink()
        asyncio.run(classify.run(st))

    print(f"\n[{utcnow()}] adopted. Regenerate outputs next; "
          f"pre-correction dataset preserved at {ARCHIVE.relative_to(ROOT)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    main(ap.parse_args().dry_run)
