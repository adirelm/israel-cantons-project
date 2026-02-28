"""Chart visualisations: bar charts, heatmaps, elbow plots.

For experiment analysis, political profiles, and stability reports.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


_BLOC_COLORS = {
    "right": "blue", "haredi": "black", "center": "purple",
    "left": "red", "arab": "green",
}


def plot_political_composition(
    profiles: pd.DataFrame,
    figsize: tuple[int, int] = (10, 6),
) -> plt.Figure:
    """Stacked bar chart of bloc percentages per canton."""
    blocs = [b for b in ["right", "haredi", "center", "left", "arab"]
             if f"{b}_pct" in profiles.columns]

    fig, ax = plt.subplots(figsize=figsize)
    bottom = np.zeros(len(profiles))
    for bloc in blocs:
        vals = profiles[f"{bloc}_pct"].values
        ax.bar(profiles["canton"].astype(str), vals, bottom=bottom,
               label=bloc.capitalize(), color=_BLOC_COLORS.get(bloc, "gray"), alpha=0.85)
        bottom += vals

    ax.set_xlabel("Canton")
    ax.set_ylabel("Percentage")
    ax.set_title("Political Composition by Canton")
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig


def plot_population_balance(
    profiles: pd.DataFrame,
    target: float | None = None,
    figsize: tuple[int, int] = (10, 5),
) -> plt.Figure:
    """Bar chart of voters per canton with optional target line."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(profiles["canton"].astype(str),
           profiles["total_voters"] / 1000,
           color=plt.cm.Set3(np.linspace(0, 1, len(profiles))))  # type: ignore[attr-defined]

    if target is not None:
        ax.axhline(y=target / 1000, color="red", linestyle="--",
                    label=f"Target ({target/1000:.0f}K)")
        ax.legend()

    ax.set_xlabel("Canton")
    ax.set_ylabel("Voters (thousands)")
    ax.set_title("Population per Canton")
    fig.tight_layout()
    return fig


def plot_experiment_results(
    results: pd.DataFrame,
    metric: str = "silhouette",
    group_by: str = "repr",
    figsize: tuple[int, int] = (12, 6),
) -> plt.Figure:
    """Line or bar plot of a metric across the experiment grid."""
    fig, ax = plt.subplots(figsize=figsize)

    for name, grp in results.groupby(group_by):
        grp_sorted = grp.sort_values("k_target")
        ax.plot(grp_sorted["k_target"], grp_sorted[metric],
                marker="o", label=str(name))

    ax.set_xlabel("K (target)")
    ax.set_ylabel(metric)
    ax.set_title(f"{metric} vs K by {group_by}")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_stability_heatmap(
    pairwise: pd.DataFrame,
    metric: str = "ari",
    figsize: tuple[int, int] = (8, 6),
) -> plt.Figure:
    """Heatmap of pairwise ARI or NMI across elections."""
    knessets = sorted(set(pairwise["knesset_a"]) | set(pairwise["knesset_b"]))
    n = len(knessets)
    mat = np.eye(n)
    kid_idx = {k: i for i, k in enumerate(knessets)}

    for _, row in pairwise.iterrows():
        i = kid_idx[row["knesset_a"]]
        j = kid_idx[row["knesset_b"]]
        mat[i, j] = row[metric]
        mat[j, i] = row[metric]

    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(mat, annot=True, fmt=".2f",
                xticklabels=[str(k) for k in knessets],
                yticklabels=[str(k) for k in knessets],
                cmap="YlOrRd", vmin=0, vmax=1, ax=ax)
    ax.set_title(f"Pairwise {metric.upper()} across Elections")
    fig.tight_layout()
    return fig


def plot_elbow(
    results: pd.DataFrame,
    algo: str | None = None,
    repr_name: str | None = None,
    metric_name: str | None = None,
    y_metric: str = "wcss",
    figsize: tuple[int, int] = (10, 5),
) -> plt.Figure:
    """WCSS / silhouette vs K for a given algo/repr/metric combo."""
    df = results.copy()
    if algo:
        df = df[df["algo"] == algo]
    if repr_name:
        df = df[df["repr"] == repr_name]
    if metric_name:
        df = df[df["metric"] == metric_name]

    df = df.sort_values("k_target")

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(df["k_target"], df[y_metric], marker="o", linewidth=2)
    ax.set_xlabel("K (target)")
    ax.set_ylabel(y_metric)
    title_parts = [y_metric, "vs K"]
    if algo:
        title_parts.append(f"[{algo}]")
    if repr_name:
        title_parts.append(f"[{repr_name}]")
    if metric_name:
        title_parts.append(f"[{metric_name}]")
    ax.set_title(" ".join(title_parts))
    fig.tight_layout()
    return fig
