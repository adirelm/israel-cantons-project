"""Pluggable distance metrics.

Each class computes pairwise distances from a feature matrix.
All metrics implement the same interface so they can be swapped freely
in the clustering pipeline (per advisor guidance).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np
from scipy.spatial.distance import (
    cdist,
    jensenshannon,
    pdist,
    squareform,
)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class DistanceMetric(Protocol):
    """Interface every distance metric must satisfy."""

    @property
    def name(self) -> str: ...

    def pairwise(self, X: np.ndarray) -> np.ndarray:
        """Return (n, n) symmetric distance matrix."""
        ...

    def between(self, a: np.ndarray, b: np.ndarray) -> float:
        """Distance between two 1-D vectors."""
        ...


# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------

class EuclideanDistance:
    """Standard Euclidean distance."""

    @property
    def name(self) -> str:
        return "euclidean"

    def pairwise(self, X: np.ndarray) -> np.ndarray:
        return squareform(pdist(X, metric="euclidean"))

    def between(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.linalg.norm(a - b))


class CosineDistance:
    """Cosine distance: ``1 - cosine_similarity``."""

    @property
    def name(self) -> str:
        return "cosine"

    def pairwise(self, X: np.ndarray) -> np.ndarray:
        return squareform(pdist(X, metric="cosine"))

    def between(self, a: np.ndarray, b: np.ndarray) -> float:
        dot = np.dot(a, b)
        norms = np.linalg.norm(a) * np.linalg.norm(b)
        if norms == 0:
            return 0.0
        return float(1.0 - dot / norms)


class JensenShannonDistance:
    """Square root of Jensen-Shannon divergence.

    Input vectors must be non-negative (vote-share-like).  Each row is
    normalised to a probability distribution before computation.

    Compatible with ``BlocShares``, ``RawPartyShares``, and
    ``NMFRepresentation``.  **Not compatible** with ``PCARepresentation``
    (which may produce negative values).
    """

    @property
    def name(self) -> str:
        return "jensen_shannon"

    @staticmethod
    def _to_distribution(v: np.ndarray) -> np.ndarray:
        s = v.sum()
        if s == 0:
            return np.ones_like(v) / len(v)
        return v / s

    def pairwise(self, X: np.ndarray) -> np.ndarray:
        n = X.shape[0]
        P = np.array([self._to_distribution(row) for row in X])
        D = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                d = jensenshannon(P[i], P[j])
                D[i, j] = d
                D[j, i] = d
        return D

    def between(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(
            jensenshannon(
                self._to_distribution(a),
                self._to_distribution(b),
            )
        )
