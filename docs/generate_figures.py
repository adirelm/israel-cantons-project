"""Generate static figures for the final report."""

import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import geopandas as gpd
import seaborn as sns
import json

FIGURES_DIR = ROOT / "docs" / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

DATA_DIR = ROOT / "data" / "processed"

# ── Colour palettes ──
CANTON_COLORS = [
    "#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
    "#ffff33", "#a65628", "#f781bf", "#999999", "#66c2a5",
]
BLOC_COLORS = {
    "right": "#3b82f6", "haredi": "#6b7280", "center": "#a855f7",
    "left": "#ef4444", "arab": "#22c55e",
}
BLOCS = ["right", "haredi", "center", "left", "arab"]


# ────────────────────────────────────────────────────────────────
# Figure 1: K=5 Canton Map
# ────────────────────────────────────────────────────────────────
print("Generating Figure 1: Canton map...")

geo = gpd.read_file(DATA_DIR / "municipalities_dissolved.geojson")

# Primary result: NMF_5 with cosine Louvain
primary_path = DATA_DIR / "experiments" / "nmf_5__cosine__louvain__k5.csv"
if primary_path.exists():
    asgn_df = pd.read_csv(primary_path)
else:
    print("  No K=5 assignment found, skipping map")
    asgn_df = None

if asgn_df is not None:
    asgn_map = dict(zip(asgn_df["municipality"], asgn_df["canton"]))
    geo_c = geo.copy()
    geo_c["canton"] = geo_c["MUN_HEB"].map(asgn_map)
    geo_c = geo_c.dropna(subset=["canton"])
    geo_c["canton"] = geo_c["canton"].astype(int)

    fig, ax = plt.subplots(figsize=(10, 14))

    canton_labels = {
        0: "Canton 0: CENTER Metro",
        1: "Canton 1: RIGHT South",
        2: "Canton 2: RIGHT North",
        3: "Canton 3: ARAB Galilee",
        4: "Canton 4: ARAB Periphery",
    }

    patches = []
    for cid in sorted(geo_c["canton"].unique()):
        color = CANTON_COLORS[int(cid) % len(CANTON_COLORS)]
        canton_geo = geo_c[geo_c["canton"] == cid]
        canton_geo.plot(ax=ax, color=color, edgecolor="black", linewidth=0.3)
        label = canton_labels.get(cid, f"Canton {cid}")
        patches.append(mpatches.Patch(color=color, label=label))

    ax.legend(handles=patches, loc="lower right", fontsize=9, title="Cantons",
              title_fontsize=10, framealpha=0.9)
    ax.set_title("K=5 Canton Partition (NMF_5 / Cosine / Louvain)", fontsize=13)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "canton_map_k5.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  Saved canton_map_k5.png")


# ────────────────────────────────────────────────────────────────
# Figure 2: Silhouette vs K (by algorithm)
# ────────────────────────────────────────────────────────────────
print("Generating Figure 2: Silhouette vs K...")

results = pd.read_csv(DATA_DIR / "experiments" / "experiment_results.csv")

# Filter to BlocShares + Euclidean for a clean plot
bloc_euc = results[(results["repr"] == "bloc_shares") & (results["metric"] == "euclidean")]

fig, ax = plt.subplots(figsize=(9, 5))
algo_labels = {
    "simulated_annealing": "Simulated Annealing",
    "agglomerative_average": "Agglomerative",
    "louvain": "Louvain",
    "kmeans_baseline": "K-Means (baseline)",
}
algo_colors = {
    "simulated_annealing": "#e41a1c",
    "agglomerative_average": "#377eb8",
    "louvain": "#4daf4a",
    "kmeans_baseline": "#984ea3",
}

for algo in ["simulated_annealing", "agglomerative_average", "kmeans_baseline", "louvain"]:
    subset = bloc_euc[bloc_euc["algo"] == algo].sort_values("k_target")
    if len(subset) > 0:
        ax.plot(subset["k_target"], subset["silhouette"], marker="o", linewidth=2,
                label=algo_labels.get(algo, algo), color=algo_colors.get(algo, "gray"))

ax.set_xlabel("K (Number of Cantons)", fontsize=11)
ax.set_ylabel("Silhouette Score", fontsize=11)
ax.set_title("Silhouette Score vs K (BlocShares / Euclidean)", fontsize=12)
ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.5, alpha=0.5)
ax.legend(fontsize=9)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIGURES_DIR / "silhouette_vs_k.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("  Saved silhouette_vs_k.png")


# ────────────────────────────────────────────────────────────────
# Figure 3: Political Composition stacked bar (K=5)
# ────────────────────────────────────────────────────────────────
print("Generating Figure 3: Political composition...")

features = pd.read_csv(DATA_DIR / "political_features.csv")

if asgn_df is not None:
    merged = asgn_df.merge(features, on="municipality", how="left")
    canton_ids = sorted(merged["canton"].unique())

    fig, ax = plt.subplots(figsize=(9, 5))
    x_pos = np.arange(len(canton_ids))
    bottom = np.zeros(len(canton_ids))

    canton_labels_short = []
    for i, cid in enumerate(canton_ids):
        cdata = merged[merged["canton"] == cid]
        bloc_avgs = {}
        for bloc in BLOCS:
            col = f"{bloc}_avg"
            val = cdata[col].mean() if col in cdata.columns else 0
            bloc_avgs[bloc] = val
        dominant = max(bloc_avgs, key=bloc_avgs.get)
        canton_labels_short.append(f"Canton {cid}\n({dominant.upper()})")

    for bloc in BLOCS:
        vals = []
        for cid in canton_ids:
            cdata = merged[merged["canton"] == cid]
            col = f"{bloc}_avg"
            vals.append(cdata[col].mean() if col in cdata.columns else 0)
        ax.bar(x_pos, vals, bottom=bottom, label=bloc.capitalize(),
               color=BLOC_COLORS[bloc], alpha=0.85, width=0.6)
        bottom += np.array(vals)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(canton_labels_short, fontsize=9)
    ax.set_ylabel("Vote Share (%)", fontsize=11)
    ax.set_title("Political Composition by Canton (K=5 Louvain)", fontsize=12)
    ax.set_ylim(0, 105)
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "political_composition_k5.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  Saved political_composition_k5.png")


# ────────────────────────────────────────────────────────────────
# Figure 4: Heatmap – best silhouette by repr x algo
# ────────────────────────────────────────────────────────────────
print("Generating Figure 4: Heatmap...")

repr_labels = {
    "bloc_shares": "BlocShares", "raw_party_shares": "RawParty",
    "pca_5": "PCA_5", "nmf_5": "NMF_5",
}
algo_labels_map = {
    "simulated_annealing": "SA", "agglomerative_average": "Agglom.",
    "louvain": "Louvain", "kmeans_baseline": "K-Means",
}

results["Repr"] = results["repr"].map(repr_labels)
results["Algo"] = results["algo"].map(algo_labels_map)

pivot = results.groupby(["Repr", "Algo"])["silhouette"].max().reset_index()
pivot_table = pivot.pivot(index="Repr", columns="Algo", values="silhouette")

fig, ax = plt.subplots(figsize=(8, 5))
sns.heatmap(pivot_table, annot=True, fmt=".3f", cmap="RdYlGn", vmin=-1, vmax=1,
            ax=ax, linewidths=0.5)
ax.set_title("Best Silhouette Score by Representation × Algorithm", fontsize=12)
ax.set_ylabel("")
ax.set_xlabel("")
fig.tight_layout()
fig.savefig(FIGURES_DIR / "heatmap_silhouette.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("  Saved heatmap_silhouette.png")


# ────────────────────────────────────────────────────────────────
# Figure 5: Stability bar chart (ARI)
# ────────────────────────────────────────────────────────────────
print("Generating Figure 5: Stability ARI...")

stability_path = DATA_DIR / "stability_results.csv"
if stability_path.exists():
    stability = pd.read_csv(stability_path)

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(stability["config"], stability["mean_ari"],
                  yerr=stability["std_ari"], capsize=4,
                  color="#3b82f6", edgecolor="black", linewidth=0.5)
    ax.set_ylabel("Adjusted Rand Index", fontsize=11)
    ax.set_title("Cross-Election Stability: Mean ARI by Configuration", fontsize=12)
    ax.set_ylim(0, 1.15)
    ax.axhline(y=1.0, color="gray", linestyle="--", linewidth=0.5, alpha=0.5)
    plt.xticks(rotation=25, ha="right", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "stability_ari.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  Saved stability_ari.png")
else:
    print("  stability_results.csv not found, skipping")


# ────────────────────────────────────────────────────────────────
# Figure 6: Methodology pipeline diagram (text-based)
# ────────────────────────────────────────────────────────────────
print("Generating Figure 6: Pipeline diagram...")

fig, ax = plt.subplots(figsize=(12, 3.5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 2)
ax.set_axis_off()

boxes = [
    (0.3, 0.8, "Election\nData (CBS)"),
    (2.0, 0.8, "Feature\nExtraction"),
    (3.7, 0.8, "Distance\nMatrix"),
    (5.4, 0.8, "Graph\nConstruction"),
    (7.1, 0.8, "Constrained\nClustering"),
    (8.8, 0.8, "Evaluation\n& Analysis"),
]

for x, y, text in boxes:
    bbox = dict(boxstyle="round,pad=0.4", facecolor="#e0e7ff", edgecolor="#3b82f6", linewidth=1.5)
    ax.text(x, y, text, ha="center", va="center", fontsize=9, fontweight="bold", bbox=bbox)

# Arrows
for i in range(len(boxes) - 1):
    x1 = boxes[i][0] + 0.65
    x2 = boxes[i + 1][0] - 0.65
    ax.annotate("", xy=(x2, 0.8), xytext=(x1, 0.8),
                arrowprops=dict(arrowstyle="->", lw=1.5, color="#3b82f6"))

# Sub-labels
sub_labels = [
    (0.3, 0.2, "5 Knesset\nelections"),
    (2.0, 0.2, "BlocShares\nRawParty\nPCA / NMF"),
    (3.7, 0.2, "Euclidean\nCosine\nJensen-Shannon"),
    (5.4, 0.2, "Adjacency\n+ augmentation"),
    (7.1, 0.2, "SA / Agglom.\nLouvain / KMeans"),
    (8.8, 0.2, "Silhouette\nWCSS / CV"),
]
for x, y, text in sub_labels:
    ax.text(x, y, text, ha="center", va="center", fontsize=7, color="#4b5563", style="italic")

ax.set_title("Methodology Pipeline", fontsize=13, fontweight="bold", pad=15)
fig.tight_layout()
fig.savefig(FIGURES_DIR / "pipeline.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("  Saved pipeline.png")


print("\nAll figures generated!")
