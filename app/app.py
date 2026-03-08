"""Israel Cantons Project -- Interactive Explorer.

Main page: project overview and key results.
"""

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from streamlit_folium import st_folium

from utils import (
    load_experiment_results,
    load_geojson,
    load_canton_assignment,
    load_political_features,
    load_cantons_labeled,
    inject_custom_css,
    BLOC_COLORS,
    BLOCS,
    PLOTLY_LAYOUT,
    FIGURES_DIR,
    build_canton_map,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Israel Cantons Explorer",
    page_icon=":world_map:",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_custom_css()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title(":world_map: Israel Cantons Explorer")
st.markdown(
    "**Dividing Israel into politically homogeneous cantons based on Knesset election results**"
)
st.markdown(
    "_M.Sc. Computer Science Project -- Adir Elmakais, Bar-Ilan University "
    "(Advisor: Dr. Oren Glickman)_"
)

st.divider()

# ---------------------------------------------------------------------------
# Key metrics
# ---------------------------------------------------------------------------

results = load_experiment_results()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Municipalities", "229", help="Consistently matched across all 5 elections")
col2.metric("Experiments", f"{len(results)}", help="4 representations x 3 metrics x 4 algorithms x 6 K values (minus incompatible)")
col3.metric("Algorithms", "4", help="Simulated Annealing, Agglomerative, Louvain, KMeans")
col4.metric("Elections Analyzed", "5", help="Knesset 21-25 (April 2019 -- November 2022)")

st.divider()

# ---------------------------------------------------------------------------
# Primary result: K=5 map
# ---------------------------------------------------------------------------

st.subheader("Featured Result: K=5 Canton Partition")
st.markdown(
    "The map below shows the K=5 partition using "
    "**NMF_5 / Cosine / Louvain**, which produces five politically coherent "
    "cantons with a positive silhouette (0.121) and perfect cross-election stability (ARI = 1.0). "
    "Explore all 264 configurations in the **Canton Map Explorer** page."
)

geo = load_geojson()
features = load_political_features()

# Load human-readable canton labels
canton_label_df = load_cantons_labeled()
_canton_label_map = (
    canton_label_df.drop_duplicates("canton")
    .set_index("canton")["label"]
    .to_dict()
)

# Load best balanced k=5 assignment
assignment = load_canton_assignment("nmf_5", "cosine", "louvain", 5)

if assignment is not None:
    merged = assignment.merge(features, on="municipality", how="left")

    # Compute canton profiles for coloring
    canton_profiles = {}
    for cid in sorted(merged["canton"].unique()):
        cdata = merged[merged["canton"] == cid]
        bloc_avgs = {b: cdata[f"{b}_avg"].mean() for b in BLOCS}
        dominant = max(bloc_avgs, key=bloc_avgs.get)
        canton_profiles[cid] = {
            "dominant": dominant,
            "blocs": bloc_avgs,
            "n_munis": len(cdata),
            "voters": cdata["avg_votes"].sum(),
            "label": _canton_label_map.get(cid, f"Canton {cid}"),
        }

    map_col, profile_col = st.columns([3, 2])

    with map_col:
        with st.spinner("Rendering map..."):
            m = build_canton_map(geo, assignment, features)
            st_folium(m, width=700, height=550, returned_objects=[])

    with profile_col:
        st.markdown("#### Canton Political Profiles")

        # Stacked bar chart
        canton_ids = sorted(canton_profiles.keys())
        bloc_data = {bloc: [] for bloc in BLOCS}
        labels = []

        for cid in canton_ids:
            p = canton_profiles[cid]
            labels.append(p["label"])
            for bloc in BLOCS:
                bloc_data[bloc].append(p["blocs"][bloc])

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
            height=320,
            margin=dict(l=40, r=20, t=10, b=60),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, width="stretch")

        # Summary table
        pop_data = []
        for cid in canton_ids:
            p = canton_profiles[cid]
            pop_data.append({
                "Canton": p["label"],
                "Dominant Bloc": p["dominant"].capitalize(),
                "Municipalities": p["n_munis"],
                "Avg Voters": f"{p['voters']:,.0f}",
            })

        st.dataframe(pd.DataFrame(pop_data), width="stretch", hide_index=True)

    st.info(
        "**Why multiple RIGHT cantons?** Cantons are *geographically contiguous* regions, "
        "not political blocs. The right bloc dominates most municipalities across the country, "
        "but these municipalities are spread across different geographic areas that cannot form "
        "a single contiguous canton. Each RIGHT canton has a distinct political mix -- "
        "see the stacked bar chart above."
    )

else:
    st.warning("Featured K=5 assignment not found. Run notebook 06 first.")

# ---------------------------------------------------------------------------
# Pipeline figure
# ---------------------------------------------------------------------------

pipeline_path = FIGURES_DIR / "pipeline.png"
if pipeline_path.exists():
    st.divider()
    st.image(str(pipeline_path), caption="Methodology Pipeline -- from raw data to cantons", width=700)

st.divider()

# ---------------------------------------------------------------------------
# Quick links
# ---------------------------------------------------------------------------

st.subheader("Explore the Project")

link_col1, link_col2, link_col3 = st.columns(3)

with link_col1:
    with st.container(border=True):
        st.markdown(
            ":world_map: **Canton Map Explorer**\n\n"
            "Interactively explore all 264 experiment configurations. "
            "Select K, algorithm, representation, and distance metric."
        )
        st.page_link("pages/1_Canton_Map.py", label="Open Map Explorer", icon=":material/map:")

with link_col2:
    with st.container(border=True):
        st.markdown(
            ":bar_chart: **Experiment Results**\n\n"
            "Compare silhouette scores, WCSS, and population balance "
            "across all configurations with interactive charts."
        )
        st.page_link("pages/2_Experiments.py", label="Open Experiments", icon=":material/bar_chart:")

with link_col3:
    with st.container(border=True):
        st.markdown(
            ":chart_with_upwards_trend: **Stability Analysis**\n\n"
            "See how canton boundaries persist across five Knesset elections "
            "(2019-2022)."
        )
        st.page_link("pages/3_Stability.py", label="Open Stability", icon=":material/trending_up:")

st.caption("Use the sidebar to navigate between pages.")
