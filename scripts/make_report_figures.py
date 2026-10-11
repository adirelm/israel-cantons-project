#!/usr/bin/env python3
"""Regenerate the data-driven figures in docs/figures from data/processed.

    python scripts/make_report_figures.py

Run after scripts/rebuild_results.py. docs/figures/pipeline.png is a static
diagram and is not touched.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.config import BLOC_COLS, DATA_PROCESSED, PROJECT_ROOT

FIG_DIR = PROJECT_ROOT / "docs" / "figures"
DPI = 200

ALGOS = {  # grid name -> (label, colour)
    "simulated_annealing": ("Simulated Annealing", "#e41a1c"),
    "agglomerative_average": ("Agglomerative", "#377eb8"),
    "kmeans_baseline": ("K-Means (baseline)", "#984ea3"),
    "louvain": ("Louvain", "#4daf4a"),
}
REPRS = {"bloc_shares": "BlocShares", "nmf_5": "NMF_5", "pca_5": "PCA_5", "raw_party_shares": "RawParty"}
BLOC_COLORS = {"right": "#5794f7", "haredi": "#808590", "center": "#b36ff5", "left": "#f06060", "arab": "#44cc77"}
CANTON_COLORS = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00"]
NO_COUNTERPART_COLOR = "#9e9e9e"
ELECTION_LABELS = {21: "April 2019", 22: "September 2019", 23: "March 2020", 24: "March 2021", 25: "November 2022"}
STABILITY_SHORT = {
    "BlocShares / Euclidean / SA": "Bloc / Euc / SA",
    "BlocShares / Cosine / Agglom": "Bloc / Cos / Agglom",
    "BlocShares / Euclidean / Louvain": "Bloc / Euc / Louvain",
    "NMF_5 / Euclidean / SA": "NMF5 / Euc / SA",
    "PCA_5 / Euclidean / SA": "PCA5 / Euc / SA",
    "RawParty / Cosine / SA": "Raw / Cos / SA",
    "NMF_5 / Cosine / Louvain": "NMF5 / Cos / Louvain\n(primary)",
}


def silhouette_vs_k(results: pd.DataFrame) -> None:
    sub = results[(results["repr"] == "bloc_shares") & (results["metric"] == "euclidean")]
    fig, ax = plt.subplots(figsize=(8.9, 4.8))
    for algo, (label, color) in ALGOS.items():
        rows = sub[sub["algo"] == algo].sort_values("k_target")
        ax.plot(rows["k_target"], rows["silhouette"], "o-", color=color, label=label, linewidth=2)
    ax.axhline(0, color="gray", linestyle="--", linewidth=0.5, alpha=0.7)
    ax.set_xlabel("K (Number of Cantons)")
    ax.set_ylabel("Silhouette Score")
    ax.set_title("Silhouette Score vs K (BlocShares / Euclidean)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "silhouette_vs_k.png", dpi=DPI)
    plt.close(fig)


def heatmap_silhouette(results: pd.DataFrame) -> None:
    best = results.pivot_table(index="repr", columns="algo", values="silhouette", aggfunc="max")
    best = best.loc[list(REPRS), ["agglomerative_average", "kmeans_baseline", "louvain", "simulated_annealing"]]
    best.index = [REPRS[r] for r in best.index]
    best.columns = ["Agglom.", "K-Means", "Louvain", "SA"]
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    sns.heatmap(best, annot=True, fmt=".3f", cmap="RdYlGn", vmin=-1, vmax=1, linewidths=1, linecolor="white", ax=ax)
    ax.set_title("Best Silhouette Score by Representation × Algorithm")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "heatmap_silhouette.png", dpi=DPI)
    plt.close(fig)


def canton_map(labeled: pd.DataFrame, geo: gpd.GeoDataFrame) -> None:
    canton = dict(zip(labeled["municipality"], labeled["canton"]))
    names = dict(zip(labeled["canton"], labeled["label"]))
    geo = geo.copy()
    geo["canton"] = geo["MUN_HEB"].map(canton)
    geo = geo.dropna(subset=["canton"])
    fig, ax = plt.subplots(figsize=(5.0, 13.9))
    patches = []
    for cid in sorted(names):
        color = CANTON_COLORS[cid % len(CANTON_COLORS)]
        geo[geo["canton"] == cid].plot(ax=ax, color=color, edgecolor="black", linewidth=0.4)
        patches.append(mpatches.Patch(color=color, label=f"Canton {cid}: {names[cid]}"))
    ax.legend(handles=patches, loc="lower right", fontsize=8, title="Cantons", title_fontsize=9, framealpha=0.9)
    ax.set_title("K=5 Canton Partition (NMF_5 / Cosine / Louvain)", fontsize=11)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "canton_map_k5.png", dpi=DPI)
    plt.close(fig)


def per_election_maps(labeled: pd.DataFrame, geo: gpd.GeoDataFrame) -> None:
    names = dict(zip(labeled["canton"], labeled["label"]))
    color = lambda c: CANTON_COLORS[c] if c in names else NO_COUNTERPART_COLOR  # noqa: E731
    fig, axes = plt.subplots(1, 5, figsize=(15, 8.5))
    unmatched = False
    for ax, (k, title) in zip(axes, ELECTION_LABELS.items()):
        canton = dict(pd.read_csv(DATA_PROCESSED / "per_election" / f"knesset_{k}.csv").values)
        g = geo.assign(canton=geo["MUN_HEB"].map(canton)).dropna(subset=["canton"])
        for cid in sorted(set(canton.values())):
            g[g["canton"] == cid].plot(ax=ax, color=color(cid), edgecolor="black", linewidth=0.15)
            unmatched |= cid not in names
        ax.set_title(title, fontsize=11)
        ax.set_axis_off()
    patches = [mpatches.Patch(color=color(c), label=f"{c}: {n}") for c, n in sorted(names.items())]
    if unmatched:
        patches.append(mpatches.Patch(color=NO_COUNTERPART_COLOR, label="No counterpart in the primary map"))
    fig.legend(handles=patches, loc="lower center", ncol=len(patches), fontsize=9, frameon=False)
    fig.suptitle("K=5 cantons computed from each election separately (NMF_5 / Cosine / Louvain)", fontsize=13)
    fig.tight_layout(rect=(0, 0.05, 1, 0.97))
    fig.savefig(FIG_DIR / "per_election_maps.png", dpi=DPI)
    plt.close(fig)


def political_composition(stats: pd.DataFrame) -> None:
    stats = stats.sort_values("canton")
    labels = [f"Canton {c}\n({b.upper()})" for c, b in zip(stats["canton"], stats["dominant_bloc"])]
    fig, ax = plt.subplots(figsize=(8.9, 4.8))
    bottom = np.zeros(len(stats))
    for bloc in BLOC_COLS:
        vals = stats[f"{bloc}_pct"].to_numpy()
        ax.bar(labels, vals, bottom=bottom, width=0.6, color=BLOC_COLORS[bloc], label=bloc.capitalize())
        bottom += vals
    ax.set_ylabel("Vote Share (%)")
    ax.set_title("Political Composition by Canton (K=5 Louvain, voter-weighted)")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "political_composition_k5.png", dpi=DPI)
    plt.close(fig)


def stability_ari(stability: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.9, 4.8))
    x = np.arange(len(stability))
    ax.bar(x, stability["mean_ari"], yerr=stability["std_ari"], capsize=5, color="#3b82f6", edgecolor="black", linewidth=0.5)
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=0.5, alpha=0.7)
    ax.set_xticks(x, [STABILITY_SHORT.get(c, c) for c in stability["config"]], rotation=30, ha="right")
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Adjusted Rand Index")
    ax.set_title("Cross-Election Stability: Mean ARI by Configuration")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "stability_ari.png", dpi=DPI)
    plt.close(fig)


def main() -> None:
    results = pd.read_csv(DATA_PROCESSED / "experiments" / "experiment_results.csv")
    silhouette_vs_k(results)
    heatmap_silhouette(results)
    labeled = pd.read_csv(DATA_PROCESSED / "cantons_labeled.csv")
    geo = gpd.read_file(DATA_PROCESSED / "municipalities_dissolved.geojson")
    canton_map(labeled, geo)
    per_election_maps(labeled, geo)
    political_composition(pd.read_csv(DATA_PROCESSED / "cantons_final_stats.csv"))
    stability_ari(pd.read_csv(DATA_PROCESSED / "stability_results.csv"))
    print(f"Figures written to {FIG_DIR}")


if __name__ == "__main__":
    main()
