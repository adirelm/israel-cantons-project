"""Compare cantons: differences in bloc vote shares, tested on the 2022 election."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import ELECTION_LABELS, inject_custom_css, load_canton_tests, load_cantons_labeled

st.set_page_config(page_title="Compare Cantons", page_icon=":bar_chart:", layout="wide")
inject_custom_css()
st.title(":bar_chart: Compare Cantons")

tests = load_canton_tests()
if tests is None:
    st.info("Canton comparison tests are not available in this build.")
    st.stop()

_train = [int(k) for k in str(tests["train_elections"].iloc[0]).split(",")]
_test = int(tests["test_election"].iloc[0])
_label = lambda k: ELECTION_LABELS.get(k, f"Knesset {k}")  # noqa: E731
st.markdown(
    f"Cantons are built from the **{_label(_train[0])} – {_label(_train[-1])}** elections only. "
    f"Differences are measured on the **{_label(_test)}** election, which did not shape the map, "
    "so they show that the differences between cantons persist into a new election "
    "(they do not show that these exact boundaries beat other ways of grouping the same towns).\n\n"
    "- **Difference and interval:** the canton's share of all its voters, A minus B, with a 95% "
    "bootstrap interval.\n"
    "- **p-value:** whether the *typical town* in A differs from the typical town in B "
    "(Mann–Whitney, Holm-adjusted across canton pairs). Each town counts once, so when a few "
    "large towns drive the voters' share the two can disagree.\n\n"
    "Neighbouring towns vote alike, so p-values are somewhat optimistic."
)
labels = dict(load_cantons_labeled()[["canton", "label"]].drop_duplicates().values)
ids = sorted(set(tests["canton_a"]) | set(tests["canton_b"]))
names = {c: labels.get(c, f"Canton {c} (no counterpart in the primary map)") for c in ids}
c1, c2, c3 = st.columns(3)
bloc = c1.selectbox("Bloc", sorted(tests["bloc"].unique()), format_func=str.capitalize)
a = c2.selectbox("Canton A", ids, format_func=lambda c: f"{c}: {names[c]}")
b = c3.selectbox("Canton B", [c for c in ids if c != a], format_func=lambda c: f"{c}: {names[c]}")

lo, hi = sorted((a, b))
row = tests[(tests.bloc == bloc) & (tests.canton_a == lo) & (tests.canton_b == hi)].iloc[0]
sign = 1 if a == lo else -1
diff = sign * row["diff"]
ci = sorted((sign * row["ci_low"], sign * row["ci_high"]))
m1, m2, m3 = st.columns(3)
m1.metric(f"Voters' share: {names[a]} − {names[b]}", f"{diff:+.1f} pts")
m2.metric("95% interval", f"{ci[0]:+.1f} to {ci[1]:+.1f}")
m3.metric("Typical-town test (adjusted p)", f"{row['p_holm']:.3g}")
st.caption(f"Across all cantons ({bloc}): Kruskal–Wallis H = {row['kw_h']:.1f}, "
           f"p = {row['kw_p']:.3g}, ε² = {row['kw_eps2']:.2f}.")

table = tests[tests.bloc == bloc].assign(
    canton_a=lambda t: t.canton_a.map(names), canton_b=lambda t: t.canton_b.map(names))
st.dataframe(table[["canton_a", "canton_b", "mean_a", "mean_b", "diff", "ci_low", "ci_high", "p_holm"]].round(3),
             hide_index=True, width="stretch")
