"""Baseline (non-spatial) clustering algorithms.

These ignore the adjacency graph and serve as comparison baselines.
"""

from __future__ import annotations

from typing import Any

import networkx as nx
import pandas as pd
from sklearn.cluster import KMeans

from src.clustering.base import CantonAssignment
from src.data.distance_metrics import DistanceMetric


class KMeansBaselineClusterer:
    """Standard K-means on the feature matrix (no spatial constraint).

    Expected to produce non-contiguous cantons — that is the point.
    """

    def __init__(self, random_state: int = 42, n_init: int = 10) -> None:
        self._random_state = random_state
        self._n_init = n_init

    @property
    def name(self) -> str:
        return "kmeans_baseline"

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

        # Filter to municipalities present in graph (consistent with other clusterers)
        munis = [m for m in feat.index if m in graph.nodes()]
        X = feat.loc[munis, feature_cols].values

        if k < 1 or k > len(munis):
            raise ValueError(
                f"k must be between 1 and {len(munis)} (number of municipalities), got {k}"
            )

        km = KMeans(
            n_clusters=k,
            random_state=self._random_state,
            n_init=self._n_init,
        )
        labels = km.fit_predict(X)

        assignments = dict(zip(munis, [int(l) for l in labels]))
        return CantonAssignment(
            assignments=assignments,
            metadata={
                "algorithm": self.name,
                "inertia": float(km.inertia_),
                "k": k,
            },
        )
