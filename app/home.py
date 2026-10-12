"""Israel Cantons Project -- Interactive Explorer.

Main page: project overview and key results.
"""

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from streamlit_folium import st_folium

from utils import (
    load_stability_results,
    load_primary_assignment,
    load_experiment_results,
    load_geojson,
    load_political_features,
    load_cantons_labeled,
    inject_custom_css,
    BLOC_COLORS,
    BLOCS,
    PLOTLY_LAYOUT,
    FIGURES_DIR,
    PUBLIC_MAP_URL,
    build_canton_map,
    canton_profiles,
    largest_bloc,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

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
st.info(
    f"**Looking for the map for readers?** The [public map]({PUBLIC_MAP_URL}) shows the five cantons in "
    "Hebrew and English, with town search and a view per election. This app holds the research behind it.",
    icon=":material/public:",
)

st.divider()

# ---------------------------------------------------------------------------
# Key metrics
# ---------------------------------------------------------------------------

results = load_experiment_results()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Municipalities", "255", help="With votes in all 5 elections, including 23 Israeli local authorities in Judea and Samaria")
col2.metric("Experiments", f"{len(results)}", help="4 representations x 3 metrics x 4 algorithms x 6 K values (minus incompatible)")
col3.metric("Algorithms", "4", help="Simulated Annealing, Agglomerative, Louvain, KMeans")
col4.metric("Elections Analyzed", "5", help="Knesset 21-25 (April 2019 -- November 2022)")

st.divider()

# ---------------------------------------------------------------------------
# Primary result: K=5 map
# ---------------------------------------------------------------------------

st.subheader("Featured Result: K=5 Canton Partition")
_ex = load_experiment_results()
_primary = _ex[(_ex["repr"] == "nmf_5") & (_ex["metric"] == "cosine") & (_ex["algo"] == "louvain") & (_ex["k_target"] == 5)]
_ari = load_stability_results().set_index("config").loc["NMF_5 / Cosine / Louvain", "mean_ari"]
st.markdown(
    "The map below shows the K=5 partition using "
    "**NMF_5 / Cosine / Louvain**, which produces five politically coherent "
    f"cantons with a positive silhouette ({_primary['silhouette'].iloc[0]:.3f}) and stable boundaries "
    f"across the five elections (mean ARI = {_ari:.3f}). "
    f"Explore all {len(_ex)} configurations in the **Canton Map Explorer** page."
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

# Primary K=5 map, numbered like cantons_labeled.csv
assignment = load_primary_assignment()

if assignment is not None:
    # Bloc shares of each canton's voters (weighted by town size, as in the report)
    profiles = canton_profiles(assignment, features)
    profiles["label"] = [_canton_label_map.get(cid, f"Canton {cid}") for cid in profiles.index]

    with st.spinner("Rendering map..."):
        m = build_canton_map(geo, assignment, features, names=_canton_label_map)
        st_folium(m, use_container_width=True, height=560, returned_objects=[])

    st.markdown("#### Canton Political Profiles")
    chart_col, table_col = st.columns([3, 2])

    with chart_col:
        # Stacked bar chart, one row per canton so the names fit
        fig = go.Figure()
        for bloc in BLOCS:
            fig.add_trace(go.Bar(
                name=bloc.capitalize(),
                y=profiles["label"],
                x=profiles[bloc],
                orientation="h",
                marker_color=BLOC_COLORS[bloc],
                hovertemplate="%{y}: %{x:.1f}%<extra>" + bloc.capitalize() + "</extra>",
            ))

        fig.update_layout(
            **PLOTLY_LAYOUT,
            barmode="stack",
            xaxis_title="Share of the canton's votes (%)",
            xaxis_range=[0, 100],
            height=300,
            margin=dict(l=10, r=10, t=10, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        fig.update_yaxes(autorange="reversed", automargin=True)
        st.plotly_chart(fig, width="stretch")

    with table_col:
        pop_data = [{
            "Canton": p["label"],
            "Largest Bloc": largest_bloc(p),
            "Municipalities": p["n_munis"],
            "Avg Voters": f"{p['voters']:,.0f}",
        } for _, p in profiles.iterrows()]
        st.dataframe(pd.DataFrame(pop_data), width="stretch", hide_index=True)

    st.info(
        "**Why several right-leaning cantons?** Cantons are built from neighbouring municipalities, "
        "not from political blocs. The right bloc leads in most municipalities, but they lie in regions "
        "with different political mixes -- see the stacked bar chart above. "
        "Not every canton is one piece on the map: towns where a single bloc has over 70% of the vote "
        "are also linked to each other, so **ARAB** joins Arab towns from the Galilee to the Negev and "
        "**HAREDI Cities** joins seven cities that share no borders."
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

st.caption("Use the sidebar to move between pages: Explore for the map and comparisons, Research for the method and its checks.")
