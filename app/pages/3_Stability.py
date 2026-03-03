"""Stability Analysis -- cross-election ARI/NMI and SA seed sensitivity."""

import statistics

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import (
    load_stability_results,
    load_sa_sensitivity,
    inject_custom_css,
    PLOTLY_LAYOUT,
)

st.set_page_config(page_title="Stability Analysis", page_icon=":chart_with_upwards_trend:", layout="wide")
inject_custom_css()

st.title(":chart_with_upwards_trend: Cross-Election Stability Analysis")
st.markdown(
    "How stable are canton boundaries when computed independently from each "
    "of the five Knesset elections (2019-2022)? Higher ARI/NMI indicates "
    "that the same partition emerges regardless of which election is used."
)

stability = load_stability_results()

# ---------------------------------------------------------------------------
# Bar chart: mean ARI by configuration
# ---------------------------------------------------------------------------

st.subheader("Mean ARI by Configuration")
st.caption("**ARI (Adjusted Rand Index):** Measures agreement between two partitions, adjusted for chance. Ranges from -1 to 1; 1 = identical partitions, 0 = random agreement.")

fig_ari = go.Figure()
fig_ari.add_trace(go.Bar(
    x=stability["config"],
    y=stability["mean_ari"],
    error_y=dict(type="data", array=stability["std_ari"], visible=True),
    marker_color="#3b82f6",
    name="ARI",
))
fig_ari.update_layout(
    **PLOTLY_LAYOUT,
    yaxis_title="Adjusted Rand Index",
    yaxis_range=[0, 1.1],
    height=400,
    margin=dict(l=40, r=20, t=30, b=80),
    xaxis_tickangle=-30,
)
st.plotly_chart(fig_ari, width="stretch")

# ---------------------------------------------------------------------------
# Bar chart: mean NMI by configuration
# ---------------------------------------------------------------------------

st.subheader("Mean NMI by Configuration")
st.caption("**NMI (Normalized Mutual Information):** Information-theoretic measure of partition similarity. Ranges from 0 to 1; 1 = identical partitions.")

fig_nmi = go.Figure()
fig_nmi.add_trace(go.Bar(
    x=stability["config"],
    y=stability["mean_nmi"],
    error_y=dict(type="data", array=stability["std_nmi"], visible=True),
    marker_color="#22c55e",
    name="NMI",
))
fig_nmi.update_layout(
    **PLOTLY_LAYOUT,
    yaxis_title="Normalized Mutual Information",
    yaxis_range=[0, 1.1],
    height=400,
    margin=dict(l=40, r=20, t=30, b=80),
    xaxis_tickangle=-30,
)
st.plotly_chart(fig_nmi, width="stretch")

# ---------------------------------------------------------------------------
# Comparison table
# ---------------------------------------------------------------------------

st.subheader("Stability Comparison Table")

st.dataframe(
    stability,
    width="stretch",
    hide_index=True,
    column_config={
        "config": st.column_config.TextColumn("Configuration"),
        "mean_ari": st.column_config.NumberColumn("Mean ARI", format="%.4f"),
        "std_ari": st.column_config.NumberColumn("Std ARI", format="%.4f"),
        "mean_nmi": st.column_config.NumberColumn("Mean NMI", format="%.4f"),
        "std_nmi": st.column_config.NumberColumn("Std NMI", format="%.4f"),
    },
)

# ---------------------------------------------------------------------------
# Key findings
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Key Findings")

col1, col2 = st.columns(2)

with col1:
    best_ari = stability.loc[stability["mean_ari"].idxmax()]
    st.success(
        f"**Most Stable (ARI):** {best_ari['config']}\n\n"
        f"Mean ARI = {best_ari['mean_ari']:.4f} "
        f"(+/- {best_ari['std_ari']:.4f})"
    )

with col2:
    best_nmi = stability.loc[stability["mean_nmi"].idxmax()]
    st.success(
        f"**Most Stable (NMI):** {best_nmi['config']}\n\n"
        f"Mean NMI = {best_nmi['mean_nmi']:.4f} "
        f"(+/- {best_nmi['std_nmi']:.4f})"
    )

st.info(
    "**Interpretation:** Deterministic algorithms (Louvain, Agglomerative) "
    "produce near-perfectly stable partitions across elections, while "
    "stochastic methods (Simulated Annealing) show more variation. "
    "Note: Louvain's perfect ARI (1.0) reflects the algorithm's determinism on "
    "a fixed adjacency graph -- the same graph structure yields identical communities "
    "regardless of which election's features are used. "
    "Overall, this confirms that Israel's political geography is structurally "
    "persistent despite electoral volatility."
)

# ---------------------------------------------------------------------------
# SA Seed Sensitivity
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Simulated Annealing Seed Sensitivity")
st.markdown(
    "SA is stochastic -- different random seeds produce different partitions. "
    "Below: **30 independent runs** of SA with NMF_5 / Cosine / K=5, "
    "each with a different random seed."
)

sa = load_sa_sensitivity()

chart_col, stats_col = st.columns([3, 2])

with chart_col:
    # Box plots for silhouette and pop_cv
    fig_box = go.Figure()
    fig_box.add_trace(go.Box(
        y=sa["silhouette"],
        name="Silhouette",
        boxpoints="all",
        jitter=0.4,
        pointpos=-1.5,
        marker_color="#3b82f6",
        line_color="#3b82f6",
    ))
    fig_box.add_trace(go.Box(
        y=sa["pop_cv"],
        name="Pop. CV",
        boxpoints="all",
        jitter=0.4,
        pointpos=-1.5,
        marker_color="#f59e0b",
        line_color="#f59e0b",
    ))
    fig_box.update_layout(
        **PLOTLY_LAYOUT,
        title="Distribution across 30 seeds",
        height=400,
        showlegend=False,
        margin=dict(l=40, r=20, t=50, b=30),
    )
    st.plotly_chart(fig_box, width="stretch")

with stats_col:
    st.markdown("#### Summary Statistics")

    sils = sa["silhouette"].tolist()
    cvs = sa["pop_cv"].tolist()
    n = len(sils)
    import math
    se_sil = statistics.stdev(sils) / math.sqrt(n)
    se_cv = statistics.stdev(cvs) / math.sqrt(n)
    mean_sil = statistics.mean(sils)
    mean_cv = statistics.mean(cvs)

    stats_data = {
        "Statistic": ["Mean", "Std Dev", "Min", "Max", "95% CI"],
        "Silhouette": [
            f"{mean_sil:.3f}",
            f"{statistics.stdev(sils):.3f}",
            f"{min(sils):.3f}",
            f"{max(sils):.3f}",
            f"[{mean_sil - 1.96*se_sil:.3f}, {mean_sil + 1.96*se_sil:.3f}]",
        ],
        "Pop. CV": [
            f"{mean_cv:.2f}",
            f"{statistics.stdev(cvs):.2f}",
            f"{min(cvs):.2f}",
            f"{max(cvs):.2f}",
            f"[{mean_cv - 1.96*se_cv:.2f}, {mean_cv + 1.96*se_cv:.2f}]",
        ],
    }
    st.dataframe(pd.DataFrame(stats_data), width="stretch", hide_index=True)

    st.info(
        "**Key takeaway:** SA's silhouette ranges from "
        f"{min(sils):.3f} to {max(sils):.3f} across seeds -- "
        "showing substantial variability. Deterministic algorithms "
        "(Louvain, Agglomerative) always produce the same result."
    )
