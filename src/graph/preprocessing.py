"""Graph preprocessing: virtual edges, enclave edges, bridge edges.

Transforms the raw adjacency graph into a fully connected graph suitable
for clustering.  Extracts logic from notebook 05 cells 7-9.

All similarity computations use a pluggable ``DistanceMetric`` rather than
hard-coding cosine similarity.
"""

from __future__ import annotations

import numpy as np
import networkx as nx
import pandas as pd

from src.config import BLOC_COLS
from src.data.distance_metrics import DistanceMetric, CosineDistance


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _similarity_matrix(
    features: pd.DataFrame,
    feature_cols: list[str],
    metric: DistanceMetric,
) -> tuple[list[str], np.ndarray]:
    """Return (municipality_list, similarity_matrix).

    Similarity = 1 − normalised_distance so higher is more similar.
    """
    munis = list(features.index if features.index.name == "municipality"
                 else features["municipality"])
    X = features[feature_cols].values if feature_cols[0] in features.columns else features.values
    D = metric.pairwise(X)
    # Normalise to [0, 1] and flip to similarity
    d_max = D.max() if D.max() > 0 else 1.0
    S = 1.0 - D / d_max
    return munis, S


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_virtual_edges_for_isolated(
    G: nx.Graph,
    features: pd.DataFrame,
    feature_cols: list[str],
    k_neighbors: int = 3,
    metric: DistanceMetric | None = None,
) -> nx.Graph:
    """Connect isolated (degree-0) nodes to *k* most similar municipalities."""
    metric = metric or CosineDistance()
    G_aug = G.copy()

    isolated = [n for n in G_aug.nodes() if G_aug.degree(n) == 0]
    if not isolated:
        return G_aug

    idx_col = features.index.name or ""
    if idx_col != "municipality" and "municipality" in features.columns:
        features = features.set_index("municipality")

    munis = list(features.index)
    X = features[feature_cols].values
    # Use the passed metric for similarity computation
    D = metric.pairwise(X)
    d_max = D.max() if D.max() > 0 else 1.0
    sims = 1.0 - D / d_max

    for node in isolated:
        if node not in munis:
            continue
        node_idx = munis.index(node)
        candidates = [
            (sims[node_idx, i], m)
            for i, m in enumerate(munis)
            if m != node and m in G_aug.nodes()
        ]
        candidates.sort(reverse=True)
        for sim, neighbor in candidates[:k_neighbors]:
            G_aug.add_edge(node, neighbor, weight=sim, virtual=True)

    return G_aug


def add_enclave_edges(
    G: nx.Graph,
    features: pd.DataFrame,
    feature_cols: list[str],
    enclave_threshold: float = 70.0,
) -> nx.Graph:
    """Connect political enclaves (>threshold % in a single bloc) of the same type."""
    G_aug = G.copy()

    idx_col = features.index.name or ""
    if idx_col != "municipality" and "municipality" in features.columns:
        features = features.set_index("municipality")

    # Use only *_avg bloc columns that are present
    avg_cols = [c for c in BLOC_COLS if f"{c}_avg" in features.columns]
    if avg_cols:
        bloc_cols_to_check = [f"{c}_avg" for c in avg_cols]
    else:
        bloc_cols_to_check = [c for c in feature_cols if c in features.columns]

    enclaves: dict[str, list[str]] = {}
    for muni in features.index:
        for col in bloc_cols_to_check:
            if features.loc[muni, col] > enclave_threshold:
                enclaves.setdefault(col, []).append(muni)

    edges_added = 0
    for _bloc, members in enclaves.items():
        if len(members) <= 1:
            continue
        for i, m1 in enumerate(members):
            for m2 in members[i + 1 :]:
                if not G_aug.has_edge(m1, m2):
                    G_aug.add_edge(m1, m2, weight=0.5, enclave=True)
                    edges_added += 1

    return G_aug


def add_bridge_edges(
    G: nx.Graph,
    features: pd.DataFrame,
    feature_cols: list[str],
    metric: DistanceMetric | None = None,
) -> nx.Graph:
    """Connect remaining disconnected components to the largest component."""
    metric = metric or CosineDistance()
    G_aug = G.copy()

    if nx.is_connected(G_aug):
        return G_aug

    idx_col = features.index.name or ""
    if idx_col != "municipality" and "municipality" in features.columns:
        features = features.set_index("municipality")

    components = list(nx.connected_components(G_aug))
    largest = max(components, key=len)

    X = features[feature_cols].values
    munis = list(features.index)
    D = metric.pairwise(X)
    d_max = D.max() if D.max() > 0 else 1.0
    sims = 1.0 - D / d_max

    for comp in components:
        if comp == largest:
            continue
        best_sim = -1.0
        best_pair: tuple[str, str] | None = None
        for m1 in comp:
            if m1 not in munis:
                continue
            i = munis.index(m1)
            for m2 in largest:
                if m2 not in munis:
                    continue
                j = munis.index(m2)
                if sims[i, j] > best_sim:
                    best_sim = sims[i, j]
                    best_pair = (m1, m2)
        if best_pair:
            G_aug.add_edge(best_pair[0], best_pair[1], weight=best_sim, bridge=True)

    return G_aug


def preprocess_graph(
    G: nx.Graph,
    features: pd.DataFrame,
    feature_cols: list[str],
    isolate_k: int = 3,
    enclave_threshold: float = 70.0,
    metric: DistanceMetric | None = None,
) -> nx.Graph:
    """Run full graph preprocessing pipeline.

    1. Add virtual edges for isolated nodes.
    2. Add enclave edges for political enclaves.
    3. Add bridge edges for any remaining disconnected components.

    Returns a connected graph.
    """
    G_aug = add_virtual_edges_for_isolated(G, features, feature_cols, isolate_k, metric)
    G_aug = add_enclave_edges(G_aug, features, feature_cols, enclave_threshold)
    G_aug = add_bridge_edges(G_aug, features, feature_cols, metric)
    return G_aug
