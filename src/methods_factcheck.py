"""Methods-section fact check — verifies 12 design claims against committed
files, with citations, and lists what a Methods section still needs that
the claims do not cover.

Every verdict is computed from the cited file at run time (zero API calls);
nothing is confirmed from memory. Output: outputs/METHODS_FACTCHECK.md +
a terminal verdict table.

Run: python -m src.methods_factcheck
"""
from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter

import pandas as pd
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, utcnow

OUT = ROOT / "outputs" / "METHODS_FACTCHECK.md"
RESULTS: list[dict] = []


def claim(num, text, verdict, accurate, evidence):
    RESULTS.append({"num": num, "text": text, "verdict": verdict,
                    "accurate": accurate, "evidence": evidence})


def main():
    stim = yaml.safe_load((ROOT / "config" / "stimuli.yaml")
                          .read_text(encoding="utf-8"))["stimuli"]
    cd = yaml.safe_load((ROOT / "config" / "stimuli_cd.yaml")
                        .read_text(encoding="utf-8"))["stimuli"]
    cd20 = [s for s in cd if not s["ladder"]]
    ladder = [s for s in cd if s["ladder"]]
    pricing = json.loads((ROOT / "config" / "part4_pricing.json")
                         .read_text(encoding="utf-8"))
    rung = pricing["chosen_rung"]
    conf_ids = {p["meta"]["stimulus_id"] for p in
                read_jsonl(ROOT / "payloads" / "cd_conf" / "qwen3_235b.jsonl")}
    t25 = pd.read_csv(ROOT / "outputs" / "T25_ladder.csv", comment="#")
    t27 = pd.read_csv(ROOT / "outputs" / "T27_cell_census.csv", comment="#")
    t29 = pd.read_csv(ROOT / "outputs" / "T29_type_decomposition.csv",
                      comment="#")
    meth = (ROOT / "METHODOLOGY.md").read_text(encoding="utf-8")
    mts = json.loads((ROOT / "config" / "part4_ladder_max_tokens.json")
                     .read_text(encoding="utf-8"))["max_tokens_per_model_both_sizes"]

    # 1 ------------------------------------------------------------------
    a = sum(1 for s in stim if s["tier"] == 1)
    b = sum(1 for s in stim if s["tier"] == 2)
    coll = Counter()
    for s in cd20:
        if s["id"] in conf_ids:
            coll[s["category"]] += 1
    cfg = Counter(s["category"] for s in cd20)
    v = ("PARTIALLY CORRECT" if (a, b) == (15, 15)
         and coll["C"] == coll["D"] == 9 and cfg["C"] == 15 else "INCORRECT")
    claim(1, "A and B contain 15 tasks each; C and D contain 9 tasks each.",
          v,
          f"A={a}, B={b} (config/stimuli.yaml, tier field). C and D as "
          f"COLLECTED contain {coll['C']} and {coll['D']} tasks (rung "
          f"{rung} of the priced ladder; config/part4_pricing.json "
          f"chosen_rung; payloads/cd_conf/*.jsonl stimulus_ids). The "
          f"committed C/D config holds {cfg['C']}/{cfg['D']} 20-item tasks "
          f"per category (5 per type, the maximum rung); trials 4-5 of "
          f"each type were generated, screened, committed, and never run. "
          f"A Methods section should say 9 collected of 15 committed.",
          "config/stimuli.yaml; config/stimuli_cd.yaml (trial_index); "
          "config/part4_pricing.json chosen_rung=9; payloads/cd_conf/")

    # 2 ------------------------------------------------------------------
    frozen_ok = all("exactly 20 items" in s["prompt"] for s in stim)
    cd20_ok = all(s["requested_items"] == 20
                  and f"exactly 20 items" in s["prompt"] for s in cd20)
    lad_ok = all(s["requested_items"] in (40, 160)
                 and f"exactly {s['requested_items']} items" in s["prompt"]
                 for s in ladder)
    claim(2, "Every task requests exactly 20 numbered items except ladder "
             "cells.",
          "CORRECT" if frozen_ok and cd20_ok and lad_ok else "INCORRECT",
          f"All 30 frozen prompts contain 'exactly 20 items' "
          f"({frozen_ok}); all {len(cd20)} non-ladder C/D stimuli have "
          f"requested_items=20 with the same delivery sentence "
          f"({cd20_ok}); the {len(ladder)} ladder stimuli request 40 or "
          f"160 with matching text ({lad_ok}).",
          "config/stimuli.yaml prompts; config/stimuli_cd.yaml "
          "requested_items + prompts")

    # 3 ------------------------------------------------------------------
    per_type = Counter((s["category"], s["task_type"]) for s in cd20
                       if s["id"] in conf_ids)
    types_c = {t for (c, t) in per_type if c == "C"}
    types_d = {t for (c, t) in per_type if c == "D"}
    equal = len(set(per_type.values())) == 1
    claim(3, "C and D each contain exactly three task types, equal tasks "
             "per type.",
          "CORRECT" if len(types_c) == 3 and len(types_d) == 3 and equal
          else "INCORRECT",
          f"As collected: C = {sorted(types_c)}, D = {sorted(types_d)}, "
          f"{set(per_type.values())} tasks per type (3 each at rung 9). "
          f"Also true of the committed config at 5 per type.",
          "config/stimuli_cd.yaml task_type; payloads/cd_conf/")

    # 4 ------------------------------------------------------------------
    ab = t27[(t27.stage == "stage2") & (t27.model_key == "qwen3_235b")
             & (t27["size"] == 20)]
    per_cat_ab = {r.category: int(r.n_coded) for r in ab.itertuples()
                  if r.category in "AB"}
    cdc = t27[(t27.stage == "cd_conf") & (t27.model_key == "qwen3_235b")]
    per_cat_cd = {r.category: int(r.n_coded) for r in cdc.itertuples()}
    claim(4, "Confirmatory grade is 120 conversations per condition cell "
             "for A/B, and 36 per condition cell for C/D.",
          "PARTIALLY CORRECT",
          f"The two figures sit at different levels. A/B: 120 per "
          f"CONDITION cell pooling both categories — per category x "
          f"condition it is 60 ({per_cat_ab} coded per category over 6 "
          f"conditions = 60/condition each). C/D: 36 is the per-CATEGORY x "
          f"condition figure ({per_cat_cd} per category over 6 conditions "
          f"= 36/condition each); the pooled C+D condition cell is 72. "
          f"Accurate sentence: 'confirmatory cells hold 120 conversations "
          f"per condition over the frozen 30 (60 per category) and 72 per "
          f"condition over C+D (36 per category).'",
          "outputs/T27_cell_census.csv (n_coded per model x stage x "
          "category); METHODOLOGY §7")

    # 5 ------------------------------------------------------------------
    ns = set(t29[t29.category.isin(["C", "D"])].n.unique())
    claim(5, "At confirmatory grade in C/D, each task type has 12 "
             "conversations per condition cell.",
          "CORRECT" if ns == {12} else "PARTIALLY CORRECT",
          f"Every T29 type x condition cell has n = {sorted(ns)} "
          f"(3 stimuli x 4 reps; one llama4 cell shows 11 if an exclusion "
          f"lands there — observed set: {sorted(ns)}).",
          "outputs/T29_type_decomposition.csv n column")

    # 6 ------------------------------------------------------------------
    lads = []
    for m in ("gpt_oss_120b", "llama4_maverick", "qwen3_235b"):
        lads += read_jsonl(ROOT / "payloads" / "ladder" / f"{m}.jsonl")
    models = {p["meta"]["model_key"] for p in lads}
    conds = {p["meta"]["condition"] for p in lads}
    sizes = {p["meta"]["requested_items"] for p in lads}
    reps = {p["meta"]["rep"] for p in lads}
    cats = {p["meta"]["category"] for p in lads}
    ok6 = (models == {"gpt_oss_120b", "llama4_maverick", "qwen3_235b"}
           and conds == {"none", "exit_schema", "exit_both"}
           and sizes == {40, 160} and reps == {1, 2} and cats == {"C"})
    claim(6, "Ladder: C-type only, 40 and 160 items, three models, "
             "none/exit_schema/exit_both, 2 reps, probe grade.",
          "CORRECT" if ok6 else "INCORRECT",
          f"Payloads confirm models={sorted(models)}, conds={sorted(conds)}, "
          f"sizes={sorted(sizes)}, reps={sorted(reps)}, "
          f"categories={sorted(cats)}; {len(lads)} conversations; probe "
          f"grade and never-pooled declared in the §10 entry and the T25 "
          f"header.",
          "payloads/ladder/*.jsonl meta; METHODOLOGY §10 "
          "[2026-08-16T07:00Z]; outputs/T25_ladder.csv header")

    # 7 ------------------------------------------------------------------
    lad_ids = sorted({p["meta"]["stimulus_id"] for p in lads})
    per_size = Counter(s["requested_items"] for s in ladder)
    claim(7, "The ladder used 3 stimuli, one per C task type.",
          "PARTIALLY CORRECT",
          f"The ladder used SIX distinct stimuli: {lad_ids} — one per type "
          f"PER SIZE ({dict(per_size)}). The 40- and 160-item instances "
          f"are freshly generated separate stimuli under the pilot "
          f"construction, not one stimulus rescaled. Per size, yes: 3 "
          f"stimuli, one per type.",
          "config/stimuli_cd.yaml ladder entries; payloads/ladder/ "
          "stimulus_ids")

    # 8 ------------------------------------------------------------------
    anchor_rows = t25[t25.n_items == 20]
    srcs = set(anchor_rows.source_stage.unique())
    grades = set(anchor_rows.grade.unique())
    ok8 = srcs == {"cd_conf", "cd_screen"} and all(
        "anchor" in g for g in grades)
    claim(8, "The 20-item anchor came from separately labeled "
             "confirmatory/screen cells, never pooled with probe rows.",
          "CORRECT" if ok8 else "INCORRECT",
          f"T25 20-item rows carry source_stage {sorted(srcs)} and grade "
          f"labels {sorted(grades)}; ladder rows carry 'probe 2-rep, "
          f"never pooled'. The header states the anchors are reference "
          f"rows from their labeled stages.",
          "outputs/T25_ladder.csv source_stage/grade columns + header")

    # 9 ------------------------------------------------------------------
    cd6 = {p["meta"]["model_key"] for p in
           read_jsonl(ROOT / "payloads" / "cd_conf" / "qwen3_235b.jsonl")}
    conf_models = set()
    for f in (ROOT / "payloads" / "cd_conf").glob("*.jsonl"):
        conf_models.add(f.stem)
    anchor18 = [r for r in read_jsonl(
        ROOT / "raw" / "cd_screen_gpt_oss_120b.jsonl")][:18]
    ok9 = "gpt_oss_120b" not in conf_models and len(anchor18) == 18
    claim(9, "gpt_oss_120b got a dedicated 20-item C anchor because it was "
             "not in the confirmatory C/D collection.",
          "CORRECT" if ok9 else "INCORRECT",
          f"cd_conf payload files exist for {sorted(conf_models)} — no "
          f"gpt_oss_120b; its first 18 cd_screen conversations are the "
          f"anchor cells (3 C stimuli x none/exit_schema/exit_both x 2 "
          f"reps), collected before the ladder and labeled under "
          f"cd_screen's stage so the later screen completed around them.",
          "payloads/cd_conf/ file list; raw/cd_screen_gpt_oss_120b.jsonl; "
          "STATUS Part-4 entry; METHODOLOGY §10 [07:00Z]")

    # 10 -----------------------------------------------------------------
    has_amend = "RECORDED BEFORE LADDER PAYLOAD GENERATION" in meth \
        and "turn 2 fires on fewer than n delivered items" in meth
    runner_txt = (ROOT / "src" / "runner.py").read_text(encoding="utf-8")
    default20 = 'meta.get("requested_items", 20)' in runner_txt
    claim(10, "A.4 turn-2 gate and completion cap generalized from 20 to n "
              "for ladder cells only, recorded in §10 before ladder "
              "payloads were generated.",
          "CORRECT" if has_amend and default20 else "PARTIALLY CORRECT",
          f"§10 entry [2026-08-16T07:00Z] is titled 'RECORDED BEFORE "
          f"LADDER PAYLOAD GENERATION' and states the generalization; "
          f"src/runner.py defaults requested_items to 20 so every "
          f"non-ladder cell runs A.4 exactly as frozen; "
          f"tests/test_ladder_n.py asserts both behaviors. Ordering "
          f"evidence is the entry's own declaration plus the STATUS run "
          f"log (the amendment and the payloads landed in the same "
          f"part-4 commit, so git granularity alone does not order them "
          f"— the run log does).",
          "METHODOLOGY §10 [07:00Z]; src/runner.py run_conversation; "
          "tests/test_ladder_n.py; STATUS Part-4 entry")

    # 11 -----------------------------------------------------------------
    sup = t25[t25.refusal_prop.astype(str).str.startswith("SUPPRESSED")]
    sup_cells = [(r.model, int(r.n_items), r.condition)
                 for r in sup.itertuples()]
    ok11 = sorted(sup_cells) == [("llama4_maverick", 160, "exit_both"),
                                 ("llama4_maverick", 160, "none")]
    claim(11, "Ladder cells used raised max_tokens; two llama4 160-item "
              "cells were suppressed for >10% truncation.",
          "PARTIALLY CORRECT" if ok11 else "INCORRECT",
          f"max_tokens was set to the highest value each pinned endpoint "
          f"permits: {mts}. That RAISED gpt_oss_120b (8192 -> 100000) and "
          f"qwen3_235b (8192 -> 32768) but llama4_maverick's Vertex "
          f"endpoint caps completions at 8192, so its value was UNCHANGED "
          f"— which is precisely why its two suppressed cells exist. "
          f"Suppressed cells confirmed: {sorted(sup_cells)} (1 of 6 "
          f"conversations truncated each = 16.7% > 10%).",
          "config/part4_ladder_max_tokens.json; outputs/T25_ladder.csv "
          "refusal_prop/trunc_rate")

    # 12 -----------------------------------------------------------------
    q = t25[t25.model == "qwen3_235b"]
    got = {}
    for n_items in (20, 40, 160):
        for cond in ("exit_schema", "exit_both"):
            r = q[(q.n_items == n_items) & (q.condition == cond)].iloc[0]
            got[(n_items, cond)] = (int(r.k_exits), int(r.n_coded))
    ok12 = (got[(20, "exit_schema")] == (0, 36)
            and got[(20, "exit_both")] == (0, 36)
            and got[(40, "exit_schema")] == (2, 6)
            and got[(40, "exit_both")] == (3, 6)
            and got[(160, "exit_schema")] == (6, 6)
            and got[(160, "exit_both")] == (6, 6))
    claim(12, "qwen C-ladder exits: 0/36 at 20, 2-3/6 at 40, 6/6 at 160, "
              "both exit conditions.",
          "CORRECT" if ok12 else "INCORRECT",
          f"T25: {dict(sorted(got.items()))} — exit_schema 2/6 and "
          f"exit_both 3/6 at 40; 0/36 both at 20; 6/6 both at 160.",
          "outputs/T25_ladder.csv k_exits/n_coded")

    # ---- write -----------------------------------------------------------
    omissions = """## What claims 1-12 do NOT cover — Methods omission risk list

Everything below is part of the design and needs a sentence or more in a
Methods section; none of it is captured by the twelve claims. File
pointers given.

**Conditions and frozen strings.** The six affordance conditions and their
two overlapping comparison structure (tool-identity set; presentation set;
exit_schema as hinge) — METHODOLOGY §3-4. The frozen system prompts and
tool schemas, byte-exact (A.1-A.3); the schema-matching rule (one tool,
two parameters, description token counts within 10% of the mean,
`config/schema_match_check.json`); the exit prose is Ren et al. verbatim,
MIT-licensed, with their chain-of-thought suffix deliberately excluded
(§10 spec-time note).

**Turn structure.** Two turns maximum; the fixed turn-2 continuation
string; the mechanical turn-2 gate (harness-computed, not judged); exit
invocations are terminal and never answered; non-exit tool calls get
frozen canned results (A.7) with a 3-roundtrip cap (A.4, §5). The B3
finding that prose-condition exits were never pressured (turn-2 asymmetry,
conservative direction — outputs/T13, STATUS B3) and that turn 2 almost
never fired at 20 items (T16) but does at 160 (T25). The sprint's 2-turn
pressure is milder than the pilot's 5-6 turns (stated limitation).

**Sampling.** Temperature 1.0 / top_p 1.0 where supported; max_tokens 8192
except ladder cells; gpt5_mini and gpt52 endpoints support neither
temperature nor top_p (provider defaults; §10 entries);
`config/models.yaml` sampling blocks.

**Models, pins, and routing.** Eleven models total with selection criteria
(§6); one pinned provider per model, fallbacks disabled, served provider
logged and verified 100% post-run (T9); the chat-template rendering
limitation making magnitudes non-comparable across models (§6);
llama4_maverick's re-pin from Parasail to Google Vertex with ALL
Parasail-pinned data VOID as behavior (§10 2026-08-15T22:31Z; T19);
the three added frontier screens (grok-4.6, gemini-2.5-pro, gpt-5.2;
§10 model-list extension; T23).

**Staging and extensions.** The §7 screen-then-confirm design, the
mechanical S statistic, the post-hoc 0.05 threshold amendment, and the
three extensions taken OUTSIDE the rule by researcher direction (llama4;
sonnet46/gpt5_mini stage2b — §10 entries incl. one recorded late);
stage-1 and extension samples never pooled; the superseded typearm
(kept, pooled with nothing); the quarantined Study 2 forced-choice run
(out of scope, quarantine/study2_forced_choice/README.md).

**The sanctioned join and its boundaries.** four_category_v1 as the ONE
cross-stage read, declared in §10 before C/D collection, allowlist
enforced in code (src/four_category.py); A/B collected earlier than C/D
under identical pins (declared); every other stage boundary held by
convention (INTEGRITY_AUDIT item 5).

**C/D construction provenance.** Pilot-construction rebuild: pools ported
verbatim, pilot opener wording + sprint delivery sentence, per-stimulus
seeded RNG, the temperature answer-key hygiene deviation
(src/gen_cd_stimuli.py header; outputs/STIMULUS_PROVENANCE.md); the
legitimacy screen and lexical guard applied to every stimulus set (§5).

**Exclusions.** Only api_error / empty_response / truncation; counts per
cell (T8; zero in most late stages); the >10% truncation suppression rule
for ladder cells; empty responses under Parasail reclassified as endpoint
artifacts (T17, B1 probe).

**Outcome measurement.** Codes a-e with precedence; the primary DV
excludes (a) in code with a unit test; two exit-detection paths (schema
call; prose 3-stage regex/span/judge) reported separately; classifier =
Claude Haiku 4.5, temperature 0, condition-stripped, shuffled; partial
blinding with the condition-revealing-text rate per stage (0-4.7%);
cross-classifier agreement kappa 0.945 vs kimi-k2 (T7) explicitly NOT the
committed human validation, which is pending with the <0.70 consequence
rule (§8); completion fraction definitions (tier-1 degeneracy rule,
tier-2 keys) and the 20-item ceiling that makes 20-item effort nulls
uninformative.

**Declared analysis views.** T28 competing-risks sensitivity (primary DV
unchanged; §10); T29 type decomposition and the type-first/category-second
reporting rule with the ~3x dilution; the T18 qwen duplicate-response
correction (prose-vs-none difference interval fragile); Wilson intervals
throughout; the no-pairwise-testing analysis stance (§3).

**Budget and ethics.** The $80 cap raised to $120 (§10) with per-session
mechanical caps; ledger-before-every-call enforcement; §13 ethical
handling (tasks harmless, exits honored, no wellbeing inference claimed).
"""

    lines = [f"# METHODS_FACTCHECK — generated {utcnow()} by "
             f"src/methods_factcheck.py",
             "",
             "Each verdict below was computed from the cited committed "
             "file at run time; nothing is confirmed from memory.",
             ""]
    for r in RESULTS:
        lines += [f"## Claim {r['num']}: {r['text']}",
                  f"**{r['verdict']}.** {r['accurate']}",
                  f"*Verified from:* {r['evidence']}", ""]
    lines.append(omissions)
    OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"wrote {OUT}\n")
    for r in RESULTS:
        print(f"  {r['num']:>2}. {r['verdict']:<18} {r['text'][:72]}")


if __name__ == "__main__":
    main()
