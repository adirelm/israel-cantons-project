"""Tests for simulated annealing spatial clustering."""

import networkx as nx
import numpy as np
import pandas as pd
import pytest

from src.clustering.simulated_annealing import SimulatedAnnealingClusterer
from src.data.distance_metrics import EuclideanDistance


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sa_graph_10() -> nx.Graph:
    """10-node graph with two dense clusters connected by a bridge."""
    G = nx.Graph()
    # Cluster 1: A-E fully connected
    for i, u in enumerate(["A", "B", "C", "D", "E"]):
        for v in ["A", "B", "C", "D", "E"][i + 1:]:
            G.add_edge(u, v)
    # Cluster 2: F-J fully connected
    for i, u in enumerate(["F", "G", "H", "I", "J"]):
        for v in ["F", "G", "H", "I", "J"][i + 1:]:
            G.add_edge(u, v)
    # Bridge
    G.add_edge("E", "F")
    return G


@pytest.fixture
def sa_features_10() -> pd.DataFrame:
    """10 municipalities — two distinct political profiles."""
    return pd.DataFrame({
        "municipality": list("ABCDEFGHIJ"),
        "right_avg": [70, 65, 68, 72, 66, 10, 12, 15, 8, 11],
        "haredi_avg": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        "center_avg": [15, 20, 17, 13, 19, 40, 38, 35, 42, 39],
        "left_avg": [8, 8, 8, 8, 8, 35, 35, 35, 35, 35],
        "arab_avg": [2, 2, 2, 2, 2, 10, 10, 10, 10, 10],
        "avg_votes": [1000] * 10,
    })


@pytest.fixture
def sa_feature_cols() -> list[str]:
    return ["right_avg", "haredi_avg", "center_avg", "left_avg", "arab_avg"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSABasic:
    def test_produces_k_clusters(self, sa_features_10, sa_feature_cols, sa_graph_10):
        clust = SimulatedAnnealingClusterer(
            max_iterations=1000, random_seed=42
        )
        result = clust.fit(
            features=sa_features_10,
            feature_cols=sa_feature_cols,
            graph=sa_graph_10,
            k=2,
            distance_metric=EuclideanDistance(),
        )
        assert result.k == 2
        assert len(result.assignments) == 10

    def test_all_municipalities_assigned(self, sa_features_10, sa_feature_cols, sa_graph_10):
        clust = SimulatedAnnealingClusterer(max_iterations=500, random_seed=42)
        result = clust.fit(sa_features_10, sa_feature_cols, sa_graph_10,
                           k=3, distance_metric=EuclideanDistance())
        assert set(result.municipalities) == set(sa_features_10["municipality"])

    def test_contiguity(self, sa_features_10, sa_feature_cols, sa_graph_10):
        """Each canton should be a connected subgraph."""
        clust = SimulatedAnnealingClusterer(max_iterations=2000, random_seed=42)
        result = clust.fit(sa_features_10, sa_feature_cols, sa_graph_10,
                           k=2, distance_metric=EuclideanDistance())
        for cid in result.canton_ids:
            members = result.get_members(cid)
            sub = sa_graph_10.subgraph(members)
            assert nx.is_connected(sub), f"Canton {cid} is disconnected"


class TestSAKGreaterThan5:
    """Test fix C1: SA should support K > 5 (more than BLOC_COLS)."""

    def test_k_10_produces_correct_clusters(self):
        """With 12 nodes and K=10, SA should produce 10 cantons."""
        G = nx.path_graph(12)
        G = nx.relabel_nodes(G, {i: f"M{i}" for i in range(12)})
        munis = [f"M{i}" for i in range(12)]
        features = pd.DataFrame({
            "municipality": munis,
            "right_avg": np.linspace(10, 90, 12),
            "haredi_avg": np.linspace(5, 30, 12),
            "center_avg": np.linspace(30, 10, 12),
            "left_avg": np.linspace(5, 40, 12),
            "arab_avg": np.linspace(2, 20, 12),
            "avg_votes": [1000] * 12,
        })
        feature_cols = ["right_avg", "haredi_avg", "center_avg", "left_avg", "arab_avg"]

        clust = SimulatedAnnealingClusterer(max_iterations=5000, random_seed=42)
        result = clust.fit(features, feature_cols, G, k=10,
                           distance_metric=EuclideanDistance())
        # Should produce exactly 10 cantons (not be limited to 5)
        assert result.k == 10, f"Expected K=10 but got K={result.k}"

    def test_k_7_with_bloc_features(self):
        """K=7 should work even though only 5 bloc columns exist."""
        G = nx.path_graph(14)
        G = nx.relabel_nodes(G, {i: f"N{i}" for i in range(14)})
        munis = [f"N{i}" for i in range(14)]
        rng = np.random.RandomState(42)
        features = pd.DataFrame({
            "municipality": munis,
            "right_avg": rng.uniform(10, 80, 14),
            "haredi_avg": rng.uniform(2, 20, 14),
            "center_avg": rng.uniform(10, 40, 14),
            "left_avg": rng.uniform(5, 40, 14),
            "arab_avg": rng.uniform(2, 25, 14),
            "avg_votes": [1000] * 14,
        })
        feature_cols = ["right_avg", "haredi_avg", "center_avg", "left_avg", "arab_avg"]

        clust = SimulatedAnnealingClusterer(max_iterations=5000, random_seed=42)
        result = clust.fit(features, feature_cols, G, k=7,
                           distance_metric=EuclideanDistance())
        assert result.k == 7, f"Expected K=7 but got K={result.k}"
