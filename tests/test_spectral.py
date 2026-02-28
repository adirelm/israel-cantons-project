"""Tests for src.clustering.spectral (Louvain, Spectral) and src.clustering.baseline (KMeans)."""

import networkx as nx
import numpy as np
import pandas as pd
import pytest

from src.clustering.spectral import LouvainSpatialClusterer, SpectralSpatialClusterer
from src.clustering.baseline import KMeansBaselineClusterer
from src.data.distance_metrics import EuclideanDistance


@pytest.fixture
def grid_graph_and_features():
    """4x3 grid graph with 12 nodes and distinct left/right features."""
    G = nx.grid_2d_graph(4, 3)
    # Relabel to strings
    mapping = {(r, c): f"N{r}_{c}" for r, c in G.nodes()}
    G = nx.relabel_nodes(G, mapping)
    nodes = sorted(G.nodes())

    # Create features: left half is "right-wing", right half is "left-wing"
    features_data = []
    for n in nodes:
        r, c = int(n.split("_")[0][1:]), int(n.split("_")[1])
        if r < 2:
            features_data.append({"municipality": n, "f1": 80 + np.random.rand(), "f2": 10 + np.random.rand()})
        else:
            features_data.append({"municipality": n, "f1": 10 + np.random.rand(), "f2": 80 + np.random.rand()})

    features = pd.DataFrame(features_data)
    weights = {n: 1000.0 for n in nodes}
    return G, features, ["f1", "f2"], weights


class TestLouvainSpatialClusterer:
    def test_produces_assignment(self, grid_graph_and_features):
        G, features, feature_cols, weights = grid_graph_and_features
        clust = LouvainSpatialClusterer(random_seed=42)
        result = clust.fit(features, feature_cols, G, k=2,
                          distance_metric=EuclideanDistance(), weights=weights)
        assert result.k >= 1
        assert len(result.assignments) == len(features)

    def test_targets_k(self, grid_graph_and_features):
        G, features, feature_cols, weights = grid_graph_and_features
        clust = LouvainSpatialClusterer(random_seed=42, max_sweep_iters=30)
        result = clust.fit(features, feature_cols, G, k=3,
                          distance_metric=EuclideanDistance(), weights=weights)
        # Should be close to K=3 (may not be exact due to Louvain heuristic)
        assert abs(result.k - 3) <= 2

    def test_name_property(self):
        clust = LouvainSpatialClusterer()
        assert clust.name == "louvain"


class TestSpectralSpatialClusterer:
    def test_produces_k_clusters(self, grid_graph_and_features):
        G, features, feature_cols, weights = grid_graph_and_features
        clust = SpectralSpatialClusterer(random_state=42)
        result = clust.fit(features, feature_cols, G, k=2,
                          distance_metric=EuclideanDistance(), weights=weights)
        assert result.k == 2
        assert len(result.assignments) == len(features)

    def test_name_property(self):
        clust = SpectralSpatialClusterer()
        assert clust.name == "spectral"


class TestKMeansBaselineClusterer:
    def test_produces_k_clusters(self, grid_graph_and_features):
        G, features, feature_cols, weights = grid_graph_and_features
        clust = KMeansBaselineClusterer(random_state=42)
        result = clust.fit(features, feature_cols, G, k=3,
                          distance_metric=EuclideanDistance(), weights=weights)
        assert result.k == 3
        assert len(result.assignments) == len(features)

    def test_all_municipalities_assigned(self, grid_graph_and_features):
        G, features, feature_cols, weights = grid_graph_and_features
        clust = KMeansBaselineClusterer(random_state=42)
        result = clust.fit(features, feature_cols, G, k=2,
                          distance_metric=EuclideanDistance(), weights=weights)
        assert set(result.municipalities) == set(features["municipality"])

    def test_name_property(self):
        clust = KMeansBaselineClusterer()
        assert clust.name == "kmeans_baseline"
