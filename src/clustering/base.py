"""Base classes and protocols for clustering algorithms.

Every clustering algorithm returns a ``CantonAssignment`` and implements
the ``SpatialClusterer`` protocol so they are interchangeable.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import networkx as nx
import numpy as np
import pandas as pd

from src.data.distance_metrics import DistanceMetric


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

class CantonAssignment:
    """Stores a municipality → canton mapping with optional metadata."""

    def __init__(
        self,
        assignments: dict[str, int],
        metadata: dict | None = None,
    ) -> None:
        self.assignments = assignments
        self.metadata = metadata or {}

    # -- properties --

    @property
    def k(self) -> int:
        return len(set(self.assignments.values()))

    @property
    def canton_ids(self) -> list[int]:
        return sorted(set(self.assignments.values()))

    @property
    def municipalities(self) -> list[str]:
        return list(self.assignments.keys())

    # -- helpers --

    def get_members(self, canton_id: int) -> list[str]:
        return [m for m, c in self.assignments.items() if c == canton_id]

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            [{"municipality": m, "canton": c} for m, c in self.assignments.items()]
        )

    def labels_for(self, municipalities: list[str]) -> list[int]:
        """Return canton labels aligned to the given municipality order."""
        return [self.assignments[m] for m in municipalities]


# ---------------------------------------------------------------------------
# Clusterer protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class SpatialClusterer(Protocol):
    """Interface every clustering algorithm must satisfy."""

    @property
    def name(self) -> str: ...

    def fit(
        self,
        features: pd.DataFrame,
        feature_cols: list[str],
        graph: nx.Graph,
        k: int,
        distance_metric: DistanceMetric,
        weights: dict[str, float] | None = None,
        **kwargs,
    ) -> CantonAssignment:
        """Run clustering and return a ``CantonAssignment``."""
        ...
