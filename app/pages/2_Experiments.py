"""Experiment Results -- heatmaps, elbow plots, and comparison tables."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import (
    load_experiment_results,
    REPR_LABELS,
    METRIC_LABELS,
    ALGO_LABELS,
    EVAL_METRIC_DESCRIPTIONS,
)

st.set_page_config(page_title="Experiment Results", page_icon=":bar_chart:", layout="wide")

st.title(":bar_chart: Experiment Results")
st.markdown("Explore results across all 264 experiment configurations.")

results = load_experiment_results()

# Add human-readable labels
results["Representation"] = results["repr"].map(REPR_LABELS)
results["Metric"] = results["metric"].map(METRIC_LABELS)
results["Algorithm"] = results["algo"].map(ALGO_LABELS)

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Filters")

    sel_reprs = st.multiselect(
        "Representations",
        options=sorted(results["Representation"].unique()),
        default=sorted(results["Representation"].unique()),
    )

    sel_metrics = st.multiselect(
        "Distance Metrics",
        options=sorted(results["Metric"].unique()),
        default=sorted(results["Metric"].unique()),
    )

    sel_algos = st.multiselect(
        "Algorithms",
        options=sorted(results["Algorithm"].unique()),
        default=sorted(results["Algorithm"].unique()),
    )

    _METRIC_VIZ_LABELS = {
        "silhouette": "Silhouette Score",
        "wcss": "WCSS",
        "pop_cv": "Population Balance (CV)",
        "avg_dominant_margin": "Dominant Bloc Margin",
    }
    sel_metric_y = st.selectbox(
        "Metric to visualize",
        ["silhouette", "wcss", "pop_cv", "avg_dominant_margin"],
        format_func=lambda x: _METRIC_VIZ_LABELS.get(x, x),
    )
    _metric_help = EVAL_METRIC_DESCRIPTIONS.get(sel_metric_y, "")
    if sel_metric_y == "avg_dominant_margin":
        _metric_help = "Average margin between the dominant bloc and second-largest bloc within each canton. Higher = more politically distinct cantons."
    st.caption(_metric_help)

filtered = results[
    (results["Representation"].isin(sel_reprs))
    & (results["Metric"].isin(sel_metrics))
    & (results["Algorithm"].isin(sel_algos))
]

# ---------------------------------------------------------------------------
# Heatmap: best score per representation x algorithm
# ---------------------------------------------------------------------------

st.subheader("Best Scores by Representation x Algorithm")

# Pivot: best metric per repr x algo (across all K and metrics)
if sel_metric_y == "wcss" or sel_metric_y == "pop_cv":
    pivot = filtered.groupby(["Representation", "Algorithm"])[sel_metric_y].min().reset_index()
    better = "lower"
else:
    pivot = filtered.groupby(["Representation", "Algorithm"])[sel_metric_y].max().reset_index()
    better = "higher"

pivot_table = pivot.pivot(index="Representation", columns="Algorithm", values=sel_metric_y)

def _fmt_heatmap_val(v):
    """Format heatmap cell values readably."""
    if pd.isna(v):
        return ""
    if abs(v) >= 1e9:
        return f"{v / 1e9:.1f}B"
    if abs(v) >= 1e6:
        return f"{v / 1e6:.1f}M"
    if abs(v) >= 1e4:
        return f"{v / 1e3:.1f}K"
    return f"{v:.3f}"

# Build custom text labels
_text_labels = [[_fmt_heatmap_val(v) for v in row] for row in pivot_table.values]

fig_heat = px.imshow(
    pivot_table.values,
    x=pivot_table.columns.tolist(),
    y=pivot_table.index.tolist(),
    color_continuous_scale="RdYlGn" if better == "higher" else "RdYlGn_r",
    aspect="auto",
)
fig_heat.update_traces(text=_text_labels, texttemplate="%{text}")
_metric_display = _METRIC_VIZ_LABELS.get(sel_metric_y, sel_metric_y)
fig_heat.update_layout(
    title=f"Best {_metric_display} ({better} is better)",
    height=350,
    margin=dict(l=40, r=20, t=50, b=30),
)
st.plotly_chart(fig_heat, width="stretch")

# ---------------------------------------------------------------------------
# Line plot: metric vs K
# ---------------------------------------------------------------------------

st.subheader(f"{_metric_display} vs K")

col1, col2 = st.columns(2)

with col1:
    # Group by algo
    fig_line = px.line(
        filtered,
        x="k_target",
        y=sel_metric_y,
        color="Algorithm",
        line_dash="Representation",
        markers=True,
        labels={"k_target": "K", sel_metric_y: sel_metric_y.replace("_", " ").title()},
    )
    fig_line.update_layout(height=400, margin=dict(l=40, r=20, t=30, b=30))
    st.plotly_chart(fig_line, width="stretch")

with col2:
    # Group by representation
    fig_line2 = px.line(
        filtered,
        x="k_target",
        y=sel_metric_y,
        color="Representation",
        line_dash="Algorithm",
        markers=True,
        labels={"k_target": "K", sel_metric_y: sel_metric_y.replace("_", " ").title()},
    )
    fig_line2.update_layout(height=400, margin=dict(l=40, r=20, t=30, b=30))
    st.plotly_chart(fig_line2, width="stretch")

# ---------------------------------------------------------------------------
# Top configurations table
# ---------------------------------------------------------------------------

st.subheader("Top 20 Configurations")

display_cols = [
    "Representation", "Metric", "Algorithm", "k_target", "k_actual",
    "silhouette", "wcss", "pop_cv", "avg_dominant_margin",
    "n_disconnected", "elapsed_s",
]

if sel_metric_y in ("wcss", "pop_cv"):
    top = filtered.nsmallest(20, sel_metric_y)
else:
    top = filtered.nlargest(20, sel_metric_y)

st.dataframe(
    top[display_cols].reset_index(drop=True),
    width="stretch",
    hide_index=True,
    column_config={
        "k_target": st.column_config.NumberColumn("K (target)"),
        "k_actual": st.column_config.NumberColumn("K (actual)"),
        "silhouette": st.column_config.NumberColumn("Silhouette", format="%.3f"),
        "wcss": st.column_config.NumberColumn("WCSS", format="%.0f"),
        "pop_cv": st.column_config.NumberColumn("Pop. CV", format="%.3f"),
        "avg_dominant_margin": st.column_config.NumberColumn("Dom. Margin", format="%.1f"),
        "n_disconnected": st.column_config.NumberColumn("Disconnected"),
        "elapsed_s": st.column_config.NumberColumn("Time (s)", format="%.1f"),
    },
)

# ---------------------------------------------------------------------------
# Summary stats
# ---------------------------------------------------------------------------

st.subheader("Summary Statistics")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.metric("Total Configurations", len(filtered))
    st.metric("Zero Disconnected", len(filtered[filtered["n_disconnected"] == 0]))

with col_b:
    st.metric("Best Silhouette", f"{filtered['silhouette'].max():.3f}")
    st.metric("Median Silhouette", f"{filtered['silhouette'].median():.3f}")

with col_c:
    st.metric("Best Pop. CV", f"{filtered['pop_cv'].min():.3f}")
    st.metric("Median Pop. CV", f"{filtered['pop_cv'].median():.3f}")
