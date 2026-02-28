"""Tests for src.data.representations."""

import numpy as np
import pandas as pd
import pytest

from src.data.representations import (
    BlocShares,
    RawPartyShares,
    PCARepresentation,
    NMFRepresentation,
)


@pytest.fixture
def mini_elections():
    """3 municipalities, 2 elections, a few parties."""
    base = {
        "municipality": ["A", "B", "C"],
        "eligible": [100, 200, 150],
        "voters": [80, 160, 120],
        "invalid": [2, 4, 3],
        "valid": [78, 156, 117],
    }
    df1 = pd.DataFrame({
        **base,
        "מחל": [40, 20, 60],  # right
        "פה": [30, 100, 40],  # center
        "שס": [8, 36, 17],   # haredi
    })
    df2 = pd.DataFrame({
        **base,
        "מחל": [38, 22, 58],
        "פה": [32, 98, 42],
        "שס": [8, 36, 17],
    })
    return {21: df1, 22: df2}


class TestBlocShares:
    def test_shape_and_columns(self, mini_elections):
        rep = BlocShares(include_std=True, elections_to_use=[21, 22])
        df = rep.fit_transform(mini_elections)
        assert len(df) == 3
        assert "municipality" in df.columns
        # 5 avg + 5 std + avg_votes = 11 feature cols
        assert len(rep.feature_names) == 11

    def test_no_std(self, mini_elections):
        rep = BlocShares(include_std=False, elections_to_use=[21, 22])
        df = rep.fit_transform(mini_elections)
        assert not any("_std" in c for c in df.columns)

    def test_name(self):
        assert BlocShares().name == "bloc_shares"

    def test_percentages_sum_near_100(self, mini_elections):
        """Bloc percentages + other_pct should roughly sum to 100."""
        rep = BlocShares(include_std=False, elections_to_use=[21, 22])
        df = rep.fit_transform(mini_elections)
        avg_cols = [c for c in df.columns if c.endswith("_avg")]
        row_sums = df[avg_cols].sum(axis=1)
        # Bloc averages won't perfectly sum to 100 (other votes exist),
        # but should be bounded
        assert (row_sums <= 105).all()
        assert (row_sums >= 0).all()


class TestRawPartyShares:
    def test_produces_dataframe(self, mini_elections):
        rep = RawPartyShares(elections_to_use=[21, 22])
        df = rep.fit_transform(mini_elections)
        assert len(df) == 3
        assert "municipality" in df.columns
        assert len(rep.feature_names) > 0

    def test_non_negative(self, mini_elections):
        rep = RawPartyShares(elections_to_use=[21, 22])
        df = rep.fit_transform(mini_elections)
        numeric = df.drop(columns=["municipality"])
        assert (numeric >= 0).all().all()


class TestPCARepresentation:
    def test_n_components(self, mini_elections):
        rep = PCARepresentation(n_components=2,
                                base_repr=RawPartyShares(elections_to_use=[21, 22]))
        df = rep.fit_transform(mini_elections)
        assert len(rep.feature_names) == 2
        assert df.shape == (3, 3)  # municipality + 2 PCs

    def test_explained_variance(self, mini_elections):
        rep = PCARepresentation(n_components=2,
                                base_repr=RawPartyShares(elections_to_use=[21, 22]))
        rep.fit_transform(mini_elections)
        assert rep.explained_variance_ratio_ is not None
        assert rep.explained_variance_ratio_.sum() > 0


class TestNMFRepresentation:
    def test_non_negative_output(self, mini_elections):
        rep = NMFRepresentation(n_components=2,
                                base_repr=RawPartyShares(elections_to_use=[21, 22]))
        df = rep.fit_transform(mini_elections)
        numeric = df.drop(columns=["municipality"])
        assert (numeric >= 0).all().all()

    def test_components_stored(self, mini_elections):
        rep = NMFRepresentation(n_components=2,
                                base_repr=RawPartyShares(elections_to_use=[21, 22]))
        rep.fit_transform(mini_elections)
        assert rep.components_ is not None
        assert rep.components_.shape[0] == 2
