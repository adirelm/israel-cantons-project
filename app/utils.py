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
PER_ELECTION_DIR = DATA_DIR / "per_election"
FIGURES_DIR = PROJECT_ROOT / "docs" / "figures"
PUBLIC_MAP_URL = "https://adirelm.github.io/israel-cantons-project/"
PUBLIC_MAP_LIVE = True  # GitHub Pages serves site/; set False to hide the app's links to it
PAPER_URL = "https://arxiv.org/abs/2603.11805"
CREDITS = (
    "Adir Elmakais, Bar-Ilan University · Advisor: Dr. Oren Glickman · "
    "with Prof. Julia Elad-Strenger, Bundeswehr University Munich"
)
MAP_SIMPLIFY_M = 60.0  # display only: invisible at country zoom, cuts the map page from ~30 MB to ~2 MB
MOVED_COLOR = "#dc2626"  # outline of towns whose canton differs from the primary map (drawn dashed)
OUTSIDE_COLOR = "#cccccc"  # municipalities without votes in every election (not in the analysis)


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

def inject_custom_css() -> None:
    """Inject global custom CSS for a polished, professional look."""
    st.markdown(
        """
        <style>
        /* --- Metric cards --- */
        [data-testid="stMetric"] {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 14px 18px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.82rem;
            color: #64748b;
            font-weight: 500;
        }
        [data-testid="stMetricValue"] {
            font-weight: 700;
        }

        /* --- Section headers accent --- */
        .main h2 {
            border-left: 4px solid #3b82f6;
            padding-left: 14px;
            margin-top: 1.5rem;
        }
        .main h3 {
            border-left: 3px solid #93c5fd;
            padding-left: 12px;
        }

        /* --- Sidebar polish --- */
        [data-testid="stSidebar"] [data-testid="stMetric"] {
            background: transparent;
            border: none;
            box-shadow: none;
            padding: 4px 0;
        }

        /* --- Tabs --- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px 6px 0 0;
            padding: 8px 20px;
        }

        /* --- Info/success/warning boxes --- */
        [data-testid="stAlert"] {
            border-radius: 8px;
        }

        /* --- Container cards --- */
        [data-testid="stVerticalBlock"] > div[data-testid="stExpander"] {
            border-radius: 8px;
        }

        /* --- Footer --- */
        .app-footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            text-align: center;
            padding: 6px 0;
            font-size: 0.72rem;
            color: #94a3b8;
            background: rgba(255,255,255,0.9);
            border-top: 1px solid #f1f5f9;
            z-index: 999;
        }
        </style>
        <div class="app-footer">
            M.Sc. Computer Science Project &middot; Bar-Ilan University &middot; Adir Elmakais
            &middot; with Prof. Julia Elad-Strenger, Bundeswehr University Munich
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Plotly shared layout
# ---------------------------------------------------------------------------

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, system-ui, sans-serif", color="#1e293b"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(gridcolor="#e2e8f0", zerolinecolor="#e2e8f0"),
    yaxis=dict(gridcolor="#e2e8f0", zerolinecolor="#e2e8f0"),
    hoverlabel=dict(bgcolor="white", font_size=13, font_family="Inter, system-ui, sans-serif"),
)

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
    "raw_party_shares": "Vote share of each list that won seats, kept separately for each election (51 features). Uses no grouping of parties into blocs.",
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
    "n_disconnected": "Cantons split on the analysis graph. The graph also links isolated towns and towns where one bloc has over 70%, so 0 does not mean every canton is one piece on the map.",
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
def load_primary_assignment() -> pd.DataFrame:
    """The primary K=5 map with the canton IDs used by cantons_labeled.csv.

    The raw experiment file for the same configuration numbers cantons differently,
    so pages must use this file wherever they show canton names.
    """
    return pd.read_csv(DATA_DIR / "cantons_final.csv")


@st.cache_data
def load_geojson() -> gpd.GeoDataFrame:
    """Municipality boundaries, simplified for display only.

    Coverage simplification keeps most shared borders shared; where the source polygons overlap
    (some Judea and Samaria councils) small gaps can appear. The result is for drawing, not for
    geometry operations (rounding leaves a few invalid shapes).
    """
    import shapely

    geo = gpd.read_file(DATA_DIR / "municipalities_dissolved.geojson").to_crs(2039)
    geo["geometry"] = gpd.GeoSeries(shapely.coverage_simplify(geo.geometry.values, MAP_SIMPLIFY_M), crs=2039)
    geo = geo.to_crs(4326)
    # About 1 m: plenty for display and halves the map page
    geo["geometry"] = shapely.set_precision(geo.geometry.values, 1e-5, mode="pointwise")
    return geo


@st.cache_data
def load_political_features() -> pd.DataFrame:
    """Load political features for all municipalities."""
    return pd.read_csv(DATA_DIR / "political_features.csv")


@st.cache_data
def load_stability_results() -> pd.DataFrame:
    """Load cross-election stability results."""
    return pd.read_csv(DATA_DIR / "stability_results.csv")


@st.cache_data
def load_elections_summary() -> pd.DataFrame:
    """Load the election-level summary table."""
    return pd.read_csv(DATA_DIR / "elections_summary.csv")


@st.cache_data
def load_sa_sensitivity() -> pd.DataFrame:
    """Load SA seed sensitivity results (30 seeds)."""
    return pd.read_csv(DATA_DIR / "sa_seed_sensitivity.csv")


@st.cache_data
def load_cantons_labeled() -> pd.DataFrame:
    """Load canton assignments with human-readable labels."""
    return pd.read_csv(DATA_DIR / "cantons_labeled.csv")


# Copy of src.config.ELECTION_LABELS (the app does not import src); tests/test_app_labels.py keeps them equal
ELECTION_LABELS = {21: "April 2019", 22: "September 2019", 23: "March 2020", 24: "March 2021", 25: "November 2022"}


# Governments formed after each election, whose lists the coalition shares count (the lists are in
# data/reference/parties.csv); no government formed after either 2019 election, and after 2020 lists split
COALITION_GOVERNMENTS = {24: "Bennett–Lapid", 25: "Netanyahu"}


@st.cache_data
def load_canton_coalition() -> pd.DataFrame | None:
    """Each canton's share of the vote for the coalition lists, by election (None if not built)."""
    path = DATA_DIR / "canton_coalition.csv"
    return pd.read_csv(path) if path.exists() else None


@st.cache_data
def load_per_election(knesset: int) -> pd.DataFrame | None:
    """Primary-configuration cantons computed from one election alone (None if not built)."""
    path = PER_ELECTION_DIR / f"knesset_{knesset}.csv"
    return pd.read_csv(path) if path.exists() else None


@st.cache_data
def load_per_election_changes() -> pd.DataFrame | None:
    """Municipalities' canton in each election vs the primary map (None if not built)."""
    path = PER_ELECTION_DIR / "per_election_changes.csv"
    return pd.read_csv(path) if path.exists() else None


@st.cache_data
def load_canton_tests() -> pd.DataFrame | None:
    """Held-out tests of differences between cantons (None if not built)."""
    path = DATA_DIR / "canton_tests.csv"
    return pd.read_csv(path) if path.exists() else None


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

def canton_profiles(assignment: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    """Per canton: bloc shares (%) of all its voters, towns, voters and the largest bloc.

    Towns are weighted by their average number of voters, as in the report's canton table.
    """
    merged = assignment.merge(features, on="municipality", how="left")
    rows = []
    for cid, g in merged.groupby("canton"):
        known = g.dropna(subset=["avg_votes"])
        row = {"canton": int(cid), "n_munis": len(g), "voters": float(known["avg_votes"].sum())}
        for bloc in BLOCS:
            row[bloc] = float((known[f"{bloc}_avg"] * known["avg_votes"]).sum() / known["avg_votes"].sum())
        row["dominant"] = max(BLOCS, key=row.get)
        rows.append(row)
    return pd.DataFrame(rows).set_index("canton")


# Bloc-based color shades — each shade is visually distinct within the family
BLOC_SHADES = {
    "right":  ["#3b82f6", "#1d4ed8", "#93c5fd", "#2563eb"],
    "arab":   ["#22c55e", "#15803d", "#4ade80", "#16a34a"],
    "center": ["#a855f7", "#7c3aed", "#c084fc", "#6d28d9"],
    "left":   ["#ef4444", "#b91c1c", "#f87171", "#dc2626"],
    "haredi": ["#6b7280", "#374151", "#9ca3af", "#4b5563"],
}
MIXED_MARGIN = 5.0  # points between the two largest blocs below which a canton counts as mixed


def _blend(a: str, b: str) -> str:
    rgb = [(int(a[i:i + 2], 16) + int(b[i:i + 2], 16)) // 2 for i in (1, 3, 5)]
    return "#" + "".join(f"{v:02x}" for v in rgb)


def canton_colors(profiles: pd.DataFrame) -> dict[int, str]:
    """A color per canton from its largest bloc's shade family.

    A mixed canton (two largest blocs within MIXED_MARGIN points) gets a blend of both
    families, so it neither reads as one bloc nor looks like its neighbours.
    """
    colors, used = {}, {}
    for cid, p in profiles.iterrows():
        top, second = sorted(BLOCS, key=p.get, reverse=True)[:2]
        key = (top, second) if p[top] - p[second] < MIXED_MARGIN else (top,)
        idx = used.get(key, 0)
        used[key] = idx + 1
        shade = lambda bloc: BLOC_SHADES[bloc][idx % len(BLOC_SHADES[bloc])]  # noqa: E731
        colors[cid] = shade(top) if len(key) == 1 else _blend(shade(top), shade(second))
    return colors


def compare_verdict(diff: float, ci_low: float, ci_high: float, p_holm: float, n_a: int, n_b: int) -> str:
    """Plain-language verdict for a canton pair: voters' share (interval) and typical town (test)."""
    clear_share = ci_low > 0 or ci_high < 0
    clear_town = p_holm < 0.05
    if clear_share and clear_town:
        return "The difference is clear both in voters' terms and for the typical town."
    if clear_share:
        return (f"It is clear in voters' terms; the typical-town test does not confirm it (p = {p_holm:.2f}, "
                f"with {n_a} and {n_b} towns). That can happen when a few large towns drive the share "
                "or when a canton has few towns.")
    if clear_town:
        return "The typical town differs, but the difference in the share of all voters is not clear (the interval includes 0)."
    return "There is no clear difference."


def largest_bloc(profile: pd.Series) -> str:
    """'Right (41%)' — the canton's largest bloc and its share of voters."""
    return f"{profile['dominant'].capitalize()} ({profile[profile['dominant']]:.0f}%)"


def canton_map_layer(
    geo: gpd.GeoDataFrame,
    assignment: pd.DataFrame,
    features: pd.DataFrame,
    names: dict[int, str] | None = None,
    outlined: set[str] | None = None,
) -> gpd.GeoDataFrame:
    """One row per municipality with its canton label, fill color and tooltip fields.

    Municipalities outside the analysis (no votes in every election) stay, drawn grey.
    Towns in ``outlined`` come last so their outline is drawn over their neighbours'.
    """
    profiles = canton_profiles(assignment, features)
    colors = canton_colors(profiles)
    labels = {}
    for cid, profile in profiles.iterrows():
        if names is None:
            labels[cid] = f"Canton {cid} ({profile['dominant'].upper()})"
        else:
            labels[cid] = names.get(cid, f"Canton {cid}: no counterpart in the primary map")

    layer = (
        geo[["MUN_HEB", "MUN_ENG", "geometry"]]
        .merge(assignment, left_on="MUN_HEB", right_on="municipality", how="left")
        .merge(features, on="municipality", how="left")
    )
    layer["canton_label"] = layer["canton"].map(labels).fillna("Not in the analysis (no votes in every election)")
    layer["fill"] = layer["canton"].map(colors).fillna(OUTSIDE_COLOR)
    layer["moved"] = layer["MUN_HEB"].isin(outlined or set())
    layer["votes"] = layer["avg_votes"].map(lambda v: f"{v:,.0f}" if pd.notna(v) else "")
    for bloc in BLOCS:
        layer[bloc] = layer[f"{bloc}_avg"].map(lambda v: f"{v:.1f}%" if pd.notna(v) else "")
    layer = layer.sort_values("moved", kind="stable").reset_index(drop=True)
    layer.attrs["colors"], layer.attrs["labels"] = colors, labels
    return layer


def town_style(props) -> dict:
    """Leaflet style of one municipality: canton fill, dashed red outline if it moved."""
    moved = bool(props["moved"])
    return {
        "fillColor": props["fill"],
        "color": MOVED_COLOR if moved else "#555",
        "weight": 2.4 if moved else 0.6,
        "dashArray": "5 3" if moved else None,
        "fillOpacity": 0.7,
    }


def build_canton_map(
    geo: gpd.GeoDataFrame,
    assignment: pd.DataFrame,
    features: pd.DataFrame,
    names: dict[int, str] | None = None,
    outlined: set[str] | None = None,
) -> "folium.Map":
    """Folium map of municipalities colored by canton, drawn as one GeoJSON layer.

    With ``names`` (the primary map's canton names), the legend and tooltips use them;
    a canton missing from ``names`` has no counterpart in the primary map. Municipalities
    in ``outlined`` get a dashed red outline (towns whose canton differs from the primary map).
    """
    import folium

    # OpenStreetMap needs no API key (CARTO basemaps now show "API key required" watermarks)
    m = folium.Map(location=[31.5, 35.0], zoom_start=8, tiles="OpenStreetMap")

    layer = canton_map_layer(geo, assignment, features, names, outlined)
    colors, canton_labels = layer.attrs["colors"], layer.attrs["labels"]
    fields = ["MUN_HEB", "MUN_ENG", "canton_label", "votes", *BLOCS]
    aliases = ["", "", "Canton", "Valid votes per election (avg.)", *[b.capitalize() for b in BLOCS]]

    folium.GeoJson(
        layer[[*fields, "fill", "moved", "geometry"]].to_json(),
        style_function=lambda f: town_style(f["properties"]),
        highlight_function=lambda f: {"weight": 2.5, "color": "#111", "fillOpacity": 0.85},
        tooltip=folium.GeoJsonTooltip(fields=fields, aliases=aliases, sticky=True),
    ).add_to(m)

    # Add legend using Folium's built-in macro approach for iframe compatibility
    from branca.element import MacroElement, Template

    legend_items = ""
    for cid in sorted(colors.keys()):
        legend_items += (
            f'<li><span style="background:{colors[cid]};width:14px;height:14px;'
            f"display:inline-block;margin-right:6px;border-radius:3px;"
            f'border:1px solid #999"></span>'
            f" {canton_labels.get(cid, '')}</li>"
        )
    if outlined:
        legend_items += (
            f'<li><span style="width:12px;height:12px;display:inline-block;margin-right:6px;'
            f'border:2px dashed {MOVED_COLOR}"></span> Different canton from the primary map</li>'
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
