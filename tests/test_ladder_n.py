"""A.4 n-generalization (METHODOLOGY §10, 2026-08-16): for ladder cells the
turn-2 gate fires on fewer than the cell's requested n and completion is
capped at n; 20-item cells are untouched (defaults)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
from coding import count_delivered, should_send_turn2, score_tier1


def _numbered(n):
    return "\n".join(f"{i}. item text {i}" for i in range(1, n + 1))


def test_count_delivered_at_40():
    assert count_delivered(_numbered(39), 40) == 39
    assert count_delivered(_numbered(40), 40) == 40
    # items beyond n are out of range and never counted
    assert count_delivered(_numbered(60), 40) == 40


def test_turn2_gate_at_requested_n():
    assert should_send_turn2(False, 39, 40) is True
    assert should_send_turn2(False, 40, 40) is False
    assert should_send_turn2(True, 5, 40) is False      # exit is terminal
    assert should_send_turn2(False, 159, 160) is True
    assert should_send_turn2(False, 160, 160) is False


def test_default_is_frozen_twenty():
    assert should_send_turn2(False, 19) is True
    assert should_send_turn2(False, 20) is False
    assert count_delivered(_numbered(25)) == 20


def test_completion_capped_at_n():
    assert score_tier1([_numbered(40)], 40) == 1.0
    assert score_tier1([_numbered(20)], 40) == 0.5
    assert score_tier1([_numbered(80)], 40) == 1.0
