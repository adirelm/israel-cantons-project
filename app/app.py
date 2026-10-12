"""Israel Cantons research app: page navigation. Streamlit Cloud runs this file."""

import streamlit as st

from utils import PUBLIC_MAP_URL

st.set_page_config(
    page_title="Israel Cantons Explorer",
    page_icon=":world_map:",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = {
    "Explore": [
        st.Page("home.py", title="Home", icon=":material/home:", default=True),
        st.Page("pages/1_Canton_Map.py", title="Canton Map", icon=":material/map:"),
        st.Page("pages/5_Compare_Cantons.py", title="Compare Cantons", icon=":material/compare_arrows:"),
    ],
    "Research": [
        st.Page("pages/3_Stability.py", title="Stability", icon=":material/timeline:"),
        st.Page("pages/2_Experiments.py", title="Experiments", icon=":material/bar_chart:"),
        st.Page("pages/4_About.py", title="About", icon=":material/info:"),
    ],
}
page = st.navigation(pages)
st.sidebar.link_button("Public map (Hebrew / English)", PUBLIC_MAP_URL, icon=":material/public:", width="stretch")
page.run()
