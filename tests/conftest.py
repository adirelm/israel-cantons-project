"""Shared test fixtures for Israel Cantons project."""

import numpy as np
import pandas as pd
import networkx as nx
import pytest


@pytest.fixture
def small_graph() -> nx.Graph:
    """6-node line graph with one branch: A-B-C-D-E, B-F."""
    G = nx.Graph()
    G.add_edges_from([("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("B", "F")])
    return G


@pytest.fixture
def small_features() -> pd.DataFrame:
    """6 municipalities with synthetic bloc percentages."""
    return pd.DataFrame({
        "municipality": ["A", "B", "C", "D", "E", "F"],
        "right_avg": [60.0, 55.0, 10.0, 15.0, 80.0, 50.0],
        "haredi_avg": [5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
        "center_avg": [20.0, 25.0, 40.0, 35.0, 10.0, 30.0],
        "left_avg": [10.0, 10.0, 30.0, 35.0, 3.0, 10.0],
        "arab_avg": [5.0, 5.0, 15.0, 10.0, 2.0, 5.0],
        "avg_votes": [1000.0, 2000.0, 1500.0, 1000.0, 500.0, 1000.0],
    })


@pytest.fixture
def small_feature_cols() -> list[str]:
    return ["right_avg", "haredi_avg", "center_avg", "left_avg", "arab_avg"]


@pytest.fixture
def small_weights() -> dict[str, float]:
    return {"A": 1000, "B": 2000, "C": 1500, "D": 1000, "E": 500, "F": 1000}


@pytest.fixture
def sample_elections() -> dict[int, pd.DataFrame]:
    """Minimal election DataFrames for 2 'elections' with 3 municipalities."""
    base = {
        "municipality": ["X", "Y", "Z"],
        "eligible": [100, 200, 150],
        "voters": [80, 160, 120],
        "invalid": [2, 4, 3],
        "valid": [78, 156, 117],
    }
    df1 = pd.DataFrame({
        **base,
        "מחל": [40, 20, 60],
        "פה": [30, 100, 40],
        "שס": [8, 36, 17],
        "knesset": 21,
    })
    df2 = pd.DataFrame({
        **base,
        "מחל": [38, 22, 58],
        "פה": [32, 98, 42],
        "שס": [8, 36, 17],
        "knesset": 22,
    })
    return {21: df1, 22: df2}
