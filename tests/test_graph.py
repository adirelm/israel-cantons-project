"""Tests for src.graph.adjacency and src.graph.preprocessing modules."""

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from src.graph.adjacency import add_tolerance_edges, connect_isolated_to_nearest, get_graph_stats
from src.graph.preprocessing import preprocess_graph
from src.data.distance_metrics import EuclideanDistance


class TestGetGraphStats:
    def test_stats_keys(self):
        G = nx.path_graph(5)
        stats = get_graph_stats(G)
        expected_keys = {"nodes", "edges", "avg_degree", "min_degree",
                         "max_degree", "n_components", "largest_component",
                         "isolated_nodes"}
        assert expected_keys == set(stats.keys())

    def test_path_graph(self):
        G = nx.path_graph(5)  # 0-1-2-3-4
        stats = get_graph_stats(G)
        assert stats["nodes"] == 5
        assert stats["edges"] == 4
        assert stats["min_degree"] == 1
        assert stats["max_degree"] == 2
        assert stats["n_components"] == 1
        assert stats["isolated_nodes"] == 0

    def test_disconnected_graph(self):
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])
        G.add_node(4)  # isolate
        stats = get_graph_stats(G)
        assert stats["nodes"] == 5
        assert stats["n_components"] == 3
        assert stats["isolated_nodes"] == 1


class TestPreprocessGraph:
    def test_connects_isolated_nodes(self):
        """Isolated node should get virtual edges after preprocessing."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])
        G.add_node("E")  # isolated

        features = pd.DataFrame({
            "right_avg": [60, 55, 10, 15, 50],
            "left_avg": [10, 10, 30, 35, 10],
        }, index=["A", "B", "C", "D", "E"])
        feature_cols = ["right_avg", "left_avg"]

        G_aug = preprocess_graph(G, features, feature_cols, metric=EuclideanDistance())
        # E should now have edges
        assert G_aug.degree("E") > 0

    def test_preserves_original_edges(self):
        """Original edges should still exist in augmented graph."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])

        features = pd.DataFrame({
            "right_avg": [60, 55, 10],
            "left_avg": [10, 10, 30],
        }, index=["A", "B", "C"])
        feature_cols = ["right_avg", "left_avg"]

        G_aug = preprocess_graph(G, features, feature_cols, metric=EuclideanDistance())
        assert G_aug.has_edge("A", "B")
        assert G_aug.has_edge("B", "C")

    def test_output_is_graph(self):
        G = nx.path_graph(3)
        nx.relabel_nodes(G, {0: "A", 1: "B", 2: "C"}, copy=False)

        features = pd.DataFrame({
            "f1": [1.0, 2.0, 3.0],
        }, index=["A", "B", "C"])

        G_aug = preprocess_graph(G, features, ["f1"], metric=EuclideanDistance())
        assert isinstance(G_aug, nx.Graph)
        assert G_aug.number_of_nodes() >= 3



def _squares(*rects):
    return gpd.GeoDataFrame({"MUN_HEB": [n for n, _ in rects]},
                            geometry=[box(*r) for _, r in rects], crs="EPSG:2039")


class TestToleranceEdges:
    def test_near_shared_side_is_adjacent(self):
        geo = _squares(("A", (0, 0, 1000, 1000)), ("B", (1050, 0, 2000, 1000)))
        G = add_tolerance_edges(nx.Graph([("X", "Y")]), geo, {"B"}, tolerance_m=100)
        assert G.has_edge("A", "B") and G.has_edge("X", "Y")

    def test_corner_contact_and_far_polygons_are_not_adjacent(self):
        geo = _squares(("A", (0, 0, 1000, 1000)), ("B", (1000, 1000, 2000, 2000)), ("C", (3000, 0, 4000, 1000)))
        G = add_tolerance_edges(nx.Graph(), geo, {"B", "C"}, tolerance_m=100)
        assert not G.has_edge("A", "B") and not G.has_edge("A", "C")

    def test_only_listed_nodes_get_tolerance_edges(self):
        geo = _squares(("A", (0, 0, 1000, 1000)), ("B", (1050, 0, 2000, 1000)))
        G = add_tolerance_edges(nx.Graph(), geo, set(), tolerance_m=100)
        assert G.number_of_edges() == 0


class TestConnectIsolated:
    def test_isolated_node_joins_its_nearest_polygon(self):
        geo = _squares(("A", (0, 0, 1000, 1000)), ("B", (1500, 0, 2500, 1000)), ("C", (5000, 0, 6000, 1000)))
        G = connect_isolated_to_nearest(nx.Graph([("A", "C")]), geo, {"B"})
        assert G.has_edge("B", "A") and not G.has_edge("B", "C")

    def test_nodes_with_neighbours_are_untouched(self):
        geo = _squares(("A", (0, 0, 1000, 1000)), ("B", (1500, 0, 2500, 1000)), ("C", (2600, 0, 3000, 1000)))
        G = connect_isolated_to_nearest(nx.Graph([("B", "C")]), geo, {"B"})
        assert set(G.edges()) == {("B", "C")}
