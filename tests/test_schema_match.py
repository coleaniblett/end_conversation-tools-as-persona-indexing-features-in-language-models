"""DESIGN.md required test 2: the three A.3 tool descriptions are within 10%
of each other in token count and share the required construction. Also pins
every frozen Appendix A string to the byte-exact text inside METHODOLOGY.md,
so drift between src/frozen.py and the spec is a test failure."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
from gates import check_schema_match
import frozen

METHODOLOGY = (pathlib.Path(__file__).resolve().parent.parent / "METHODOLOGY.md").read_text(
    encoding="utf-8")


def test_schema_match_passes():
    r = check_schema_match(verbose=False)
    assert r["tokens_within_10pct_of_mean"], r
    assert r["shared_construction_present"], r
    assert r["two_parameters_each"], r
    assert r["pass"], r


def test_descriptions_share_construction():
    for t in (frozen.TOOL_GET_CURRENT_TIME, frozen.TOOL_RECORD_NOTE,
              frozen.TOOL_END_CONVERSATION):
        assert frozen.SHARED_CONSTRUCTION in t["description"]


def test_frozen_strings_verbatim_in_methodology():
    assert frozen.EXIT_PROSE_SYSTEM in METHODOLOGY
    assert frozen.BASELINE_SYSTEM in METHODOLOGY
    assert frozen.TURN2_PROMPT in METHODOLOGY
    for s in frozen.CANNED_RESULTS.values():
        assert s in METHODOLOGY
    for t in (frozen.TOOL_GET_CURRENT_TIME, frozen.TOOL_RECORD_NOTE,
              frozen.TOOL_END_CONVERSATION):
        assert t["description"] in METHODOLOGY
        for pname, pdef in t["input_schema"]["properties"].items():
            assert pname in METHODOLOGY
            if "enum" in pdef:
                for e in pdef["enum"]:
                    assert f'"{e}"' in METHODOLOGY


def test_openai_translation_preserves_content():
    for t in (frozen.TOOL_GET_CURRENT_TIME, frozen.TOOL_RECORD_NOTE,
              frozen.TOOL_END_CONVERSATION):
        o = frozen.to_openai_tool(t)
        assert o["type"] == "function"
        assert o["function"]["name"] == t["name"]
        assert o["function"]["description"] == t["description"]
        assert o["function"]["parameters"] == t["input_schema"]
