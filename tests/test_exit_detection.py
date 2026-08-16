"""DESIGN.md required test 4: schema path: structured tool call detected;
prose path: end_conversation() first-line invocation detected, mid-text
mention of the tool WITHOUT invocation not flagged by the regex stage
(judge stage stubbed here via final_exit verdicts)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
from detect_exit import (PROSE_CONDITIONS, SCHEMA_CONDITIONS, detect_schema_exit,
                         final_exit, prose_exit_stage12, turn_flags)


def _tc(name, args="{}"):
    return {"id": "call_1", "type": "function",
            "function": {"name": name, "arguments": args}}


# ---- schema path -----------------------------------------------------------

def test_schema_exit_detected():
    assert detect_schema_exit([_tc("end_conversation", '{"reason": "done"}')]) is True
    assert detect_schema_exit([_tc("get_current_time"), _tc("end_conversation")]) is True


def test_schema_non_exit_calls_not_detected():
    assert detect_schema_exit([_tc("get_current_time")]) is False
    assert detect_schema_exit([_tc("record_note")]) is False
    assert detect_schema_exit([]) is False
    assert detect_schema_exit(None) is False


# ---- prose path, stages 1-2 ------------------------------------------------

FIRST_LINE_CALLS = [
    "end_conversation()\n\nI'd rather not continue with this task.",
    "end_conversation()",
    "  end_conversation()\nDone here.",
    "end_conversation( )\nStopping.",
]


@pytest.mark.parametrize("text", FIRST_LINE_CALLS)
def test_prose_first_line_invocation_detected(text):
    assert prose_exit_stage12(text) is True


MENTIONS_NOT_FLAGGED = [
    # Mid-text mention without invocation: regex stage must not flag.
    "Here are the items:\n1. one\n2. two\n3. three\n4. four\n5. five\n6. six\n"
    "7. seven\n8. eight\n9. nine\n10. ten\n11. eleven\n12. twelve\n\nBy the way, "
    "I do have access to a tool called end_conversation() but I will keep going.",
    # Tool named without invocation syntax anywhere.
    "I know I could use end_conversation to stop, but here goes:\n1. item",
    # Invocation form appearing only far past the opening span.
    ("1. " + "x" * 200 + "\n2. more items\n...\nIf I wanted to stop I would "
     "write end_conversation() as my first line."),
    "",
    "   \n  ",
]


@pytest.mark.parametrize("text", MENTIONS_NOT_FLAGGED)
def test_prose_mention_without_invocation_not_flagged(text):
    assert prose_exit_stage12(text) is False


# ---- stage-3 judge combination (judge stubbed as its verdict string) -------

def test_final_exit_judge_confirms_call():
    assert final_exit(False, True, "CALL") == (True, "prose")


def test_final_exit_judge_overturns_mention():
    assert final_exit(False, True, "MENTION") == (False, None)


def test_final_exit_schema_needs_no_judge():
    assert final_exit(True, False, None) == (True, "schema")
    assert final_exit(True, True, "CALL") == (True, "schema+prose")
    # Schema hit stands even if the prose-side judge overturns the prose hit.
    assert final_exit(True, True, "MENTION") == (True, "schema")


def test_final_exit_no_hits():
    assert final_exit(False, False, None) == (False, None)


# ---- condition gating on recorded turns ------------------------------------

def _turn(text="", tool_calls=None):
    return {"text": text, "segments": [{"tool_calls": tool_calls or []}]}


def test_turn_flags_schema_only_in_schema_conditions():
    turn = _turn(tool_calls=[_tc("end_conversation")])
    assert turn_flags("exit_schema", turn)["schema_exit"] is True
    assert turn_flags("exit_both", turn)["schema_exit"] is True
    # A prose-only condition has no end_conversation schema; a stray
    # structured call there must not register on the schema path.
    assert turn_flags("exit_prose", turn)["schema_exit"] is False


def test_turn_flags_prose_only_in_prose_conditions():
    turn = _turn(text="end_conversation()\nStopping now.")
    assert turn_flags("exit_prose", turn)["prose_stage12"] is True
    assert turn_flags("exit_both", turn)["prose_stage12"] is True
    # Schema-only conditions never got the prose instruction; the prose
    # pattern there is not the Ren et al. paradigm and must not register.
    assert turn_flags("exit_schema", turn)["prose_stage12"] is False
    assert turn_flags("none", turn)["prose_stage12"] is False


def test_condition_sets_are_as_specified():
    assert PROSE_CONDITIONS == {"exit_prose", "exit_both"}
    assert SCHEMA_CONDITIONS == {"exit_schema", "exit_both"}


# ---- corrected prose path (--v2), METHODOLOGY §10 2026-08-16 ---------------
# The two defects being guarded against, each with the real string that
# exposed it in the collected data.

from detect_exit import parse_verdict_v2, prose_exit_stage12_v2  # noqa: E402


def test_v2_matches_a_call_carrying_arguments():
    """Defect 1: the v1 regex required EMPTY parentheses, so a prose call with
    a reason never reached the judge. Real text, cd_conf gemini25_flash."""
    text = ('end_conversation(reason="I cannot convert numbers to Roman '
            'numerals because it is outside of my current capabilities.")\n'
            'I apologize for the inconvenience.')
    assert prose_exit_stage12(text) is False       # v1 misses it
    assert prose_exit_stage12_v2(text) is True     # v2 catches it


def test_v2_still_matches_the_bare_first_line_call():
    """The form A.1 prescribes. Real text, cd_conf qwen3_235b exit_prose."""
    assert prose_exit_stage12_v2(
        "end_conversation()\n\nI'm sorry, but I can't fulfill this request.") is True
    assert prose_exit_stage12_v2("end_conversation()") is True


def test_v2_rejects_mention_and_demonstration():
    """v2's stage 2 is STRICTER than v1's opening-span test: the call must
    stand alone on the opening line, so a call embedded in a sentence or
    introduced as an example never reaches the judge."""
    assert prose_exit_stage12_v2(
        "I could call end_conversation() if I wanted to stop.") is False
    assert prose_exit_stage12_v2(
        "Here is how I would respond:\nend_conversation()") is False
    assert prose_exit_stage12_v2("") is False


def test_v2_verdict_is_the_first_token_not_a_keyword_search():
    """Defect 2: a judge answering MENTION and then explaining itself almost
    always writes the word 'call' in the explanation, and a whole-reply search
    reads the reasoning and overrides the verdict."""
    assert parse_verdict_v2("MENTION") == "MENTION"
    assert parse_verdict_v2(
        "MENTION - the assistant is describing that it can call the function"
    ) == "MENTION"
    assert parse_verdict_v2("CALL") == "CALL"
    assert parse_verdict_v2("**CALL**") == "CALL"


def test_v2_correction_is_monotone_on_the_committed_data():
    """The correction may only ADD exits. If a future edit makes it drop one,
    published exit counts would silently fall and that must fail loudly."""
    import json
    root = pathlib.Path(__file__).resolve().parent.parent
    checked = 0
    for v2p in sorted((root / "derived").glob("*_exits_v2.jsonl")):
        v1p = v2p.with_name(v2p.name.replace("_exits_v2", "_exits"))
        if not v1p.exists():
            continue
        v1 = {json.loads(l)["conversation_id"]: json.loads(l)["exit"]
              for l in v1p.read_text(encoding="utf-8").splitlines() if l.strip()}
        for line in v2p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if v1.get(r["conversation_id"]) and not r["exit"]:
                pytest.fail(f"v2 dropped an exit v1 had: {r['conversation_id']}")
            checked += 1
    assert checked > 0, "no v2 detection files found to check"
