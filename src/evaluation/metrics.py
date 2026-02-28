"""Evaluation metrics for canton partitions.

Extracts and extends the evaluation logic from notebook 05 cell 16.
"""

from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score as _sklearn_silhouette

from src.config import BLOC_COLS
from src.clustering.base import CantonAssignment


# ---------------------------------------------------------------------------
# Individual metrics
# ---------------------------------------------------------------------------

def population_balance(
    assignment: CantonAssignment,
    weights: dict[str, float],
) -> dict:
    """Population-balance statistics per canton."""
    canton_pops: dict[int, float] = {c: 0.0 for c in assignment.canton_ids}
    for m, c in assignment.assignments.items():
        canton_pops[c] += weights.get(m, 0.0)

    pops = list(canton_pops.values())
    mean_pop = float(np.mean(pops)) if pops else 0.0
    return {
        "pop_per_canton": canton_pops,
        "pop_min": min(pops) if pops else 0,
        "pop_max": max(pops) if pops else 0,
        "pop_ratio": max(pops) / max(min(pops), 1) if pops else 0,
        "pop_cv": float(np.std(pops) / max(mean_pop, 1e-10)),
    }


def political_homogeneity(
    assignment: CantonAssignment,
    features: pd.DataFrame,
    feature_cols: list[str],
    weights: dict[str, float] | None = None,
) -> dict:
    """Within-canton political variance and dominant-bloc margins."""
    feat = features.copy()
    if "municipality" in feat.columns:
        feat = feat.set_index("municipality")

    canton_stds: list[float] = []
    dominant_margins: list[float] = []

    # Detect bloc-average columns for profile
    bloc_avg_cols = [f"{b}_avg" for b in BLOC_COLS if f"{b}_avg" in feat.columns]
    profile_cols = bloc_avg_cols if bloc_avg_cols else feature_cols

    for c in assignment.canton_ids:
        members = assignment.get_members(c)
        members = [m for m in members if m in feat.index]
        if not members:
            continue

        vals = feat.loc[members, feature_cols].values
        if len(members) > 1:
            canton_stds.append(float(np.mean(np.std(vals, axis=0))))

        # Dominant bloc margin (weighted average profile)
        if weights:
            w = np.array([weights.get(m, 1.0) for m in members])
            profile = np.average(feat.loc[members, profile_cols].values, axis=0, weights=w)
        else:
            profile = feat.loc[members, profile_cols].values.mean(axis=0)

        sorted_vals = sorted(profile, reverse=True)
        margin = sorted_vals[0] - sorted_vals[1] if len(sorted_vals) > 1 else sorted_vals[0]
        dominant_margins.append(margin)

    return {
        "avg_within_std": float(np.mean(canton_stds)) if canton_stds else 0.0,
        "avg_dominant_margin": float(np.mean(dominant_margins)) if dominant_margins else 0.0,
        "min_dominant_margin": float(min(dominant_margins)) if dominant_margins else 0.0,
    }


def wcss(
    assignment: CantonAssignment,
    features: pd.DataFrame,
    feature_cols: list[str],
) -> float:
    """Within-cluster sum of squares."""
    feat = features.copy()
    if "municipality" in feat.columns:
        feat = feat.set_index("municipality")

    total = 0.0
    for c in assignment.canton_ids:
        members = [m for m in assignment.get_members(c) if m in feat.index]
        if not members:
            continue
        vals = feat.loc[members, feature_cols].values
        centroid = vals.mean(axis=0)
        total += float(np.sum((vals - centroid) ** 2))
    return total


def silhouette(
    assignment: CantonAssignment,
    features: pd.DataFrame,
    feature_cols: list[str],
) -> float:
    """Silhouette score (higher is better, range [-1, 1])."""
    feat = features.copy()
    if "municipality" in feat.columns:
        feat = feat.set_index("municipality")

    munis = [m for m in assignment.municipalities if m in feat.index]
    if len(set(assignment.labels_for(munis))) < 2:
        return 0.0

    X = feat.loc[munis, feature_cols].values
    labels = assignment.labels_for(munis)
    return float(_sklearn_silhouette(X, labels))


def contiguity_check(
    assignment: CantonAssignment,
    graph: nx.Graph,
) -> dict:
    """Check geographic contiguity of each canton."""
    disconnected: list[int] = []
    for c in assignment.canton_ids:
        members = [m for m in assignment.get_members(c) if m in graph.nodes()]
        if len(members) <= 1:
            continue
        sub = graph.subgraph(members)
        if not nx.is_connected(sub):
            disconnected.append(c)
    return {
        "n_disconnected": len(disconnected),
        "disconnected_cantons": disconnected,
    }


def canton_profiles(
    assignment: CantonAssignment,
    features: pd.DataFrame,
    weights: dict[str, float],
) -> pd.DataFrame:
    """Weighted political profile per canton."""
    feat = features.copy()
    if "municipality" in feat.columns:
        feat = feat.set_index("municipality")

    bloc_avg_cols = [f"{b}_avg" for b in BLOC_COLS if f"{b}_avg" in feat.columns]
    blocs = [b for b in BLOC_COLS if f"{b}_avg" in feat.columns]

    rows: list[dict] = []
    for c in assignment.canton_ids:
        members = [m for m in assignment.get_members(c) if m in feat.index]
        w = np.array([weights.get(m, 1.0) for m in members])
        total_w = w.sum()

        profile: dict = {
            "canton": c,
            "n_municipalities": len(members),
            "total_voters": int(total_w),
        }

        if bloc_avg_cols:
            for bloc, col in zip(blocs, bloc_avg_cols):
                vals = feat.loc[members, col].values
                profile[f"{bloc}_pct"] = round(float(np.average(vals, weights=w)), 1)

            bloc_pcts = {b: profile[f"{b}_pct"] for b in blocs}
            profile["dominant_bloc"] = max(bloc_pcts, key=bloc_pcts.get)  # type: ignore[arg-type]

        rows.append(profile)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Consolidated evaluator
# ---------------------------------------------------------------------------

def evaluate_all(
    assignment: CantonAssignment,
    features: pd.DataFrame,
    feature_cols: list[str],
    graph: nx.Graph,
    weights: dict[str, float],
) -> dict:
    """Run all evaluation metrics and return a consolidated dict."""
    result: dict = {"k": assignment.k}
    result.update(population_balance(assignment, weights))
    result.update(political_homogeneity(assignment, features, feature_cols, weights))
    result["wcss"] = wcss(assignment, features, feature_cols)
    result["silhouette"] = silhouette(assignment, features, feature_cols)
    result.update(contiguity_check(assignment, graph))
    return result
