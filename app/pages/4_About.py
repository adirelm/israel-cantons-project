"""About -- project methodology and information, organized in tabs."""

import plotly.graph_objects as go
import streamlit as st

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import (
    inject_custom_css,
    load_elections_summary,
    FIGURES_DIR,
    PLOTLY_LAYOUT,
)

st.set_page_config(page_title="About", page_icon=":information_source:", layout="wide")
inject_custom_css()

st.title(":information_source: About This Project")

st.markdown(
    "**Partitioning Israeli Municipalities into Politically Homogeneous Cantons**\n\n"
    "Author: **Adir Elmakais** · Advisor: **Dr. Oren Glickman** · "
    "M.Sc. Computer Science (Project Track), Bar-Ilan University · 2025-2026"
)

st.divider()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_method, tab_results, tab_data, tab_tech = st.tabs([
    "Methodology", "Key Results", "Data Sources", "Technology",
])

# ===== METHODOLOGY TAB =====================================================
with tab_method:
    st.subheader("Motivation")
    st.markdown(
        "Over the past four years, Israel held five Knesset elections "
        "(April 2019, September 2019, March 2020, March 2021, and November 2022). "
        "Public discourse repeatedly invoked the notion of dividing Israel into "
        'separate "cantons" along political lines.\n\n'
        "This project applies data-driven computational methods to answer: "
        "**if Israel were divided into politically coherent regions based purely "
        "on voting patterns, what would those regions look like?**"
    )

    # Pipeline figure
    pipeline_path = FIGURES_DIR / "pipeline.png"
    if pipeline_path.exists():
        st.image(str(pipeline_path), caption="Methodology Pipeline", width="stretch")

    with st.expander("Feature Representations", expanded=True):
        st.markdown("""
| Representation | Dimensions | Description |
|---|---|---|
| **BlocShares** | 11 | Average + std of 5 political blocs across elections |
| **RawParty** | ~79 | Raw party vote percentages |
| **PCA (5)** | 5 | Principal component analysis on raw party shares |
| **NMF (5)** | 5 | Non-negative matrix factorization on raw party shares |
""")

    with st.expander("Distance Metrics"):
        st.markdown("""
- **Euclidean** -- Standard L2 distance in feature space
- **Cosine** -- Angular distance (1 - cosine similarity), focuses on proportion patterns
- **Jensen-Shannon** -- Information-theoretic divergence for probability distributions

*Note: PCA (5) is incompatible with Jensen-Shannon because PCA produces negative values
and JSD requires non-negative inputs. This excludes 24 configurations (288 - 24 = 264).*
""")

    with st.expander("Clustering Algorithms"):
        st.markdown("""
| Algorithm | Type | Contiguity |
|---|---|---|
| **Simulated Annealing** | Metaheuristic | Enforced (swap-based) |
| **Agglomerative** | Hierarchical | Enforced (merge-based) |
| **Louvain** | Community detection | Inherent (graph-based) |
| **KMeans (baseline)** | Centroid-based | None (baseline) |
""")

    with st.expander("Evaluation Metrics"):
        st.markdown("""
- **Silhouette score** -- Cluster separation quality (-1 to 1, higher is better)
- **WCSS** -- Within-cluster sum of squares (lower = more homogeneous)
- **Population balance** -- Coefficient of variation of canton populations
- **Contiguity** -- Number of disconnected cantons (0 = fully contiguous)
- **Temporal stability** -- ARI/NMI across independent per-election clusterings
""")

# ===== KEY RESULTS TAB =====================================================
with tab_results:
    st.subheader("Experiment Overview")

    r1, r2, r3 = st.columns(3)
    r1.metric("Total Configurations", "264")
    r2.metric("Highest Silhouette", "0.905", help="BlocShares / Euclidean / Agglomerative, K=3")
    r3.metric("Best Stability (ARI)", "1.000", help="Louvain -- deterministic on fixed graph")

    st.divider()

    # Figures
    fig_cols = st.columns(2)

    heatmap_path = FIGURES_DIR / "heatmap_silhouette.png"
    sil_vs_k_path = FIGURES_DIR / "silhouette_vs_k.png"

    with fig_cols[0]:
        if heatmap_path.exists():
            st.image(str(heatmap_path), caption="Silhouette Heatmap by Representation x Algorithm", width="stretch")

    with fig_cols[1]:
        if sil_vs_k_path.exists():
            st.image(str(sil_vs_k_path), caption="Silhouette Score vs K", width="stretch")

    comp_path = FIGURES_DIR / "political_composition_k5.png"
    if comp_path.exists():
        st.image(str(comp_path), caption="Political Composition by Canton (K=5)", width="stretch")

    st.divider()
    st.subheader("K=5 Canton Descriptions")

    st.markdown("""
1. **CENTER Metro** -- Secular-center belt from Tel Aviv through the Sharon plain (42.0% Center)
2. **RIGHT South** -- Southern periphery arc from Jerusalem through the Negev (44.9% Right)
3. **RIGHT North** -- Mixed northern region including Haifa and the Galilee (38.0% Right)
4. **ARAB Galilee** -- Arab-majority municipalities in the Galilee and Triangle (89.9% Arab)
5. **ARAB Periphery** -- Bedouin towns in the Negev and central Arab towns (86.1% Arab)
""")

    canton_map_path = FIGURES_DIR / "canton_map_k5.png"
    if canton_map_path.exists():
        st.image(str(canton_map_path), caption="K=5 Canton Map", width="stretch")

# ===== DATA SOURCES TAB ====================================================
with tab_data:
    st.subheader("Election Data")
    st.markdown(
        "Municipality-level results from **Knesset elections 21-25** "
        "(Israel Central Bureau of Statistics). "
        "**229 municipalities** consistently matchable across all 5 elections."
    )

    elections = load_elections_summary()

    st.dataframe(
        elections,
        width="stretch",
        hide_index=True,
        column_config={
            "knesset": st.column_config.NumberColumn("Knesset"),
            "n_municipalities": st.column_config.NumberColumn("Municipalities"),
            "n_common": st.column_config.NumberColumn("Common"),
            "total_eligible": st.column_config.NumberColumn("Eligible Voters", format="%d"),
            "total_voters": st.column_config.NumberColumn("Actual Voters", format="%d"),
            "avg_turnout": st.column_config.NumberColumn("Avg Turnout (%)", format="%.1f"),
        },
    )

    # Turnout bar chart
    fig_turnout = go.Figure()
    fig_turnout.add_trace(go.Bar(
        x=[f"Knesset {k}" for k in elections["knesset"]],
        y=elections["avg_turnout"],
        marker_color="#3b82f6",
        text=[f"{t:.1f}%" for t in elections["avg_turnout"]],
        textposition="outside",
    ))
    fig_turnout.update_layout(
        **PLOTLY_LAYOUT,
        title="Average Turnout by Election",
        yaxis_title="Turnout (%)",
        yaxis_range=[0, 80],
        height=350,
        margin=dict(l=40, r=20, t=50, b=30),
    )
    st.plotly_chart(fig_turnout, width="stretch")

    st.divider()
    st.subheader("Geographic Data")
    st.markdown(
        "Municipal boundary polygons from **CBS GIS repository**. "
        "Adjacency graph: 234 raw nodes, 516 edges (queen contiguity). "
        "After subsetting to 229 analysis municipalities and 3-step augmentation: 229 nodes, 2,178 edges."
    )

# ===== TECHNOLOGY TAB =======================================================
with tab_tech:
    st.subheader("Technology Stack")

    t1, t2 = st.columns(2)

    with t1:
        st.markdown("""
**Analysis & Algorithms:**
- Python 3.12+
- pandas, NumPy, SciPy
- scikit-learn (KMeans, silhouette, ARI/NMI)
- NetworkX (graph operations, Louvain)
- GeoPandas (spatial data)
""")

    with t2:
        st.markdown("""
**Visualization & Web:**
- Matplotlib (static figures)
- Plotly (interactive charts)
- Folium / Leaflet.js (interactive maps)
- Streamlit (web application)
- Streamlit Cloud (deployment)
""")

    st.divider()
    st.subheader("References")
    st.markdown(
        "- Brieden, A. et al. (2017). *Constrained clustering problems*. "
        "[arXiv:1703.02867](https://arxiv.org/abs/1703.02867)"
    )
