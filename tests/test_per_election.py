"""Tests for src.evaluation.per_election."""

import pytest

from src.evaluation.per_election import align_to_reference, changes_table


def test_align_relabels_by_largest_overlap():
    reference = {"a": 0, "b": 0, "c": 1, "d": 1, "e": 2}
    assignment = {"a": 7, "b": 7, "c": 3, "d": 3, "e": 9}
    assert align_to_reference(assignment, reference) == reference


def test_align_is_one_to_one_even_when_a_canton_splits():
    reference = {"a": 0, "b": 0, "c": 0, "d": 1}
    assignment = {"a": 5, "b": 5, "c": 6, "d": 6}
    out = align_to_reference(assignment, reference)
    assert sorted(set(out.values())) == [0, 1] and out["a"] == out["b"] == 0 and out["d"] == 1


def test_canton_with_little_overlap_gets_a_new_id_instead_of_a_misleading_label():
    reference = {"a": 0, "b": 0, "c": 1, "d": 1, "e": 2, "f": 2, "g": 2}
    assignment = {"a": 7, "b": 7, "c": 8, "d": 8, "e": 8, "f": 8, "g": 9}
    out = align_to_reference(assignment, reference)
    assert out["a"] == 0 and out["c"] == 1  # majority-overlap matches keep their label
    assert out["g"] == 3                    # {g} shares 1 of 3 with canton 2: new ID


def test_align_rejects_different_canton_counts():
    with pytest.raises(ValueError, match="3 cantons"):
        align_to_reference({"a": 0, "b": 1, "c": 2}, {"a": 0, "b": 1, "c": 1})


def test_changes_table_counts_elections_that_differ_from_primary():
    reference = {"a": 0, "b": 1}
    maps = {21: {"a": 0, "b": 1}, 22: {"a": 1, "b": 1}}
    t = changes_table(maps, reference).set_index("municipality")
    assert t.loc["a", "n_differ"] == 1 and t.loc["b", "n_differ"] == 0
    assert list(t.columns) == ["primary", "knesset_21", "knesset_22", "n_differ"]
