"""Compare cantons: differences in bloc vote shares, tested on the 2022 election."""

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import (
    ELECTION_LABELS, PLOTLY_LAYOUT, compare_verdict, inject_custom_css, load_canton_tests, load_cantons_labeled,
)

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
    f"Do the cantons really differ? The cantons were built from the **{_label(_train[0])} – "
    f"{_label(_train[-1])}** elections only, and are compared here on the **{_label(_test)}** election, "
    "which played no part in drawing them."
)
labels = dict(load_cantons_labeled()[["canton", "label"]].drop_duplicates().values)
ids = sorted(set(tests["canton_a"]) | set(tests["canton_b"]))
names = {c: labels.get(c, f"Canton {c} (no counterpart in the primary map)") for c in ids}
c1, c2, c3 = st.columns(3)
bloc = c1.selectbox("Bloc", sorted(tests["bloc"].unique()), format_func=str.capitalize)
a = c2.selectbox("Canton A", ids, format_func=lambda c: names[c])
b = c3.selectbox("Canton B", [c for c in ids if c != a], format_func=lambda c: names[c])

lo, hi = sorted((a, b))
row = tests[(tests.bloc == bloc) & (tests.canton_a == lo) & (tests.canton_b == hi)].iloc[0]
sign = 1 if a == lo else -1
diff = sign * row["diff"]
ci = sorted((sign * row["ci_low"], sign * row["ci_high"]))
share_a, share_b = (row["mean_a"], row["mean_b"]) if sign == 1 else (row["mean_b"], row["mean_a"])
verdict = compare_verdict(diff, ci[0], ci[1], row["p_holm"], int(row["n_a"] if sign == 1 else row["n_b"]),
                          int(row["n_b"] if sign == 1 else row["n_a"]))
gap = round(share_a, 1) - round(share_b, 1)  # stated from the rounded shares so the sentence adds up


def _bound(x: float) -> str:
    return f"{x:+.2f}" if abs(x) < 0.05 else f"{x:+.1f}"


st.markdown(
    f"#### {names[a]} vs {names[b]}\n"
    f"In {_label(_test)}, the **{bloc.capitalize()}** bloc got **{share_a:.1f}%** of the vote in **{names[a]}** "
    f"and **{share_b:.1f}%** in **{names[b]}**: "
    f"{f'{abs(gap):.1f} points ' + ('more' if gap > 0 else 'less') if abs(gap) >= 0.05 else 'about the same share'} "
    f"(95% interval for A minus B: {_bound(ci[0])} to {_bound(ci[1])} points). "
    f"{verdict}"
)

pairs = tests[tests.bloc == bloc].copy()
# Show the selected pair as A minus B, the same direction as the sentence above
flip = (pairs.canton_a == lo) & (pairs.canton_b == hi) & (sign == -1)
pairs.loc[flip, ["canton_a", "canton_b"]] = pairs.loc[flip, ["canton_b", "canton_a"]].to_numpy()
pairs.loc[flip, ["diff", "ci_low", "ci_high"]] = -pairs.loc[flip, ["diff", "ci_high", "ci_low"]].to_numpy()
pairs["pair"] = pairs.canton_a.map(names) + "  vs  " + pairs.canton_b.map(names)
pairs["clear"] = ((pairs.ci_low > 0) | (pairs.ci_high < 0)) & (pairs.p_holm < 0.05)
pairs = pairs.sort_values("diff")
selected = pairs.canton_a.isin([lo, hi]) & pairs.canton_b.isin([lo, hi])
fig = go.Figure(go.Scatter(
    x=pairs["diff"], y=pairs["pair"], mode="markers",
    marker=dict(size=selected.map({True: 16, False: 11}),
                symbol=selected.map({True: "diamond", False: "circle"}),
                color=pairs["clear"].map({True: "#0f172a", False: "#94a3b8"}),
                line=dict(width=selected.map({True: 2, False: 0}), color="#2563eb")),
    error_x=dict(type="data", symmetric=False, array=pairs.ci_high - pairs["diff"],
                 arrayminus=pairs["diff"] - pairs.ci_low, color="#64748b", thickness=1.5),
    hovertemplate="%{y}<br>%{x:+.1f} points<extra></extra>",
))
fig.add_vline(x=0, line_width=1, line_color="#ef4444")
fig.update_layout(
    **PLOTLY_LAYOUT, height=90 + 38 * len(pairs), margin=dict(l=10, r=20, t=40, b=40),
    title=f"{bloc.capitalize()} share, {_label(_test)}: first canton minus second (points, 95% interval)",
    xaxis_title="Difference in vote share (points)", showlegend=False,
)
st.plotly_chart(fig, width="stretch")
st.caption("Dark: clear difference (interval excludes 0 and the typical-town test is significant). "
           "Grey: not clear on at least one of the two. Each row is the first canton minus the second; "
           "the diamond is the pair selected above, shown as A minus B.")

with st.expander("How to read the tests, and the full table"):
    st.markdown(
        "- **Difference and interval:** the canton's share of all its voters, A minus B, with a 95% "
        "bootstrap interval.\n"
        "- **Typical-town test:** whether the typical town in A differs from the typical town in B "
        "(Mann–Whitney, Holm-adjusted across canton pairs). Each town counts once, so when a few large "
        "towns drive the voters' share the two can disagree.\n"
        "- Neighbouring towns vote alike, so p-values are somewhat optimistic.\n\n"
        f"Across all cantons ({bloc}): Kruskal–Wallis H = {row['kw_h']:.1f}, p = {row['kw_p']:.3g}, "
        f"ε² = {row['kw_eps2']:.2f}."
    )
    table = tests[tests.bloc == bloc].assign(
        canton_a=lambda t: t.canton_a.map(names), canton_b=lambda t: t.canton_b.map(names))
    st.dataframe(table[["canton_a", "canton_b", "mean_a", "mean_b", "diff", "ci_low", "ci_high", "p_holm"]].round(3),
                 hide_index=True, width="stretch")
