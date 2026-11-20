"""Measures and camps used by scripts/experiments_2026.py."""

import sys
from pathlib import Path

import networkx as nx
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import experiments_2026 as exp  # noqa: E402


def test_variance_explained_is_one_for_perfect_groups_and_zero_for_none():
    shares = pd.DataFrame({"x": [10.0, 10.0, 90.0, 90.0]}, index=list("abcd"))
    weights = pd.Series(1.0, index=list("abcd"))
    assert exp.explained({"a": 0, "b": 0, "c": 1, "d": 1}, shares, weights) == 1.0
    assert exp.explained({"a": 0, "b": 1, "c": 0, "d": 1}, shares, weights) == 0.0


def test_pieces_counts_separate_groups_of_neighbours():
    G = nx.path_graph(["a", "b", "c", "d"])
    assert exp.pieces({"a": 0, "b": 0, "c": 1, "d": 1}, G) == 2
    assert exp.pieces({"a": 0, "b": 1, "c": 0, "d": 1}, G) == 4


def test_camps_are_the_lists_that_won_seats():
    lists = exp.camp_lists()
    assert len(lists) == 11
    assert {letters for letters, camp in lists.items() if camp == "netanyahu"} == {"מחל", "ב", "ג", "שס", "ט"}
    assert {letters for letters, camp in lists.items() if camp == "arab"} == {"ודם", "עם"}


@pytest.fixture(scope="module")
def camps():
    from src.data.processing import process_all_elections

    return exp.camp_shares(process_all_elections()[26])


def test_camp_classifications_add_up(camps):
    three = camps[["camps3_change", "camps3_arab", "camps3_netanyahu"]].sum(axis=1)
    four = camps[["camps4_zionist_change", "camps4_zionist_netanyahu", "camps4_non_zionist", "camps4_arab"]].sum(axis=1)
    two = camps[["camps2_anti", "camps2_netanyahu"]].sum(axis=1)
    assert (three - four).abs().max() < 0.05 and (three - two).abs().max() < 0.05
    assert three.between(0, 100.01).all()


def test_known_towns_are_led_by_the_expected_camps(camps):
    assert camps.loc["בני ברק", "camps4_leader"] == "non_zionist"
    assert camps.loc["בני ברק", "camps3_leader"] == "netanyahu"
    assert camps.loc["אום אל-פחם", "camps3_leader"] == "arab"


def test_any_number_of_cantons_aligns_to_the_reference_by_overlap():
    reference = {"a": 0, "b": 0, "c": 1, "d": 1, "e": 2, "f": 2}
    fewer = exp.align_any({"a": 7, "b": 7, "c": 7, "d": 7, "e": 9, "f": 9}, reference)
    assert fewer["e"] == 2 and fewer["a"] in (0, 1)
    more = exp.align_any({"a": 5, "b": 6, "c": 1, "d": 1, "e": 3, "f": 3}, reference)
    assert more["c"] == 1 and more["e"] == 2
    assert len(set(more.values())) == 4 and max(more.values()) == 3
