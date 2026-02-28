"""Pluggable political representations.

Each class transforms election DataFrames into a municipality × feature matrix.
All representations implement the same interface so they can be swapped freely
in the clustering pipeline (per advisor guidance).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA, NMF

from src.config import BLOC_MAPPING, BLOC_COLS, KNESSET_IDS, NON_PARTY_COLS


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class Representation(Protocol):
    """Interface every representation must satisfy."""

    @property
    def name(self) -> str: ...

    @property
    def feature_names(self) -> list[str]: ...

    def fit_transform(self, elections: dict[int, pd.DataFrame]) -> pd.DataFrame:
        """Return DataFrame indexed by *municipality* with numeric feature columns."""
        ...


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_party_columns(df: pd.DataFrame) -> list[str]:
    """Party vote-count columns (no _pct, no metadata)."""
    return [
        c for c in df.columns
        if c not in NON_PARTY_COLS
        and not c.endswith("_pct")
        and c != "סמל ועדה"
    ]


def _common_municipalities(elections: dict[int, pd.DataFrame]) -> list[str]:
    """Municipalities present in every election."""
    sets = [set(df["municipality"]) for df in elections.values()]
    common = sets[0]
    for s in sets[1:]:
        common &= s
    return sorted(common)


# ---------------------------------------------------------------------------
# 1. Raw Party Shares
# ---------------------------------------------------------------------------

class RawPartyShares:
    """Average raw party vote percentages across elections.

    The union of all party codes across all elections is used.  Parties
    absent from a given election receive 0 %.  This is the highest-dimensional
    representation (~100+ features).
    """

    def __init__(self, elections_to_use: list[int] | None = None) -> None:
        self._elections_to_use = elections_to_use or KNESSET_IDS
        self._feature_names: list[str] = []

    @property
    def name(self) -> str:
        return "raw_party_shares"

    @property
    def feature_names(self) -> list[str]:
        return list(self._feature_names)

    def fit_transform(self, elections: dict[int, pd.DataFrame]) -> pd.DataFrame:
        munis = _common_municipalities(elections)
        # Collect all unique party codes
        all_parties: set[str] = set()
        for k_id in self._elections_to_use:
            all_parties.update(_get_party_columns(elections[k_id]))
        all_parties_sorted = sorted(all_parties)

        # Build per-election percentage matrices
        pct_matrices: list[pd.DataFrame] = []
        for k_id in self._elections_to_use:
            df = elections[k_id].set_index("municipality").loc[munis]
            valid = df["valid"]
            pct = pd.DataFrame(0.0, index=munis, columns=all_parties_sorted)
            for p in _get_party_columns(elections[k_id]):
                if p in df.columns:
                    pct[p] = (df[p].div(valid.replace(0, np.nan)).mul(100).fillna(0.0)).values
            pct_matrices.append(pct)

        # Average across elections
        avg = sum(pct_matrices) / len(pct_matrices)  # type: ignore[arg-type]
        avg.index.name = "municipality"

        self._feature_names = all_parties_sorted
        return avg.reset_index()


# ---------------------------------------------------------------------------
# 2. Bloc Shares (current approach from notebook 04)
# ---------------------------------------------------------------------------

class BlocShares:
    """Manual 5-bloc grouping: right, haredi, center, left, arab.

    Produces 5 average-percentage features and optionally 5 standard-deviation
    features measuring cross-election stability.
    """

    def __init__(
        self,
        include_std: bool = True,
        bloc_mapping: dict[int, dict[str, str]] | None = None,
        elections_to_use: list[int] | None = None,
    ) -> None:
        self._include_std = include_std
        self._bloc_mapping = bloc_mapping or BLOC_MAPPING
        self._elections_to_use = elections_to_use or KNESSET_IDS
        self._feature_names: list[str] = []

    @property
    def name(self) -> str:
        return "bloc_shares"

    @property
    def feature_names(self) -> list[str]:
        return list(self._feature_names)

    # ---- internal ----

    def _bloc_percentages_for_election(
        self, df: pd.DataFrame, knesset: int
    ) -> pd.DataFrame:
        mapping = self._bloc_mapping[knesset]
        result = pd.DataFrame()
        result["municipality"] = df["municipality"]
        result["valid_votes"] = df["valid"]

        for bloc in BLOC_COLS:
            bloc_parties = [p for p, b in mapping.items() if b == bloc]
            existing = [p for p in bloc_parties if p in df.columns]
            result[f"{bloc}_votes"] = df[existing].sum(axis=1) if existing else pd.Series(0, index=df.index)
            result[f"{bloc}_pct"] = result[f"{bloc}_votes"].div(result["valid_votes"].replace(0, np.nan)).mul(100).fillna(0.0)

        mapped_votes = sum(result[f"{b}_votes"] for b in BLOC_COLS)
        result["other_votes"] = result["valid_votes"] - mapped_votes
        result["other_pct"] = result["other_votes"].div(result["valid_votes"].replace(0, np.nan)).mul(100).fillna(0.0)
        return result

    # ---- public ----

    def fit_transform(self, elections: dict[int, pd.DataFrame]) -> pd.DataFrame:
        munis = _common_municipalities(elections)

        bloc_data: dict[int, pd.DataFrame] = {}
        for k_id in self._elections_to_use:
            bloc_data[k_id] = self._bloc_percentages_for_election(
                elections[k_id], k_id
            )

        features = pd.DataFrame({"municipality": munis})

        for bloc in BLOC_COLS:
            pcts = []
            for k_id in self._elections_to_use:
                bd = bloc_data[k_id].set_index("municipality")
                pcts.append(bd.loc[munis, f"{bloc}_pct"].values)
            features[f"{bloc}_avg"] = np.mean(pcts, axis=0)
            if self._include_std:
                features[f"{bloc}_std"] = np.std(pcts, axis=0)

        # Average valid votes across elections
        vote_arrays = []
        for k_id in self._elections_to_use:
            bd = bloc_data[k_id].set_index("municipality")
            vote_arrays.append(bd.loc[munis, "valid_votes"].values)
        features["avg_votes"] = np.mean(vote_arrays, axis=0)

        feat_cols = [c for c in features.columns if c != "municipality"]
        self._feature_names = feat_cols
        return features


# ---------------------------------------------------------------------------
# 3. PCA on raw party shares
# ---------------------------------------------------------------------------

class PCARepresentation:
    """PCA dimensionality reduction on raw party shares.

    Useful for discovering latent political dimensions algorithmically
    (as suggested by the advisor).
    """

    def __init__(
        self,
        n_components: int = 5,
        base_repr: Representation | None = None,
    ) -> None:
        self._n_components = n_components
        self._base = base_repr or RawPartyShares()
        self._feature_names: list[str] = []
        self.explained_variance_ratio_: np.ndarray | None = None

    @property
    def name(self) -> str:
        return f"pca_{self._n_components}"

    @property
    def feature_names(self) -> list[str]:
        return list(self._feature_names)

    def fit_transform(self, elections: dict[int, pd.DataFrame]) -> pd.DataFrame:
        base_df = self._base.fit_transform(elections)
        munis = base_df["municipality"].values
        X = base_df.drop(columns=["municipality"]).values

        pca = PCA(n_components=self._n_components)
        X_pca = pca.fit_transform(X)
        self.explained_variance_ratio_ = pca.explained_variance_ratio_

        cols = [f"pc{i+1}" for i in range(self._n_components)]
        self._feature_names = cols

        result = pd.DataFrame(X_pca, columns=cols)
        result.insert(0, "municipality", munis)
        return result


# ---------------------------------------------------------------------------
# 4. NMF on raw party shares
# ---------------------------------------------------------------------------

class NMFRepresentation:
    """Non-negative Matrix Factorisation on raw party shares.

    Components are interpretable as latent political "blocs" discovered
    algorithmically (advisor's suggestion).  Unlike PCA, outputs are
    non-negative, making them compatible with Jensen-Shannon divergence.
    """

    def __init__(
        self,
        n_components: int = 5,
        base_repr: Representation | None = None,
        random_state: int = 42,
    ) -> None:
        self._n_components = n_components
        self._base = base_repr or RawPartyShares()
        self._random_state = random_state
        self._feature_names: list[str] = []
        self.components_: np.ndarray | None = None

    @property
    def name(self) -> str:
        return f"nmf_{self._n_components}"

    @property
    def feature_names(self) -> list[str]:
        return list(self._feature_names)

    def fit_transform(self, elections: dict[int, pd.DataFrame]) -> pd.DataFrame:
        base_df = self._base.fit_transform(elections)
        munis = base_df["municipality"].values
        X = base_df.drop(columns=["municipality"]).values

        # Clip small negatives from floating-point noise
        X = np.clip(X, 0, None)

        model = NMF(
            n_components=self._n_components,
            random_state=self._random_state,
            max_iter=500,
        )
        W = model.fit_transform(X)
        self.components_ = model.components_

        cols = [f"nmf{i+1}" for i in range(self._n_components)]
        self._feature_names = cols

        result = pd.DataFrame(W, columns=cols)
        result.insert(0, "municipality", munis)
        return result
