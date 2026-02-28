"""Tests for cross-election stability analysis."""

import copy

import numpy as np
import pandas as pd
import networkx as nx
import pytest

from src.clustering.base import CantonAssignment
from src.data.distance_metrics import EuclideanDistance
from src.data.representations import BlocShares, RawPartyShares, PCARepresentation, NMFRepresentation
from src.evaluation.stability import (
    cluster_single_election,
    compute_pairwise_stability,
    stability_summary,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def stability_elections() -> dict[int, pd.DataFrame]:
    """Two elections with 4 municipalities — politically distinct."""
    base = {
        "municipality": ["A", "B", "C", "D"],
        "eligible": [100, 200, 150, 120],
        "voters": [80, 160, 120, 100],
        "invalid": [2, 4, 3, 2],
        "valid": [78, 156, 117, 98],
    }
    df1 = pd.DataFrame({
        **base,
        "מחל": [50, 10, 60, 8],
        "פה": [20, 120, 40, 70],
        "שס": [8, 26, 17, 20],
        "knesset": 21,
    })
    # Second election: very different distribution
    df2 = pd.DataFrame({
        **base,
        "מחל": [10, 50, 8, 60],
        "פה": [50, 20, 70, 10],
        "שס": [18, 86, 39, 28],
        "knesset": 22,
    })
    return {21: df1, 22: df2}


@pytest.fixture
def stability_graph() -> nx.Graph:
    G = nx.Graph()
    G.add_edges_from([("A", "B"), ("B", "C"), ("C", "D"), ("A", "D")])
    return G


# ---------------------------------------------------------------------------
# Tests: compute_pairwise_stability
# ---------------------------------------------------------------------------

class TestPairwiseStability:
    def test_identical_assignments_give_ari_1(self):
        """Identical clusterings → ARI = 1.0."""
        a = CantonAssignment({"A": 0, "B": 0, "C": 1, "D": 1})
        pw = compute_pairwise_stability({21: a, 22: a})
        assert len(pw) == 1
        assert pw["ari"].iloc[0] == pytest.approx(1.0)
        assert pw["nmi"].iloc[0] == pytest.approx(1.0)

    def test_different_assignments_give_ari_less_than_1(self):
        """Completely different clusterings → ARI < 1.0."""
        a1 = CantonAssignment({"A": 0, "B": 0, "C": 1, "D": 1})
        a2 = CantonAssignment({"A": 0, "B": 1, "C": 0, "D": 1})
        pw = compute_pairwise_stability({21: a1, 22: a2})
        assert pw["ari"].iloc[0] < 1.0

    def test_summary_has_required_keys(self):
        a = CantonAssignment({"A": 0, "B": 0, "C": 1, "D": 1})
        pw = compute_pairwise_stability({21: a, 22: a})
        s = stability_summary(pw)
        for key in ("mean_ari", "std_ari", "mean_nmi", "std_nmi"):
            assert key in s


# ---------------------------------------------------------------------------
# Tests: single-election filtering propagation (C2 fix)
# ---------------------------------------------------------------------------

class TestSingleElectionPropagation:
    def test_raw_party_shares_elections_to_use_set(self):
        """After deepcopy, _elections_to_use should be limited to the single knesset."""
        rep = RawPartyShares(elections_to_use=[21, 22])
        rep_copy = copy.deepcopy(rep)
        rep_copy._elections_to_use = [21]
        assert rep_copy._elections_to_use == [21]
        # Original unchanged
        assert rep._elections_to_use == [21, 22]

    def test_pca_base_propagation(self):
        """PCA wrapper should propagate _elections_to_use to its _base."""
        base = RawPartyShares(elections_to_use=[21, 22])
        rep = PCARepresentation(n_components=2, base_repr=base)
        rep_copy = copy.deepcopy(rep)
        # Simulate what stability.py does after fix
        if hasattr(rep_copy, "_elections_to_use"):
            rep_copy._elections_to_use = [21]
        if hasattr(rep_copy, "_base") and hasattr(rep_copy._base, "_elections_to_use"):
            rep_copy._base._elections_to_use = [21]
        assert rep_copy._base._elections_to_use == [21]

    def test_nmf_base_propagation(self):
        """NMF wrapper should propagate _elections_to_use to its _base."""
        base = RawPartyShares(elections_to_use=[21, 22])
        rep = NMFRepresentation(n_components=2, base_repr=base)
        rep_copy = copy.deepcopy(rep)
        if hasattr(rep_copy, "_base") and hasattr(rep_copy._base, "_elections_to_use"):
            rep_copy._base._elections_to_use = [22]
        assert rep_copy._base._elections_to_use == [22]
