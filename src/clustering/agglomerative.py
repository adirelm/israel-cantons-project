"""Greedy agglomerative spatial clustering with contiguity constraint.

Starts with each municipality as its own cluster and iteratively merges
the most similar adjacent pair until *k* clusters remain.

This is the algorithm described in the project specification (Ward's
criterion variant with spatial constraint).
"""

from __future__ import annotations

import heapq
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

from src.clustering.base import CantonAssignment
from src.data.distance_metrics import DistanceMetric


class AgglomerativeSpatialClusterer:
    """Greedy agglomerative clustering respecting spatial contiguity."""

    def __init__(self, linkage: str = "average") -> None:
        if linkage not in ("single", "complete", "average", "ward"):
            raise ValueError(f"Unsupported linkage: {linkage}")
        self._linkage = linkage

    @property
    def name(self) -> str:
        return f"agglomerative_{self._linkage}"

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
        X = feat.loc[munis, feature_cols].values
        n = len(munis)
        muni_to_idx = {m: i for i, m in enumerate(munis)}

        # Pairwise distance matrix
        D = distance_metric.pairwise(X)
        self._X = X  # store for Ward centroid computation

        # Initial clusters: each municipality is its own cluster
        cluster_of: dict[str, int] = {m: i for i, m in enumerate(munis)}
        cluster_members: dict[int, list[int]] = {i: [i] for i in range(n)}
        next_cid = n

        # Build initial priority queue of (distance, cid_a, cid_b) for adjacent pairs
        pq: list[tuple[float, int, int]] = []
        for u, v in graph.subgraph(munis).edges():
            i, j = muni_to_idx[u], muni_to_idx[v]
            d = self._linkage_distance(D, [i], [j])
            heapq.heappush(pq, (d, cluster_of[u], cluster_of[v]))

        n_clusters = n

        while n_clusters > k and pq:
            dist, ca, cb = heapq.heappop(pq)

            # Skip stale entries (clusters already merged)
            if ca not in cluster_members or cb not in cluster_members:
                continue

            # Merge cb into ca
            new_cid = next_cid
            next_cid += 1
            merged = cluster_members[ca] + cluster_members[cb]
            cluster_members[new_cid] = merged
            del cluster_members[ca]
            del cluster_members[cb]

            # Update cluster_of for all municipalities
            for idx in merged:
                cluster_of[munis[idx]] = new_cid

            n_clusters -= 1

            # Find adjacent clusters of the new cluster
            adj_clusters: set[int] = set()
            for idx in merged:
                m = munis[idx]
                for nbr in graph.neighbors(m):
                    if nbr in cluster_of:
                        nbr_cid = cluster_of[nbr]
                        if nbr_cid != new_cid:
                            adj_clusters.add(nbr_cid)

            # Push new merge candidates
            for adj_cid in adj_clusters:
                if adj_cid in cluster_members:
                    d = self._linkage_distance(
                        D, cluster_members[new_cid], cluster_members[adj_cid]
                    )
                    heapq.heappush(pq, (d, new_cid, adj_cid))

        # Build final assignments (renumber 0..k-1)
        cid_list = sorted(cluster_members.keys())
        cid_map = {old: new for new, old in enumerate(cid_list)}
        assignments = {m: cid_map[cluster_of[m]] for m in munis}

        return CantonAssignment(
            assignments=assignments,
            metadata={"algorithm": self.name, "linkage": self._linkage, "k": k},
        )

    # ------------------------------------------------------------------
    # Linkage helpers
    # ------------------------------------------------------------------

    def _linkage_distance(
        self, D: np.ndarray, members_a: list[int], members_b: list[int]
    ) -> float:
        dists = [D[i, j] for i in members_a for j in members_b]
        if not dists:
            return float("inf")
        if self._linkage == "single":
            return min(dists)
        if self._linkage == "complete":
            return max(dists)
        if self._linkage == "average":
            return float(np.mean(dists))
        # ward: squared Euclidean between centroids, scaled by sizes
        if self._linkage == "ward":
            na, nb = len(members_a), len(members_b)
            centroid_a = np.mean(self._X[members_a], axis=0)
            centroid_b = np.mean(self._X[members_b], axis=0)
            sq_dist = float(np.sum((centroid_a - centroid_b) ** 2))
            return sq_dist * (na * nb) / (na + nb)
        return float(np.mean(dists))
