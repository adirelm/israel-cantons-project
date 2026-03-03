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
    load_cantons_labeled,
    build_canton_map,
    inject_custom_css,
    REPR_LABELS,
    METRIC_LABELS,
    ALGO_LABELS,
    REPR_DESCRIPTIONS,
    METRIC_DESCRIPTIONS,
    ALGO_DESCRIPTIONS,
    EVAL_METRIC_DESCRIPTIONS,
    BLOC_COLORS,
    BLOCS,
    PLOTLY_LAYOUT,
    config_label,
)

st.set_page_config(page_title="Canton Map Explorer", page_icon=":world_map:", layout="wide")
inject_custom_css()

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

# Load canton labels for the featured config
_is_featured = (sel_repr == "nmf_5" and sel_metric == "cosine"
                and sel_algo == "louvain" and sel_k == 5)
canton_label_map = {}
if _is_featured:
    _lbl_df = load_cantons_labeled()
    canton_label_map = _lbl_df.drop_duplicates("canton").set_index("canton")["label"].to_dict()

# ---------------------------------------------------------------------------
# Map
# ---------------------------------------------------------------------------

map_col, info_col = st.columns([3, 2])

with map_col:
    st.subheader(config_label(sel_repr, sel_metric, sel_algo, sel_k))
    with st.spinner("Rendering canton map..."):
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
        if _is_featured and cid in canton_label_map:
            labels.append(canton_label_map[cid])
        else:
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
        **PLOTLY_LAYOUT,
        barmode="stack",
        yaxis_title="Vote Share (%)",
        yaxis_range=[0, 105],
        xaxis_title="",
        height=350,
        margin=dict(l=40, r=20, t=30, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.05),
    )
    st.plotly_chart(fig, width="stretch")

    # Population distribution
    pop_data = []
    for cid in canton_ids:
        cdata = merged[merged["canton"] == cid]
        lbl = canton_label_map.get(cid, f"Canton {cid}") if _is_featured else f"Canton {cid}"
        pop_data.append({
            "Canton": lbl,
            "Municipalities": len(cdata),
            "Total Voters": f"{cdata['avg_votes'].sum():,.0f}" if "avg_votes" in cdata.columns else "0",
            "Dominant Bloc": cdata["dominant_bloc"].mode().iloc[0].capitalize() if len(cdata) > 0 else "N/A",
        })

    pop_df = pd.DataFrame(pop_data)
    st.dataframe(pop_df, width="stretch", hide_index=True)

# ---------------------------------------------------------------------------
# Comparison mode
# ---------------------------------------------------------------------------

st.divider()

with st.expander("Compare with another configuration", expanded=False):
    st.markdown("Select a second configuration to compare against the current one.")

    cmp_col1, cmp_col2, cmp_col3, cmp_col4 = st.columns(4)

    with cmp_col1:
        cmp_repr = st.selectbox(
            "Representation (B)",
            reprs,
            format_func=lambda x: REPR_LABELS.get(x, x),
            index=reprs.index("bloc_shares") if "bloc_shares" in reprs else 0,
            key="cmp_repr",
        )
    # Filter compatible options for comparison
    cmp_compat = results[results["repr"] == cmp_repr]
    cmp_avail_metrics = sorted(cmp_compat["metric"].unique())

    with cmp_col2:
        cmp_metric = st.selectbox(
            "Metric (B)",
            cmp_avail_metrics,
            format_func=lambda x: METRIC_LABELS.get(x, x),
            key="cmp_metric",
        )

    cmp_compat2 = cmp_compat[cmp_compat["metric"] == cmp_metric]
    cmp_avail_algos = sorted(cmp_compat2["algo"].unique())

    with cmp_col3:
        cmp_algo = st.selectbox(
            "Algorithm (B)",
            cmp_avail_algos,
            format_func=lambda x: ALGO_LABELS.get(x, x),
            key="cmp_algo",
        )

    cmp_compat3 = cmp_compat2[cmp_compat2["algo"] == cmp_algo]
    cmp_avail_k = sorted(cmp_compat3["k_target"].unique().astype(int))

    with cmp_col4:
        cmp_k = st.selectbox(
            "K (B)",
            cmp_avail_k,
            index=cmp_avail_k.index(5) if 5 in cmp_avail_k else 0,
            key="cmp_k",
        )

    # Load comparison data
    cmp_assignment = load_canton_assignment(cmp_repr, cmp_metric, cmp_algo, cmp_k)
    cmp_row = results[
        (results["repr"] == cmp_repr)
        & (results["metric"] == cmp_metric)
        & (results["algo"] == cmp_algo)
        & (results["k_target"] == cmp_k)
    ]

    if cmp_assignment is not None and len(cmp_row) > 0 and len(row) > 0:
        ra = row.iloc[0]
        rb = cmp_row.iloc[0]

        st.markdown(
            f"**A:** {config_label(sel_repr, sel_metric, sel_algo, sel_k)} &nbsp;&nbsp;vs&nbsp;&nbsp; "
            f"**B:** {config_label(cmp_repr, cmp_metric, cmp_algo, cmp_k)}"
        )

        # Metrics comparison
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Silhouette", f"{rb['silhouette']:.3f}",
                   delta=f"{rb['silhouette'] - ra['silhouette']:+.3f}")
        m2.metric("Pop. CV", f"{rb['pop_cv']:.3f}",
                   delta=f"{rb['pop_cv'] - ra['pop_cv']:+.3f}", delta_color="inverse")
        m3.metric("WCSS", f"{rb['wcss']:.0f}",
                   delta=f"{rb['wcss'] - ra['wcss']:+.0f}", delta_color="inverse")
        m4.metric("Disconnected", f"{int(rb['n_disconnected'])}",
                   delta=f"{int(rb['n_disconnected']) - int(ra['n_disconnected']):+d}", delta_color="inverse")

        # Municipality movement
        cmp_merged = assignment[["municipality", "canton"]].merge(
            cmp_assignment[["municipality", "canton"]],
            on="municipality",
            suffixes=("_a", "_b"),
        )
        n_changed = int((cmp_merged["canton_a"] != cmp_merged["canton_b"]).sum())
        st.metric("Municipalities that changed canton", f"{n_changed} / {len(cmp_merged)}")

        # Side-by-side bar charts
        bar_a, bar_b = st.columns(2)

        cmp_merged_feat = cmp_assignment.merge(features, on="municipality", how="left")
        cmp_canton_ids = sorted(cmp_merged_feat["canton"].unique())

        with bar_a:
            st.caption(f"**Config A** -- {ALGO_LABELS.get(sel_algo, sel_algo)}")
            # Reuse the fig from above
            st.plotly_chart(fig, width="stretch", key="comparison_a")

        with bar_b:
            st.caption(f"**Config B** -- {ALGO_LABELS.get(cmp_algo, cmp_algo)}")
            cmp_bloc_data = {bloc: [] for bloc in BLOCS}
            cmp_labels = []
            for cid in cmp_canton_ids:
                cdata = cmp_merged_feat[cmp_merged_feat["canton"] == cid]
                bloc_avgs_b = {}
                for bloc in BLOCS:
                    col_name = f"{bloc}_avg"
                    val = cdata[col_name].mean() if col_name in cdata.columns else 0
                    cmp_bloc_data[bloc].append(val)
                    bloc_avgs_b[bloc] = val
                dominant_b = max(bloc_avgs_b, key=bloc_avgs_b.get)
                cmp_labels.append(f"Canton {cid}\n({dominant_b.upper()})")

            fig_b = go.Figure()
            for bloc in BLOCS:
                fig_b.add_trace(go.Bar(
                    name=bloc.capitalize(),
                    x=cmp_labels,
                    y=cmp_bloc_data[bloc],
                    marker_color=BLOC_COLORS[bloc],
                    showlegend=False,
                ))
            fig_b.update_layout(
                **PLOTLY_LAYOUT,
                barmode="stack",
                yaxis_title="Vote Share (%)",
                yaxis_range=[0, 105],
                height=300,
                margin=dict(l=40, r=20, t=10, b=60),
            )
            st.plotly_chart(fig_b, width="stretch", key="comparison_b")
    else:
        st.warning("Comparison assignment not found.")
