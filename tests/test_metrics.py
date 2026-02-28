"""Tests for src.evaluation.metrics."""

import networkx as nx
import numpy as np
import pandas as pd
import pytest

from src.clustering.base import CantonAssignment
from src.evaluation.metrics import (
    population_balance,
    wcss,
    silhouette,
    contiguity_check,
)


@pytest.fixture
def simple_assignment():
    return CantonAssignment({"A": 0, "B": 0, "C": 1, "D": 1, "E": 1, "F": 0})


@pytest.fixture
def simple_weights():
    return {"A": 100, "B": 200, "C": 150, "D": 100, "E": 50, "F": 100}


class TestPopulationBalance:
    def test_returns_expected_keys(self, simple_assignment, simple_weights):
        result = population_balance(simple_assignment, simple_weights)
        assert "pop_cv" in result
        assert "pop_ratio" in result
        assert result["pop_min"] > 0

    def test_perfect_balance(self):
        a = CantonAssignment({"A": 0, "B": 1})
        w = {"A": 100, "B": 100}
        result = population_balance(a, w)
        assert result["pop_cv"] == pytest.approx(0.0)
        assert result["pop_ratio"] == pytest.approx(1.0)

    def test_imbalanced_ratio(self):
        """pop_ratio should reflect max/min population."""
        a = CantonAssignment({"A": 0, "B": 1})
        w = {"A": 100, "B": 300}
        result = population_balance(a, w)
        assert result["pop_ratio"] == pytest.approx(3.0)
        assert result["pop_cv"] > 0


class TestWCSS:
    def test_non_negative(self, simple_assignment, small_features, small_feature_cols):
        val = wcss(simple_assignment, small_features, small_feature_cols)
        assert val >= 0

    def test_zero_for_single_member_clusters(self, small_features, small_feature_cols):
        a = CantonAssignment({m: i for i, m in enumerate(small_features["municipality"])})
        val = wcss(a, small_features, small_feature_cols)
        assert val == pytest.approx(0.0)


class TestSilhouette:
    def test_range(self, simple_assignment, small_features, small_feature_cols):
        val = silhouette(simple_assignment, small_features, small_feature_cols)
        assert -1.0 <= val <= 1.0


class TestContiguityCheck:
    def test_connected(self, small_graph):
        # A-B-F in one canton, C-D-E in another → both connected
        a = CantonAssignment({"A": 0, "B": 0, "F": 0, "C": 1, "D": 1, "E": 1})
        result = contiguity_check(a, small_graph)
        assert result["n_disconnected"] == 0

    def test_disconnected(self, small_graph):
        # A and E in one canton but not connected
        a = CantonAssignment({"A": 0, "E": 0, "B": 1, "C": 1, "D": 1, "F": 1})
        result = contiguity_check(a, small_graph)
        assert result["n_disconnected"] > 0
