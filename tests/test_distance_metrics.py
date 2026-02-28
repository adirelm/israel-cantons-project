"""Tests for src.data.distance_metrics."""

import numpy as np
import pytest

from src.data.distance_metrics import (
    EuclideanDistance,
    CosineDistance,
    JensenShannonDistance,
)


@pytest.fixture
def X():
    return np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [1.0, 1.0, 0.0],
    ])


class TestEuclidean:
    def test_identity(self, X):
        d = EuclideanDistance()
        assert d.between(X[0], X[0]) == pytest.approx(0.0)

    def test_symmetry(self, X):
        d = EuclideanDistance()
        assert d.between(X[0], X[1]) == pytest.approx(d.between(X[1], X[0]))

    def test_pairwise_shape(self, X):
        d = EuclideanDistance()
        D = d.pairwise(X)
        assert D.shape == (3, 3)
        assert D[0, 0] == pytest.approx(0.0)

    def test_triangle_inequality(self, X):
        d = EuclideanDistance()
        assert d.between(X[0], X[1]) <= d.between(X[0], X[2]) + d.between(X[2], X[1])


class TestCosine:
    def test_identity(self, X):
        d = CosineDistance()
        assert d.between(X[0], X[0]) == pytest.approx(0.0, abs=1e-10)

    def test_symmetry(self, X):
        d = CosineDistance()
        assert d.between(X[0], X[1]) == pytest.approx(d.between(X[1], X[0]))

    def test_orthogonal_vectors(self, X):
        d = CosineDistance()
        # [1,0,0] and [0,1,0] are orthogonal → cosine distance = 1
        assert d.between(X[0], X[1]) == pytest.approx(1.0)


class TestJensenShannon:
    def test_identity(self):
        d = JensenShannonDistance()
        v = np.array([0.5, 0.3, 0.2])
        assert d.between(v, v) == pytest.approx(0.0, abs=1e-10)

    def test_symmetry(self):
        d = JensenShannonDistance()
        a = np.array([0.7, 0.2, 0.1])
        b = np.array([0.1, 0.3, 0.6])
        assert d.between(a, b) == pytest.approx(d.between(b, a))

    def test_bounded(self):
        d = JensenShannonDistance()
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 0.0, 1.0])
        val = d.between(a, b)
        assert 0.0 <= val <= 1.0

    def test_pairwise(self):
        d = JensenShannonDistance()
        X = np.array([[0.5, 0.3, 0.2], [0.1, 0.8, 0.1], [0.3, 0.3, 0.4]])
        D = d.pairwise(X)
        assert D.shape == (3, 3)
        assert D[0, 0] == pytest.approx(0.0, abs=1e-10)

    def test_pairwise_symmetric(self):
        """Pairwise distance matrix should be symmetric."""
        d = JensenShannonDistance()
        X = np.array([[0.5, 0.3, 0.2], [0.1, 0.8, 0.1], [0.3, 0.3, 0.4]])
        D = d.pairwise(X)
        np.testing.assert_array_almost_equal(D, D.T)


class TestEuclideanValues:
    def test_known_distance(self):
        d = EuclideanDistance()
        a = np.array([0.0, 0.0])
        b = np.array([3.0, 4.0])
        assert d.between(a, b) == pytest.approx(5.0)

    def test_pairwise_symmetric(self):
        d = EuclideanDistance()
        X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        D = d.pairwise(X)
        np.testing.assert_array_almost_equal(D, D.T)


class TestCosineValues:
    def test_parallel_vectors(self):
        """Parallel vectors → cosine distance = 0."""
        d = CosineDistance()
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([2.0, 4.0, 6.0])
        assert d.between(a, b) == pytest.approx(0.0, abs=1e-10)

    def test_pairwise_symmetric(self):
        d = CosineDistance()
        X = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
        D = d.pairwise(X)
        np.testing.assert_array_almost_equal(D, D.T)
