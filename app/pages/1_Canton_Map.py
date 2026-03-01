"""Canton Map Explorer -- interactive map with parameter controls."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import (
    load_experiment_results,
    load_geojson,
    load_canton_assignment,
    load_political_features,
    build_canton_map,
    REPR_LABELS,
    METRIC_LABELS,
    ALGO_LABELS,
    REPR_DESCRIPTIONS,
    METRIC_DESCRIPTIONS,
    ALGO_DESCRIPTIONS,
    EVAL_METRIC_DESCRIPTIONS,
    BLOC_COLORS,
    BLOCS,
    config_label,
)

st.set_page_config(page_title="Canton Map Explorer", page_icon=":world_map:", layout="wide")

st.title(":world_map: Canton Map Explorer")
st.markdown("Select parameters to explore different canton partitions interactively.")

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------

results = load_experiment_results()

# Get unique values from actual results
reprs = sorted(results["repr"].unique())
metrics = sorted(results["metric"].unique())
algos = sorted(results["algo"].unique())

with st.sidebar:
    st.header("Configuration")

    sel_repr = st.selectbox(
        "Representation",
        reprs,
        format_func=lambda x: REPR_LABELS.get(x, x),
        index=reprs.index("nmf_5") if "nmf_5" in reprs else 0,
    )
    st.caption(REPR_DESCRIPTIONS.get(sel_repr, ""))

    # Filter metrics compatible with selected representation
    compatible = results[results["repr"] == sel_repr]
    avail_metrics = sorted(compatible["metric"].unique())

    sel_metric = st.selectbox(
        "Distance Metric",
        avail_metrics,
        format_func=lambda x: METRIC_LABELS.get(x, x),
    )
    st.caption(METRIC_DESCRIPTIONS.get(sel_metric, ""))

    # Filter algorithms
    compatible2 = compatible[compatible["metric"] == sel_metric]
    avail_algos = sorted(compatible2["algo"].unique())

    default_algo_idx = avail_algos.index("louvain") if "louvain" in avail_algos else 0
    sel_algo = st.selectbox(
        "Algorithm",
        avail_algos,
        index=default_algo_idx,
        format_func=lambda x: ALGO_LABELS.get(x, x),
    )
    st.caption(ALGO_DESCRIPTIONS.get(sel_algo, ""))

    # Filter K values
    compatible3 = compatible2[compatible2["algo"] == sel_algo]
    avail_k = sorted(compatible3["k_target"].unique().astype(int))

    sel_k = st.select_slider(
        "Number of Cantons (K)",
        options=avail_k,
        value=5 if 5 in avail_k else avail_k[0],
        help="How many cantons to divide Israel into.",
    )

    st.divider()

    # Show current config metrics
    row = results[
        (results["repr"] == sel_repr)
        & (results["metric"] == sel_metric)
        & (results["algo"] == sel_algo)
        & (results["k_target"] == sel_k)
    ]
    if len(row) > 0:
        r = row.iloc[0]
        st.markdown("#### Metrics")
        st.metric("Silhouette", f"{r['silhouette']:.3f}", help=EVAL_METRIC_DESCRIPTIONS["silhouette"])
        st.metric("WCSS", f"{r['wcss']:.0f}", help=EVAL_METRIC_DESCRIPTIONS["wcss"])
        st.metric("Pop. Balance (CV)", f"{r['pop_cv']:.3f}", help=EVAL_METRIC_DESCRIPTIONS["pop_cv"])
        st.metric("Disconnected", f"{int(r['n_disconnected'])}", help=EVAL_METRIC_DESCRIPTIONS["n_disconnected"])
        st.metric("Runtime", f"{r['elapsed_s']:.1f}s", help=EVAL_METRIC_DESCRIPTIONS["elapsed_s"])

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

assignment = load_canton_assignment(sel_repr, sel_metric, sel_algo, sel_k)

if assignment is None:
    st.error(
        f"No assignment file found for: "
        f"{config_label(sel_repr, sel_metric, sel_algo, sel_k)}"
    )
    st.stop()

geo = load_geojson()
features = load_political_features()

# ---------------------------------------------------------------------------
# Map
# ---------------------------------------------------------------------------

map_col, info_col = st.columns([3, 2])

with map_col:
    st.subheader(config_label(sel_repr, sel_metric, sel_algo, sel_k))
    m = build_canton_map(geo, assignment, features)
    st_folium(m, width=700, height=550, returned_objects=[])

# ---------------------------------------------------------------------------
# Canton profiles
# ---------------------------------------------------------------------------

with info_col:
    st.subheader("Canton Profiles")

    merged = assignment.merge(features, on="municipality", how="left")

    # Political composition stacked bar
    canton_ids = sorted(merged["canton"].unique())
    bloc_data = {bloc: [] for bloc in BLOCS}
    labels = []

    for cid in canton_ids:
        cdata = merged[merged["canton"] == cid]
        bloc_avgs = {}
        for bloc in BLOCS:
            col_name = f"{bloc}_avg"
            val = cdata[col_name].mean() if col_name in cdata.columns else 0
            bloc_data[bloc].append(val)
            bloc_avgs[bloc] = val
        dominant = max(bloc_avgs, key=bloc_avgs.get)
        labels.append(f"Canton {cid}\n({dominant.upper()})")

    fig = go.Figure()
    for bloc in BLOCS:
        fig.add_trace(go.Bar(
            name=bloc.capitalize(),
            x=labels,
            y=bloc_data[bloc],
            marker_color=BLOC_COLORS[bloc],
        ))

    fig.update_layout(
        barmode="stack",
        yaxis_title="Vote Share (%)",
        yaxis_range=[0, 105],
        xaxis_title="",
        height=350,
        margin=dict(l=40, r=20, t=30, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.05),
    )
    st.plotly_chart(fig, width="stretch")

    # Population distribution
    pop_data = []
    for cid in canton_ids:
        cdata = merged[merged["canton"] == cid]
        pop_data.append({
            "Canton": f"Canton {cid}",
            "Municipalities": len(cdata),
            "Total Voters": f"{cdata['avg_votes'].sum():,.0f}" if "avg_votes" in cdata.columns else "0",
            "Dominant Bloc": cdata["dominant_bloc"].mode().iloc[0].capitalize() if len(cdata) > 0 else "N/A",
        })

    pop_df = pd.DataFrame(pop_data)
    st.dataframe(pop_df, width="stretch", hide_index=True)
