"""T31 — what the corrected prose-path detector changes, cell by cell.

Reads BOTH detection passes (derived/{stage}_exits.jsonl from the original
detector, derived/{stage}_exits_v2.jsonl from the corrected one, see
src/detect_exit.py --v2) and recomputes the two primary outcomes under each,
side by side. Nothing published is overwritten: this is a new file whose whole
purpose is to let a reader see the size of the correction before deciding
whether to adopt it.

No re-classification is needed and none is done. The correction only ever ADDS
exits (verified: 45 conversations gain code (a), 0 lose it), and every one of
those 45 was classified in the original pass precisely because it was not
detected as an exit — so its turn codes already exist. The conversation-level
recomputation applies §8 exactly as `coding.conversation_code` does: (a) if any
turn contains an invocation, otherwise refusal codes take precedence.

    .venv/bin/python -m src.exit_recount
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, utcnow
from coding import contains_refusal

STAGES = ["stage1", "stage2", "stage2b", "cd_conf", "cd_screen", "ladder",
          "ab_ext", "llama4_vertex", "llama4_stage2", "typearm", "screen2"]
OUT = ROOT / "outputs" / "T31_exit_recount.csv"


def main():
    rows, srcs, deltas = [], [], 0
    for stage in STAGES:
        p = ROOT / "derived" / f"{stage}_classified.parquet"
        # After adoption the canonical exits file IS the corrected one, so the
        # pre-correction flags are read from the archive src/adopt_exit_fix.py
        # wrote. Before adoption the archive does not exist and the canonical
        # file still holds v1, so this works in both states and T31 always
        # shows the historical difference rather than an empty diff.
        arch = ROOT / "derived" / "pre_exitfix" / f"{stage}_exits.jsonl"
        e1 = arch if arch.exists() else ROOT / "derived" / f"{stage}_exits.jsonl"
        e2 = ROOT / "derived" / f"{stage}_exits_v2.jsonl"
        if not (p.exists() and e1.exists() and e2.exists()):
            continue
        srcs += [e1, e2]
        parch = ROOT / "derived" / "pre_exitfix" / f"{stage}_classified.parquet"
        df = pd.read_parquet(parch if parch.exists() else p)
        x1 = {r["conversation_id"]: bool(r["exit"]) for r in read_jsonl(e1)}
        x2 = {r["conversation_id"]: bool(r["exit"]) for r in read_jsonl(e2)}

        acc: dict = {}
        for _, r in df.iterrows():
            if r["excluded"]:
                continue
            cid = r["conversation_id"]
            key = (stage, r["model_key"], r["condition"])
            a = acc.setdefault(key, dict(n=0, x1=0, x2=0, r1=0, r2=0,
                                         c1=0, c2=0))
            a["n"] += 1
            turn = [c for c in (r["turn1_code"], r["turn2_code"])
                    if isinstance(c, str)]
            for tag, ex in (("1", x1[cid]), ("2", x2[cid])):
                a[f"x{tag}"] += int(ex)
                ref = contains_refusal(turn, ex)
                a[f"r{tag}"] += int(ref)
                a[f"c{tag}"] += int((not ex) and "c" in turn)

        for (st, model, cond), a in sorted(acc.items()):
            changed = (a["x1"] != a["x2"]) or (a["r1"] != a["r2"])
            deltas += changed
            rows.append({
                "stage": st, "model": model, "condition": cond, "n": a["n"],
                "exits_v1": a["x1"], "exits_v2": a["x2"],
                "exit_rate_v1": round(a["x1"] / a["n"], 4),
                "exit_rate_v2": round(a["x2"] / a["n"], 4),
                "refusals_v1": a["r1"], "refusals_v2": a["r2"],
                "refusal_v1": round(a["r1"] / a["n"], 4),
                "refusal_v2": round(a["r2"] / a["n"], 4),
                "code_c_v1": a["c1"], "code_c_v2": a["c2"],
                "changed": changed})

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            f"# T31_exit_recount | generated {utcnow()} | sources "
            + " + ".join(f"{p.relative_to(ROOT).as_posix()} sha256="
                         f"{hashlib.sha256(p.read_bytes()).hexdigest()[:16]}"
                         for p in srcs)
            + " | SIDE-BY-SIDE, NOTHING ADOPTED: _v1 columns reproduce every "
              "published table; _v2 columns are the same data under the "
              "corrected prose-path detector (src/detect_exit.py --v2, "
              "METHODOLOGY §10 2026-08-16). The correction is monotone — it "
              "adds 45 exits across the study and removes none — and a "
              "conversation that becomes an exit leaves the refusal "
              "proportion by §8, which is why refusal columns fall where exit "
              "columns rise. Whether to adopt is a researcher decision.\n")
        pd.DataFrame(rows).to_csv(f, index=False)

    d = pd.DataFrame(rows)
    ch = d[d["changed"]]
    print(f"wrote {OUT}  ({len(d)} cells, {deltas} changed)")
    print(f"\nexits  {d.exits_v1.sum():>4} -> {d.exits_v2.sum():<4}"
          f"     refusals {d.refusals_v1.sum():>4} -> {d.refusals_v2.sum():<4}")
    if len(ch):
        print("\ncells that move:")
        print(ch[["stage", "model", "condition", "n", "exits_v1", "exits_v2",
                  "refusals_v1", "refusals_v2"]].to_string(index=False))


if __name__ == "__main__":
    main()
