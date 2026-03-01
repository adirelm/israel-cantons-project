"""Shared data loading utilities for the Streamlit app.

All loaders use @st.cache_data for performance.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
EXPERIMENTS_DIR = DATA_DIR / "experiments"

# ---------------------------------------------------------------------------
# Color palettes
# ---------------------------------------------------------------------------

BLOC_COLORS = {
    "right": "#3b82f6",
    "haredi": "#6b7280",
    "center": "#a855f7",
    "left": "#ef4444",
    "arab": "#22c55e",
}

# ---------------------------------------------------------------------------
# Human-readable labels
# ---------------------------------------------------------------------------

REPR_LABELS = {
    "bloc_shares": "BlocShares",
    "raw_party_shares": "RawParty",
    "pca_5": "PCA (5)",
    "nmf_5": "NMF (5)",
}

METRIC_LABELS = {
    "euclidean": "Euclidean",
    "cosine": "Cosine",
    "jensen_shannon": "Jensen-Shannon",
}

ALGO_LABELS = {
    "simulated_annealing": "Simulated Annealing",
    "agglomerative_average": "Agglomerative",
    "louvain": "Louvain",
    "kmeans_baseline": "KMeans (baseline)",
}

K_VALUES = [3, 5, 7, 10, 15, 20]

BLOCS = ["right", "haredi", "center", "left", "arab"]

# ---------------------------------------------------------------------------
# Descriptions (used for help= tooltips)
# ---------------------------------------------------------------------------

REPR_DESCRIPTIONS = {
    "bloc_shares": "11 features: average + std of 5 political blocs across elections, plus avg voter turnout. Most interpretable representation.",
    "raw_party_shares": "Vote share for each individual party. High-dimensional but captures fine-grained differences between municipalities.",
    "pca_5": "PCA dimensionality reduction to 5 components from raw party shares. Captures the main axes of political variance.",
    "nmf_5": "Non-negative Matrix Factorization to 5 components. Similar to PCA but preserves non-negativity of vote shares.",
}

METRIC_DESCRIPTIONS = {
    "euclidean": "Straight-line distance in feature space. Treats all dimensions equally.",
    "cosine": "Measures angle between feature vectors. Focuses on proportion patterns, ignores magnitude.",
    "jensen_shannon": "Information-theoretic divergence for probability distributions. Natural choice for vote share data.",
}

ALGO_DESCRIPTIONS = {
    "simulated_annealing": "Stochastic optimization that swaps municipalities between cantons to minimize within-cluster distance while enforcing geographic contiguity.",
    "agglomerative_average": "Bottom-up hierarchical clustering that merges the most similar adjacent municipalities. May produce unbalanced partitions.",
    "louvain": "Graph community detection on the adjacency graph weighted by political similarity. Optimizes modularity.",
    "kmeans_baseline": "Standard K-Means without contiguity constraints. Baseline for comparison -- cantons may be geographically disconnected.",
}

EVAL_METRIC_DESCRIPTIONS = {
    "silhouette": "How well-separated cantons are (-1 to 1). Higher = more distinct. Negative means municipalities are closer to other cantons than their own.",
    "wcss": "Within-Cluster Sum of Squares. Lower = more politically homogeneous cantons.",
    "pop_cv": "Coefficient of variation of canton populations. Lower = more balanced sizes (0 = perfectly equal).",
    "n_disconnected": "Municipalities not connected to their canton's main territory. 0 = fully contiguous.",
    "elapsed_s": "Algorithm runtime in seconds.",
}


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

@st.cache_data
def load_experiment_results() -> pd.DataFrame:
    """Load the master experiment results table."""
    return pd.read_csv(EXPERIMENTS_DIR / "experiment_results.csv")


@st.cache_data
def load_canton_assignment(repr_name: str, metric: str, algo: str, k: int) -> pd.DataFrame | None:
    """Load a specific experiment's canton assignments."""
    filename = f"{repr_name}__{metric}__{algo}__k{k}.csv"
    path = EXPERIMENTS_DIR / filename
    if not path.exists():
        return None
    return pd.read_csv(path)


@st.cache_data
def load_geojson() -> gpd.GeoDataFrame:
    """Load municipality boundaries GeoJSON."""
    return gpd.read_file(DATA_DIR / "municipalities_dissolved.geojson")


@st.cache_data
def load_political_features() -> pd.DataFrame:
    """Load political features for all municipalities."""
    return pd.read_csv(DATA_DIR / "political_features.csv")


@st.cache_data
def load_stability_results() -> pd.DataFrame:
    """Load cross-election stability results."""
    return pd.read_csv(DATA_DIR / "stability_results.csv")


def config_label(repr_name: str, metric: str, algo: str, k: int) -> str:
    """Human-readable label for a configuration."""
    return (
        f"{REPR_LABELS.get(repr_name, repr_name)} / "
        f"{METRIC_LABELS.get(metric, metric)} / "
        f"{ALGO_LABELS.get(algo, algo)} / K={k}"
    )


# ---------------------------------------------------------------------------
# Map builder
# ---------------------------------------------------------------------------

def build_canton_map(
    geo: gpd.GeoDataFrame,
    assignment: pd.DataFrame,
    features: pd.DataFrame,
) -> "folium.Map":
    """Build a Folium map with dissolved canton polygons and municipality outlines."""
    import folium

    m = folium.Map(location=[31.5, 35.0], zoom_start=8, tiles="cartodbpositron")

    # Merge assignment into geo
    geo_merged = geo.merge(assignment, left_on="MUN_HEB", right_on="municipality", how="left")
    geo_merged["canton"] = geo_merged["canton"].fillna(-1).astype(int)

    # Merge political features
    feat_merged = geo_merged.merge(features, on="municipality", how="left")

    # Compute canton profiles for coloring
    merged_data = assignment.merge(features, on="municipality", how="left")
    canton_colors = {}
    canton_labels = {}

    # Bloc-based color shades — each shade is visually distinct within the family
    _BLOC_SHADES = {
        "right":  ["#3b82f6", "#1d4ed8", "#93c5fd", "#2563eb"],
        "arab":   ["#22c55e", "#15803d", "#4ade80", "#16a34a"],
        "center": ["#a855f7", "#7c3aed", "#c084fc", "#6d28d9"],
        "left":   ["#ef4444", "#b91c1c", "#f87171", "#dc2626"],
        "haredi": ["#6b7280", "#374151", "#9ca3af", "#4b5563"],
    }

    # Assign colors per canton from its dominant bloc's shade family
    bloc_usage_count = {}
    for cid in sorted(merged_data["canton"].unique()):
        cdata = merged_data[merged_data["canton"] == cid]
        bloc_avgs = {b: cdata[f"{b}_avg"].mean() for b in BLOCS}
        dominant = max(bloc_avgs, key=bloc_avgs.get)
        canton_labels[cid] = dominant.upper()

        idx = bloc_usage_count.get(dominant, 0)
        shades = _BLOC_SHADES[dominant]
        canton_colors[cid] = shades[idx % len(shades)]
        bloc_usage_count[dominant] = idx + 1

    # Draw each municipality individually (for tooltips) but color by canton
    for _, row in feat_merged.iterrows():
        canton = int(row["canton"]) if row["canton"] >= 0 else -1
        color = canton_colors.get(canton, "#cccccc")

        heb_name = row.get("MUN_HEB", "")
        eng_name = row.get("MUN_ENG", "")
        dominant = row.get("dominant_bloc", "N/A")
        voters = row.get("avg_votes", 0)
        label = canton_labels.get(canton, "N/A")

        tooltip_parts = [
            f"<b>{heb_name}</b> ({eng_name})" if eng_name else f"<b>{heb_name}</b>",
            f"<b>Canton {canton}</b> ({label})",
            f"Dominant: {dominant}",
            f"Avg voters: {voters:,.0f}" if pd.notna(voters) else "",
        ]
        # Add bloc breakdown
        for bloc in BLOCS:
            col = f"{bloc}_avg"
            if col in row.index and pd.notna(row[col]):
                tooltip_parts.append(f"{bloc.capitalize()}: {row[col]:.1f}%")

        tooltip_text = "<br>".join(p for p in tooltip_parts if p)

        if row.geometry is not None:
            folium.GeoJson(
                row.geometry.__geo_interface__,
                style_function=lambda x, c=color: {
                    "fillColor": c,
                    "color": "#555",
                    "weight": 0.8,
                    "fillOpacity": 0.7,
                },
                tooltip=folium.Tooltip(tooltip_text),
            ).add_to(m)

    # Add legend using Folium's built-in macro approach for iframe compatibility
    from branca.element import MacroElement, Template

    legend_items = ""
    for cid in sorted(canton_colors.keys()):
        color = canton_colors[cid]
        label = canton_labels.get(cid, "")
        legend_items += (
            f'<li><span style="background:{color};width:14px;height:14px;'
            f"display:inline-block;margin-right:6px;border-radius:3px;"
            f'border:1px solid #999"></span>'
            f" Canton {cid} ({label})</li>"
        )

    legend_macro = MacroElement()
    legend_macro._template = Template(
        """
        {%% macro html(this, kwargs) %%}
        <div style="position:fixed;bottom:30px;left:30px;z-index:9999;
            background:white;padding:12px 16px;border-radius:8px;
            border:1px solid #ccc;font-size:13px;color:#333;
            box-shadow:0 2px 6px rgba(0,0,0,0.15)">
            <b style="color:#333">Cantons</b>
            <ul style="list-style:none;margin:4px 0 0 0;padding:0">
            %s
            </ul>
        </div>
        {%% endmacro %%}
        """
        % legend_items
    )
    m.get_root().add_child(legend_macro)

    return m
