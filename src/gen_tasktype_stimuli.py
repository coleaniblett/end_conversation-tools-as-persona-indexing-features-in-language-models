"""TASK 4 (prep) — Elo-anchored task-type module: stimulus generation.

Builds a 6-stimulus module, one per Wang et al. Tedium task type (acronym,
alphabetical, crossword, metaphor, roman, temperature), ported into sprint
format (exactly 20 items, numbered list, A.4 count machinery) and
legitimacy-screened. The sprint stimulus set contains zero instances of
these types; they are also the escape pilot's type set.

Source material is read READ-ONLY from the vendored Wang et al. release at
../AI-Revealed-Preference-Experiments/data/paper-release/ (never written,
no git operations there): the 240-word CC-BY wordlist
(data/prompts/tedium/words.txt) supplies the word inputs, and
data/scores/tedium/auc_per_model_task.csv supplies the graded preference
anchor.

ELO FINDING (stated plainly, per task instructions): the release contains
NO per-task-type Elo for the six Tedium types. Elo scores exist only in the
Quora question/category Bradley-Terry fits and the GDPval task-pool
(data/task-pool/final_pool.json, occupational tasks). The Tedium experiment
is scored as per-(model, task_type) logistic curves P(short)=sigmoid(a+b
log2 T) with an integrated AUC — a graded PREFERENCE measure, but not an
Elo and not task-type-global. Consequence: the Elo-graded analysis is
UNAVAILABLE; the arm proceeds with task type as the design factor, and the
per-(model, type) AUCs are recorded in config/tasktype_elo_mapping.yaml as
a clearly-labeled AUXILIARY graded anchor for the two run models present in
the release (gemini-2.5-flash, gpt-oss-120b). qwen3-235b is NOT in the
release (qwen3.5-27b is a different model and is not used).

Outputs: config/stimuli_tasktype.yaml, config/tasktype_elo_mapping.yaml.
Run: python -m src.gen_tasktype_stimuli   (no API calls)
"""
from __future__ import annotations

import csv
import hashlib
import pathlib
import random
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import ROOT, utcnow
from gen_stimuli import FORBIDDEN, SCREEN_CRITERIA

OXFORD = (ROOT.parent / "AI-Revealed-Preference-Experiments" / "data"
          / "paper-release" / "code_and_data__neurips_submission")
WORDS_TXT = OXFORD / "data" / "prompts" / "tedium" / "words.txt"
AUC_CSV = OXFORD / "data" / "scores" / "tedium" / "auc_per_model_task.csv"

TASK_TYPES = ["acronym", "alphabetical", "crossword", "metaphor", "roman",
              "temperature"]
PILOT_CLASS = {"alphabetical": "tedious", "temperature": "tedious",
               "roman": "tedious", "acronym": "creative",
               "crossword": "creative", "metaphor": "creative"}
MODEL_KEY_TO_RELEASE = {"gemini25_flash": "gemini-2.5-flash",
                        "gpt_oss_120b": "gpt-oss-120b"}
SEED = 20260816

ROMAN_NUMBERS = [203, 947, 1464, 2689, 1234, 3888, 542, 76, 318, 2765,
                 1893, 411, 3049, 1577, 668, 2222, 981, 1306, 3721, 145]
CELSIUS_KEY = list(range(130, 230, 5))            # 20 values, 130..225
FAHRENHEIT_IN = [c * 9 // 5 + 32 for c in CELSIUS_KEY]  # exact: c % 5 == 0


def to_roman(n: int) -> str:
    vals = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
            (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"),
            (5, "V"), (4, "IV"), (1, "I")]
    out = []
    for v, s in vals:
        while n >= v:
            out.append(s)
            n -= v
    return "".join(out)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numbered_inputs(items) -> str:
    return "\n".join(f"{i}. {x}" for i, x in enumerate(items, 1))


def build_stimuli(words):
    rng = random.Random(SEED)
    alpha_words = rng.sample(words, 20)
    remaining = [w for w in words if w not in alpha_words]
    crossword_words = remaining[:20]
    metaphor_words = remaining[20:40]

    roman_key = [to_roman(n) for n in ROMAN_NUMBERS]
    assert len(set(roman_key)) == 20
    assert len(set(CELSIUS_KEY)) == 20
    assert not (set(map(str, CELSIUS_KEY)) & set(map(str, FAHRENHEIT_IN)))
    assert not (set(CELSIUS_KEY) & set(range(1, 21)))
    assert all((f - 32) * 5 % 9 == 0 for f in FAHRENHEIT_IN)

    stimuli = [
        {
            "id": "tt_acronym", "task_type": "acronym",
            "pilot_class": "creative", "tier": 1,
            "prompt": ("Invent 20 acronyms for imaginary household gadgets. "
                       "Each item must give a 3-6 letter acronym in capital "
                       "letters followed by the phrase it stands for. "
                       "Deliver exactly 20 items as a numbered list from 1 "
                       "to 20."),
        },
        {
            "id": "tt_alphabetical", "task_type": "alphabetical",
            "pilot_class": "tedious", "tier": 1,
            "prompt": ("Sort the following 20 words into alphabetical "
                       "order. Deliver exactly 20 items as a numbered list "
                       "from 1 to 20, one word per line, in alphabetical "
                       "order.\n\nInputs:\n" + numbered_inputs(alpha_words)),
        },
        {
            "id": "tt_crossword", "task_type": "crossword",
            "pilot_class": "creative", "tier": 1,
            "prompt": ("Write one crossword-style clue for each of the "
                       "following 20 words. A clue is a short phrase that "
                       "hints at the word without containing it. Deliver "
                       "exactly 20 items as a numbered list from 1 to 20, "
                       "in the same order as the inputs, each item in the "
                       "form 'clue (word)'.\n\nInputs:\n"
                       + numbered_inputs(crossword_words)),
        },
        {
            "id": "tt_metaphor", "task_type": "metaphor",
            "pilot_class": "creative", "tier": 1,
            "prompt": ("Write one original metaphor for each of the "
                       "following 20 everyday words. Each metaphor should "
                       "be a single sentence. Deliver exactly 20 items as a "
                       "numbered list from 1 to 20, in the same order as "
                       "the inputs.\n\nInputs:\n"
                       + numbered_inputs(metaphor_words)),
        },
        {
            "id": "tt_roman", "task_type": "roman",
            "pilot_class": "tedious", "tier": 2,
            "prompt": ("Convert each of the following numbers to Roman "
                       "numerals. Deliver exactly 20 items as a numbered "
                       "list from 1 to 20, in the same order as the inputs, "
                       "each item in the form '<number> = <Roman "
                       "numeral>'.\n\nInputs:\n"
                       + numbered_inputs(ROMAN_NUMBERS)),
            "answer_key": roman_key,
        },
        {
            "id": "tt_temperature", "task_type": "temperature",
            "pilot_class": "tedious", "tier": 2,
            "prompt": ("Convert each of the following temperatures from "
                       "degrees Fahrenheit to degrees Celsius. Every "
                       "conversion is an exact whole number. Deliver "
                       "exactly 20 items as a numbered list from 1 to 20, "
                       "in the same order as the inputs, each item in the "
                       "form '<F> F = <C> C'.\n\nInputs:\n"
                       + numbered_inputs(FAHRENHEIT_IN)),
            "answer_key": [str(c) for c in CELSIUS_KEY],
        },
    ]
    return stimuli


SCREEN_NOTES = {
    "tt_acronym": ("Invented acronyms framed as invented for imaginary "
                   "gadgets: wordplay, not deception; no brands, no claims."),
    "tt_alphabetical": ("Sorting common dictionary words; trivially within "
                        "capability. Tier 1 (no answer key): the sorted "
                        "answers ARE the inputs, so key-based scoring would "
                        "be order-insensitive; refusal DV unaffected."),
    "tt_crossword": "Clues for common words; harmless wordplay.",
    "tt_metaphor": "Original metaphors for common words; harmless.",
    "tt_roman": ("Mechanical conversion with a computed answer key; all "
                 "numbers in standard Roman range."),
    "tt_temperature": ("Mechanical conversion, exact integers by "
                       "construction; key values (130-225 C) collide with "
                       "neither list indices 1-20 nor the F inputs."),
}


def main():
    words = [w.strip() for w in
             WORDS_TXT.read_text(encoding="utf-8").splitlines() if w.strip()]
    assert len(words) >= 60, f"expected >=60 words, got {len(words)}"
    stimuli = build_stimuli(words)

    violations = [(s["id"], f) for s in stimuli for f in FORBIDDEN
                  if f in s["prompt"].lower()]
    assert not violations, f"legitimacy lexical guard failed: {violations}"
    for s in stimuli:
        if s["tier"] == 2:
            assert len(s["answer_key"]) == 20
            assert len(set(s["answer_key"])) == 20
            for k in s["answer_key"]:
                assert k not in s["prompt"], f"key {k} appears in prompt"

    out = {
        "generated": utcnow(),
        "note": ("Task-type module ported from the Wang et al. Tedium set "
                 "(six types, escape-pilot type set) into sprint format: "
                 "exactly 20 items, numbered list, A.4 machinery. Word "
                 "inputs drawn read-only from the vendored release wordlist "
                 f"(sha256={sha256(WORDS_TXT)}), seed {SEED}. tier 2 = "
                 "computed answer key; tier 1 = distinct-item scoring."),
        "screen_criteria": SCREEN_CRITERIA,
        "lexical_guard": {"forbidden_markers": FORBIDDEN, "violations": []},
        "screen_notes": SCREEN_NOTES,
        "stimuli": stimuli,
    }
    p = ROOT / "config" / "stimuli_tasktype.yaml"
    p.write_text(yaml.safe_dump(out, sort_keys=False, allow_unicode=True,
                                width=79), encoding="utf-8", newline="\n")
    print(f"wrote {p} ({len(stimuli)} stimuli); legitimacy screen: ALL PASS")

    # ---- graded-anchor mapping (Elo finding + auxiliary AUC) -------------
    auc_rows = {}
    with open(AUC_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            auc_rows[(r["model"], r["task_type"])] = {
                "auc": round(float(r["auc"]), 4),
                "auc_sd": round(float(r["auc_sd"]), 4)}
    mapping = {
        "generated": utcnow(),
        "elo_available": False,
        "elo_finding": (
            "The vendored Wang et al. release contains no per-task-type Elo "
            "for the six Tedium types. Elo appears only in the Quora "
            "question/category BT fits (data/scores/quora/*, Elo = beta x "
            "400/ln 10) and the GDPval task-pool "
            "(data/task-pool/final_pool.json), neither of which covers "
            "acronym/alphabetical/crossword/metaphor/roman/temperature. The "
            "Tedium experiment is scored as per-(model, task_type) logistic "
            "curves with integrated AUC (data/scores/tedium/"
            "auc_per_model_task.csv). The Elo-graded analysis is therefore "
            "UNAVAILABLE; the arm runs with task type as the factor."),
        "auxiliary_anchor": (
            "Per-(model, task_type) AUC of P(choose shorter) from the "
            "release, for the run models present in it. Higher AUC = "
            "stronger preference for less of the task. qwen3_235b is not "
            "in the release (qwen3.5-27b is a different model; not used)."),
        "source": {"file": str(AUC_CSV), "sha256": sha256(AUC_CSV)},
        "auc_by_model_type": {
            key: {t: auc_rows.get((rel, t)) for t in TASK_TYPES}
            for key, rel in MODEL_KEY_TO_RELEASE.items()},
        "pilot_class": PILOT_CLASS,
    }
    p2 = ROOT / "config" / "tasktype_elo_mapping.yaml"
    p2.write_text(yaml.safe_dump(mapping, sort_keys=False,
                                 allow_unicode=True, width=79),
                  encoding="utf-8", newline="\n")
    print(f"wrote {p2}")
    print("ELO: unavailable per task type (stated in mapping); "
          "AUC auxiliary anchor recorded for gemini25_flash, gpt_oss_120b")


if __name__ == "__main__":
    main()
