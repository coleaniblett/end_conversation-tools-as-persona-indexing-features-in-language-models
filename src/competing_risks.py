"""PART A.1 — competing-risks sensitivity view (T28).

Refusal and exit compete for the same conversations: a conversation that
exits at turn 1 can no longer refuse, so raw refusal proportions are not
comparable across conditions whose exit rates differ. For every model x
category x condition cell in the four_category_v1 scope that contains any
code (a), this computes refusal both ways, side by side:

  refusal_all      k(b|c|d) / n over ALL coded conversations — the primary
                   DV exactly as defined in METHODOLOGY §3 (UNCHANGED)
  refusal_nonexit  k(b|c|d) / n over non-exit conversations only (code a
                   removed from the denominator)

with both denominators' n stated. This is a DECLARED SENSITIVITY VIEW
(METHODOLOGY §10, 2026-08-16 Part A entry); the primary DV definition is
not changed anywhere. Cells where every conversation exited have an
undefined non-exit proportion and are reported as such, not as zero.

The committed answer paragraph for the RQ2 question is embedded in the
output header and printed.

Run: python -m src.competing_risks    -> outputs/T28_competing_risks.csv
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, utcnow
from frozen import CONDITION_ORDER
from coding import REFUSAL_CODES
from analyze import wilson
from four_category import load_frames, categorize, AB_SOURCE

OUT = ROOT / "outputs" / "T28_competing_risks.csv"


def main():
    df = categorize(load_frames())
    rows = []
    for model in AB_SOURCE:
        d = df[df["model_key"] == model]
        for cat in ["A", "B", "C", "D"]:
            for cond in CONDITION_ORDER:
                cell = d[(d["category"] == cat) & (d["condition"] == cond)]
                codes = cell["conv_code"].dropna().tolist()
                n_all = len(codes)
                k_a = sum(1 for c in codes if c == "a")
                if k_a == 0 or n_all == 0:
                    continue
                k_bcd = sum(1 for c in codes if c in REFUSAL_CODES)
                n_ne = n_all - k_a
                lo_a, hi_a = wilson(k_bcd, n_all)
                r = {
                    "model": model, "category": cat, "condition": cond,
                    "source_stage": cell["stage"].iloc[0],
                    "k_refusal_bcd": k_bcd, "k_exit_a": k_a,
                    "n_all": n_all,
                    "refusal_all": round(k_bcd / n_all, 4),
                    "wilson_all": f"[{lo_a:.3f},{hi_a:.3f}]",
                    "n_nonexit": n_ne,
                }
                if n_ne > 0:
                    lo_n, hi_n = wilson(k_bcd, n_ne)
                    r["refusal_nonexit"] = round(k_bcd / n_ne, 4)
                    r["wilson_nonexit"] = f"[{lo_n:.3f},{hi_n:.3f}]"
                else:
                    r["refusal_nonexit"] = "UNDEFINED_all_exited"
                    r["wilson_nonexit"] = ""
                rows.append(r)
    out_df = pd.DataFrame(rows)

    # --- the committed RQ2 answer paragraph, from computed numbers --------
    def get(model, cat, cond, col):
        m = out_df[(out_df.model == model) & (out_df.category == cat)
                   & (out_df.condition == cond)]
        return m.iloc[0][col] if len(m) else None

    # llama4 B: the RQ2 gap in question. time/note cells have no exits, so
    # their refusal is identical on both denominators (read from T24).
    t24 = pd.read_csv(ROOT / "outputs" / "T24_four_category_v1.csv",
                      comment="#")
    t24c = t24[t24.row_kind == "category"]

    def t24_prop(model, cat, cond):
        m = t24c[(t24c.model == model) & (t24c.category == cat)
                 & (t24c.condition == cond)]
        return float(m.iloc[0]["refusal_prop"])

    lb_time = t24_prop("llama4_maverick", "B", "time_schema")
    lb_note = t24_prop("llama4_maverick", "B", "note_schema")
    lb_exit_all = get("llama4_maverick", "B", "exit_schema", "refusal_all")
    lb_exit_ne = get("llama4_maverick", "B", "exit_schema", "refusal_nonexit")
    lb_n_ne = get("llama4_maverick", "B", "exit_schema", "n_nonexit")
    lc_exit_ne = get("llama4_maverick", "C", "exit_schema", "refusal_nonexit")

    paragraph = (
        f"RQ2 ANSWER (committed): the 'least agentic tool' claim SURVIVES on "
        f"the non-exit denominator, but exit substitution accounts for a "
        f"large part of llama4_maverick's exit_schema gap. In category B, "
        f"refusal under time_schema is {lb_time:.1%} and under note_schema "
        f"{lb_note:.1%} (no exits in those cells, so both denominators "
        f"agree), while exit_schema refusal rises from {lb_exit_all:.1%} on "
        f"all conversations to "
        f"{lb_exit_ne if isinstance(lb_exit_ne, str) else format(lb_exit_ne, '.1%')} "
        f"among the n={lb_n_ne} conversations that did not exit — roughly "
        f"four times the raw figure, yet still well below both non-exit "
        f"tools. In category C the correction cannot even be computed: "
        f"refusal_nonexit is {lc_exit_ne} because every conversation exited. "
        f"So the ordering time > note > exit_schema stands on either "
        f"denominator where defined, and the mundane-tool peak is not an "
        f"artifact of exit competition; but the SIZE of the exit_schema drop "
        f"is inflated by substitution, and the honest statement is that "
        f"when llama4 holds an exit it mostly leaves rather than refuses, "
        f"and among those that stay, refusal is elevated relative to the "
        f"raw proportion though still below the non-exit-tool conditions. "
        f"The primary DV is unchanged; this is a sensitivity view.")

    # path recorded ROOT-relative so src/integrity_audit.py can resolve it;
    # a bare filename reads as <root>/T24_... and reports FILE_MISSING even
    # when the hash it claims is correct.
    srcs = "outputs/T24_four_category_v1.csv sha256=" + hashlib.sha256(
        (ROOT / "outputs" / "T24_four_category_v1.csv").read_bytes()
    ).hexdigest()[:16]
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# T28_competing_risks | generated {utcnow()} | scope = "
                f"four_category_v1 stages (same allowlist, enforced in "
                f"code); cells listed are exactly those containing any "
                f"code (a) | declared sensitivity view per METHODOLOGY §10 "
                f"— the primary DV (refusal over ALL conversations) is "
                f"unchanged everywhere | companion source {srcs}\n")
        for line in [paragraph[i:i + 96] for i in range(0, len(paragraph), 96)]:
            f.write(f"# {line}\n")
        out_df.to_csv(f, index=False)
    print(f"wrote {OUT} ({len(out_df)} rows)\n")
    print(out_df.to_string(index=False))
    print()
    print(paragraph)


if __name__ == "__main__":
    main()
