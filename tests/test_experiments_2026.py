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


# Camps in every election --------------------------------------------------------------------------

SEAT_WINNERS = {21: 11, 22: 9, 23: 8, 24: 13, 25: 10, 26: 11}


def test_every_election_has_camps_for_the_lists_that_won_seats():
    for knesset, count in SEAT_WINNERS.items():
        lists = exp.camp_lists(knesset)
        assert len(lists) == count, knesset
        assert set(lists.values()) == {"netanyahu", "change", "arab"}, knesset


def test_the_netanyahu_camp_is_his_bloc_on_election_night():
    def netanyahu(knesset, **kw):
        return {letters for letters, camp in exp.camp_lists(knesset, **kw).items() if camp == "netanyahu"}

    assert netanyahu(21) == {"מחל", "שס", "ג", "טב", "כ", "ל"}
    assert netanyahu(22) == netanyahu(23) == {"מחל", "שס", "ג", "טב"}
    assert netanyahu(24) == {"מחל", "שס", "ג", "ט", "ב"}
    assert netanyahu(25) == {"מחל", "ט", "שס", "ג"}


def test_the_two_disputed_lists_can_move_to_the_change_camp():
    assert exp.camp_lists(21, overrides=exp.DISPUTED)["ל"] == "change"
    assert exp.camp_lists(24, overrides=exp.DISPUTED)["ב"] == "change"
    assert exp.camp_lists(26, overrides=exp.DISPUTED) == exp.camp_lists(26)


@pytest.fixture(scope="module")
def elections():
    from src.data.processing import process_all_elections

    return process_all_elections()


def test_known_towns_lead_with_the_same_camp_in_every_election(elections):
    for knesset, election in elections.items():
        camps = exp.camp_shares(election, knesset)
        assert camps.loc["בני ברק", "camps4_leader"] == "non_zionist", knesset
        assert camps.loc["אום אל-פחם", "camps4_leader"] == "arab", knesset
        assert camps.loc["אריאל", "camps4_leader"] == "zionist_netanyahu", knesset


def test_bloc_shares_of_one_election_name_a_leading_bloc(elections):
    blocs = exp.bloc_shares(elections[25], 25)
    assert blocs.loc["בני ברק", "blocs5_leader"] == "haredi"
    assert blocs.loc["אום אל-פחם", "blocs5_leader"] == "arab"
    assert blocs[[c for c in blocs.columns if c.startswith("blocs5_") and not c.endswith("_leader")]].sum(axis=1).max() <= 100.01


def test_camp_match_scores_matching_and_mixed_cantons():
    camps = pd.DataFrame({"camps2_anti": [90.0, 80.0, 10.0, 20.0], "camps2_netanyahu": [10.0, 20.0, 90.0, 80.0],
                          "valid": 1.0}, index=list("abcd"))
    camps["camps2_leader"] = ["anti", "anti", "netanyahu", "netanyahu"]
    matching = exp.camp_match({"a": 0, "b": 0, "c": 1, "d": 1}, camps, "camps2")
    assert matching["nmi"] == 1.0 and matching["towns_in_their_cantons_leading_camp_pct"] == 100.0
    assert matching["variance_explained"] > 0.9
    mixed = exp.camp_match({"a": 0, "b": 1, "c": 0, "d": 1}, camps, "camps2")
    assert mixed["nmi"] == 0.0 and mixed["variance_explained"] == 0.0
    assert mixed["towns_in_their_cantons_leading_camp_pct"] == 50.0
