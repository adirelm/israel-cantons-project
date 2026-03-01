"""Graph-based clustering algorithms: Louvain community detection and spectral clustering.

These use the graph topology weighted by political similarity.
"""

from __future__ import annotations

from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.cluster import SpectralClustering

from src.clustering.base import CantonAssignment
from src.data.distance_metrics import DistanceMetric


class LouvainSpatialClusterer:
    """Louvain community detection on the adjacency graph.

    Edge weights are set to political similarity (1 − normalised distance).
    The ``resolution`` parameter controls granularity — higher values produce
    more communities.

    A binary search over the ``resolution`` parameter is performed to find the
    resolution that yields a number of communities closest to ``k``.
    """

    def __init__(self, resolution: float = 1.0, random_seed: int = 42,
                 max_sweep_iters: int = 30) -> None:
        self._resolution = resolution
        self._random_seed = random_seed
        self._max_sweep_iters = max_sweep_iters

    @property
    def name(self) -> str:
        return "louvain"

    def _run_louvain(self, G: nx.Graph, resolution: float) -> list[set]:
        return list(nx.community.louvain_communities(
            G,
            resolution=resolution,
            seed=self._random_seed,
        ))

    def fit(
        self,
        features: pd.DataFrame,
        feature_cols: list[str],
        graph: nx.Graph,
        k: int,
        distance_metric: DistanceMetric,
        weights: dict[str, float] | None = None,
        **kwargs: Any,
    ) -> CantonAssignment:
        feat = features.copy()
        if "municipality" in feat.columns:
            feat = feat.set_index("municipality")

        munis = [m for m in feat.index if m in graph.nodes()]

        if k < 1 or k > len(munis):
            raise ValueError(
                f"k must be between 1 and {len(munis)} (number of municipalities), got {k}"
            )

        G = graph.subgraph(munis).copy()

        # Weight edges by political similarity
        X = feat.loc[munis, feature_cols].values
        D = distance_metric.pairwise(X)
        d_max = D.max() if D.max() > 0 else 1.0
        muni_idx = {m: i for i, m in enumerate(munis)}

        for u, v in G.edges():
            sim = 1.0 - D[muni_idx[u], muni_idx[v]] / d_max
            G[u][v]["weight"] = max(sim, 1e-6)

        # Binary search over resolution to target k communities
        lo, hi = 0.01, 10.0
        best_communities = self._run_louvain(G, self._resolution)
        best_diff = abs(len(best_communities) - k)
        best_res = self._resolution

        if best_diff != 0:
            for _ in range(self._max_sweep_iters):
                mid = (lo + hi) / 2
                communities = self._run_louvain(G, mid)
                n_comm = len(communities)
                diff = abs(n_comm - k)
                if diff < best_diff:
                    best_diff = diff
                    best_communities = communities
                    best_res = mid
                if n_comm == k:
                    break
                if n_comm < k:
                    lo = mid  # need more communities → higher resolution
                else:
                    hi = mid  # need fewer communities → lower resolution
                if hi - lo < 1e-6:
                    break

        assignments: dict[str, int] = {}
        for cid, community in enumerate(best_communities):
            for m in community:
                assignments[m] = cid

        return CantonAssignment(
            assignments=assignments,
            metadata={
                "algorithm": self.name,
                "resolution": best_res,
                "k_detected": len(best_communities),
                "k_requested": k,
            },
        )


class SpectralSpatialClusterer:
    """Spectral clustering on the graph Laplacian weighted by political similarity."""

    def __init__(self, random_state: int = 42) -> None:
        self._random_state = random_state

    @property
    def name(self) -> str:
        return "spectral"

    def fit(
        self,
        features: pd.DataFrame,
        feature_cols: list[str],
        graph: nx.Graph,
        k: int,
        distance_metric: DistanceMetric,
        weights: dict[str, float] | None = None,
        **kwargs: Any,
    ) -> CantonAssignment:
        feat = features.copy()
        if "municipality" in feat.columns:
            feat = feat.set_index("municipality")

        munis = [m for m in feat.index if m in graph.nodes()]
        n = len(munis)

        if k < 1 or k > n:
            raise ValueError(
                f"k must be between 1 and {n} (number of municipalities), got {k}"
            )

        G = graph.subgraph(munis).copy()

        # Build affinity matrix from graph + similarity
        X = feat.loc[munis, feature_cols].values
        D = distance_metric.pairwise(X)
        d_max = D.max() if D.max() > 0 else 1.0
        muni_idx = {m: i for i, m in enumerate(munis)}

        n = len(munis)
        affinity = np.zeros((n, n))
        for u, v in G.edges():
            sim = 1.0 - D[muni_idx[u], muni_idx[v]] / d_max
            affinity[muni_idx[u], muni_idx[v]] = max(sim, 1e-6)
            affinity[muni_idx[v], muni_idx[u]] = max(sim, 1e-6)

        sc = SpectralClustering(
            n_clusters=k,
            affinity="precomputed",
            random_state=self._random_state,
            assign_labels="kmeans",
        )
        labels = sc.fit_predict(affinity)

        assignments = dict(zip(munis, [int(l) for l in labels]))
        return CantonAssignment(
            assignments=assignments,
            metadata={"algorithm": self.name, "k": k},
        )
