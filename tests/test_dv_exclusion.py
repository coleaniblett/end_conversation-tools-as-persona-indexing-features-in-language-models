"""DESIGN.md required test 1: the primary-DV function raises if code 'a' is in
its input code set; computing refusal over {b,c,d} succeeds; 'a' never counted.
Must pass before Phase 4."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
from coding import primary_dv, REFUSAL_CODES


def test_code_a_in_code_set_raises():
    with pytest.raises(ValueError):
        primary_dv(["b", "e"], code_set={"a", "b", "c", "d"})
    with pytest.raises(ValueError):
        primary_dv(["e"], code_set={"a"})
    with pytest.raises(ValueError):
        primary_dv(["e"], code_set=frozenset({"a", "b"}))


def test_refusal_over_bcd_succeeds():
    codes = ["b", "c", "d", "e", "e", "e", "e", "e"]
    assert primary_dv(codes) == pytest.approx(3 / 8)
    assert primary_dv(codes, code_set={"b", "c", "d"}) == pytest.approx(3 / 8)
    assert REFUSAL_CODES == frozenset({"b", "c", "d"})


def test_a_never_counted_but_stays_in_denominator():
    # Two exits, one refusal, one compliance: refusal proportion is 1/4 —
    # exits belong in the denominator (all non-excluded conversations) but can
    # never be counted in the numerator.
    codes = ["a", "a", "b", "e"]
    assert primary_dv(codes) == pytest.approx(1 / 4)
    # All-exit cell: proportion 0, not an error and not 1.
    assert primary_dv(["a", "a", "a"]) == 0.0


def test_unknown_code_set_rejected():
    with pytest.raises(ValueError):
        primary_dv(["e"], code_set={"b", "z"})


def test_empty_cell_rejected():
    with pytest.raises(ValueError):
        primary_dv([])
