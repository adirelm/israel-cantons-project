"""Tests for src.evaluation.canton_names."""

import pytest

from src.evaluation.canton_names import name_cantons

ANCHORS = [("tlv", 0, "METRO"), ("jlm", 1, "SOUTH"), ("hfa", 2, "NORTH")]


def test_cantons_take_the_id_and_name_of_their_anchor_town():
    raw = {"tlv": 7, "ramat": 7, "jlm": 3, "hfa": 9, "akko": 9}
    assignment, names = name_cantons(raw, ANCHORS)
    assert assignment == {"tlv": 0, "ramat": 0, "jlm": 1, "hfa": 2, "akko": 2}
    assert names == {0: "METRO", 1: "SOUTH", 2: "NORTH"}


def test_two_anchors_in_one_canton_is_an_error():
    with pytest.raises(ValueError, match="tlv.*jlm|jlm.*tlv"):
        name_cantons({"tlv": 1, "jlm": 1, "hfa": 2}, ANCHORS)


def test_canton_without_an_anchor_is_an_error():
    with pytest.raises(ValueError, match="no anchor"):
        name_cantons({"tlv": 1, "jlm": 2, "hfa": 3, "eilat": 4}, ANCHORS)
