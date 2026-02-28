"""Tests for clustering algorithms."""

import networkx as nx
import numpy as np
import pandas as pd
import pytest

from src.clustering.base import CantonAssignment
from src.clustering.baseline import KMeansBaselineClusterer
from src.clustering.agglomerative import AgglomerativeSpatialClusterer
from src.data.distance_metrics import EuclideanDistance


class TestCantonAssignment:
    def test_basic_properties(self):
        a = CantonAssignment({"A": 0, "B": 0, "C": 1})
        assert a.k == 2
        assert a.canton_ids == [0, 1]
        assert set(a.get_members(0)) == {"A", "B"}
        assert a.get_members(1) == ["C"]

    def test_to_dataframe(self):
        a = CantonAssignment({"A": 0, "B": 1})
        df = a.to_dataframe()
        assert len(df) == 2
        assert set(df.columns) == {"municipality", "canton"}

    def test_labels_for(self):
        a = CantonAssignment({"A": 0, "B": 1, "C": 0})
        assert a.labels_for(["C", "B", "A"]) == [0, 1, 0]


class TestKMeansBaseline:
    def test_produces_k_clusters(self, small_features, small_feature_cols, small_graph):
        clust = KMeansBaselineClusterer()
        result = clust.fit(
            features=small_features,
            feature_cols=small_feature_cols,
            graph=small_graph,
            k=2,
            distance_metric=EuclideanDistance(),
        )
        assert result.k == 2
        assert set(result.municipalities) == set(small_features["municipality"])

    def test_all_assigned(self, small_features, small_feature_cols, small_graph):
        clust = KMeansBaselineClusterer()
        result = clust.fit(small_features, small_feature_cols, small_graph,
                           k=3, distance_metric=EuclideanDistance())
        assert len(result.assignments) == len(small_features)


class TestAgglomerativeSpatial:
    def test_produces_k_clusters(self, small_features, small_feature_cols, small_graph):
        clust = AgglomerativeSpatialClusterer(linkage="average")
        result = clust.fit(
            features=small_features,
            feature_cols=small_feature_cols,
            graph=small_graph,
            k=2,
            distance_metric=EuclideanDistance(),
        )
        assert result.k == 2

    def test_contiguous_clusters(self, small_features, small_feature_cols, small_graph):
        clust = AgglomerativeSpatialClusterer(linkage="average")
        result = clust.fit(small_features, small_feature_cols, small_graph,
                           k=2, distance_metric=EuclideanDistance())
        # Each cluster subgraph should be connected
        for cid in result.canton_ids:
            members = result.get_members(cid)
            sub = small_graph.subgraph(members)
            assert nx.is_connected(sub), f"Canton {cid} is not contiguous"
