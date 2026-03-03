"""Cross-election stability analysis.

Cluster each election independently and compute pairwise ARI / NMI
to measure how stable canton boundaries are across electoral cycles.
"""

from __future__ import annotations

import copy

import networkx as nx
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

from src.config import KNESSET_IDS
from src.clustering.base import CantonAssignment, SpatialClusterer
from src.data.distance_metrics import DistanceMetric
from src.data.representations import Representation


def cluster_single_election(
    knesset: int,
    elections: dict[int, pd.DataFrame],
    representation: Representation,
    distance_metric: DistanceMetric,
    clusterer: SpatialClusterer,
    graph: nx.Graph,
    k: int,
    **kwargs,
) -> CantonAssignment:
    """Cluster municipalities using data from a single election."""

    # Create a copy of the representation limited to this single election
    rep = copy.deepcopy(representation)
    if hasattr(rep, "_elections_to_use"):
        rep._elections_to_use = [knesset]
    # NMF/PCA wrappers delegate to a _base representation (e.g. RawPartyShares)
    # which holds _elections_to_use — propagate there too.
    if hasattr(rep, "_base") and hasattr(rep._base, "_elections_to_use"):
        rep._base._elections_to_use = [knesset]

    features = rep.fit_transform(elections)
    feature_cols = rep.feature_names

    weights = None
    if "avg_votes" in features.columns:
        weights = dict(zip(features["municipality"], features["avg_votes"]))

    return clusterer.fit(
        features=features,
        feature_cols=feature_cols,
        graph=graph,
        k=k,
        distance_metric=distance_metric,
        weights=weights,
        **kwargs,
    )


def compute_pairwise_stability(
    assignments: dict[int, CantonAssignment],
) -> pd.DataFrame:
    """Compute ARI and NMI between all pairs of election-specific clusterings.

    Parameters
    ----------
    assignments : dict mapping knesset_id → CantonAssignment

    Returns
    -------
    DataFrame with columns: knesset_a, knesset_b, ari, nmi
    """
    knesset_ids = sorted(assignments.keys())
    # Align municipality order across all assignments
    common = set.intersection(
        *(set(a.municipalities) for a in assignments.values())
    )
    munis = sorted(common)

    rows: list[dict] = []
    for i, ka in enumerate(knesset_ids):
        la = assignments[ka].labels_for(munis)
        for kb in knesset_ids[i + 1 :]:
            lb = assignments[kb].labels_for(munis)
            rows.append({
                "knesset_a": ka,
                "knesset_b": kb,
                "ari": adjusted_rand_score(la, lb),
                "nmi": normalized_mutual_info_score(la, lb),
            })

    return pd.DataFrame(rows)


def stability_summary(pairwise: pd.DataFrame) -> dict:
    """Aggregate pairwise stability into summary statistics."""
    return {
        "mean_ari": float(pairwise["ari"].mean()),
        "std_ari": float(pairwise["ari"].std()),
        "mean_nmi": float(pairwise["nmi"].mean()),
        "std_nmi": float(pairwise["nmi"].std()),
    }


def run_stability_analysis(
    elections: dict[int, pd.DataFrame],
    representation: Representation,
    distance_metric: DistanceMetric,
    clusterer: SpatialClusterer,
    graph: nx.Graph,
    k: int,
    knesset_ids: list[int] | None = None,
    **kwargs,
) -> tuple[dict[int, CantonAssignment], pd.DataFrame, dict]:
    """Run full stability analysis pipeline.

    Returns (per_election_assignments, pairwise_df, summary_dict).
    """
    knesset_ids = knesset_ids or KNESSET_IDS
    per_election: dict[int, CantonAssignment] = {}

    for kid in knesset_ids:
        per_election[kid] = cluster_single_election(
            knesset=kid,
            elections=elections,
            representation=representation,
            distance_metric=distance_metric,
            clusterer=clusterer,
            graph=graph,
            k=k,
            **kwargs,
        )

    pw = compute_pairwise_stability(per_election)
    summary = stability_summary(pw)
    return per_election, pw, summary
