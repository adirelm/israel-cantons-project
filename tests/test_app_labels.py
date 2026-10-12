"""The public app must name the primary map's cantons correctly."""

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402


def _canton_table(page: str):
    at = AppTest.from_file(page, default_timeout=180).run()
    assert not at.exception, [e.message for e in at.exception]
    tables = [df.value for df in at.dataframe if "Canton" in df.value.columns and "Municipalities" in df.value.columns]
    assert tables, f"no canton table on {page}"
    return tables[0].set_index("Canton")


@pytest.mark.parametrize("page", ["../app/app.py", "../app/pages/1_Canton_Map.py"])
def test_featured_cantons_carry_their_own_names(page):
    table = _canton_table(page)
    assert table.loc["HAREDI Cities", "Municipalities"] == 7
    assert table.loc["ARAB", "Municipalities"] == 60
    assert str(table.loc["HAREDI Cities", "Largest Bloc"]).startswith("Haredi")
    # Voter-weighted, as in the report: Right 41.1% vs Center 39.0% (towns counted equally give Center)
    assert str(table.loc["METRO Tel Aviv", "Largest Bloc"]).startswith("Right")


def test_stability_page_quotes_the_current_ari_values():
    import pandas as pd
    from src.config import DATA_PROCESSED

    stab = pd.read_csv(DATA_PROCESSED / "stability_results.csv").set_index("config")["mean_ari"]
    at = AppTest.from_file("../app/pages/3_Stability.py", default_timeout=180).run()
    assert not at.exception
    text = " ".join(i.value for i in at.info)
    assert f"{stab['BlocShares / Euclidean / Louvain']:.3f}" in text
    assert f"{stab['NMF_5 / Cosine / Louvain']:.3f}" in text


def test_compare_page_names_the_elections_the_tests_used():
    import sys
    import pandas as pd
    from src.config import DATA_PROCESSED, ELECTION_LABELS

    tests = pd.read_csv(DATA_PROCESSED / "canton_tests.csv")
    assert {"train_elections", "test_election"} <= set(tests.columns)
    train = [int(k) for k in str(tests["train_elections"].iloc[0]).split(",")]
    test = int(tests["test_election"].iloc[0])
    at = AppTest.from_file("../app/pages/5_Compare_Cantons.py", default_timeout=180).run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    assert ELECTION_LABELS[test] in text
    assert ELECTION_LABELS[train[0]].split()[-1] in text and ELECTION_LABELS[train[-1]].split()[-1] in text


def test_app_election_labels_match_the_pipeline():
    import sys
    from pathlib import Path
    from src.config import ELECTION_LABELS

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
    import utils
    assert utils.ELECTION_LABELS == ELECTION_LABELS


def _app_utils():
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
    import utils
    return utils


def test_canton_profiles_are_voter_weighted_like_the_report():
    import pandas as pd
    from src.config import DATA_PROCESSED

    utils = _app_utils()
    profiles = utils.canton_profiles(utils.load_primary_assignment(), utils.load_political_features())
    stats = pd.read_csv(DATA_PROCESSED / "cantons_final_stats.csv").set_index("canton")
    for bloc in utils.BLOCS:
        assert (profiles[bloc] - stats[f"{bloc}_pct"]).abs().max() < 0.06, bloc
    assert profiles["dominant"].to_dict() == stats["dominant_bloc"].to_dict()
    assert profiles["n_munis"].to_dict() == stats["n_municipalities"].to_dict()


def test_featured_map_names_its_cantons_and_needs_no_basemap_key():
    utils = _app_utils()
    names = dict(utils.load_cantons_labeled()[["canton", "label"]].drop_duplicates().values)
    m = utils.build_canton_map(utils.load_geojson(), utils.load_primary_assignment(),
                               utils.load_political_features(), names=names)
    html = m.get_root().render()
    for name in names.values():
        assert name.replace("&", "&amp;") in html or name in html, name
    assert "Canton 0 (CENTER)" not in html
    assert "cartocdn" not in html  # CARTO basemaps now need an API key and show watermarks


def test_primary_cantons_get_distinct_colours_and_a_mixed_canton_blends_its_two_blocs():
    utils = _app_utils()
    profiles = utils.canton_profiles(utils.load_primary_assignment(), utils.load_political_features())
    colours = utils.canton_colors(profiles)
    assert len(set(colours.values())) == len(profiles)
    # METRO Tel Aviv: Right 41.1% vs Center 39.0% — neither the Right nor the Center shade family
    assert colours[0] not in utils.BLOC_SHADES["right"] + utils.BLOC_SHADES["center"]
    assert colours[1] in utils.BLOC_SHADES["right"] and colours[3] in utils.BLOC_SHADES["arab"]


def test_home_page_quotes_the_current_primary_numbers():
    import pandas as pd
    from src.config import DATA_PROCESSED

    ex = pd.read_csv(DATA_PROCESSED / "experiments" / "experiment_results.csv")
    primary = ex[(ex["repr"] == "nmf_5") & (ex["metric"] == "cosine") & (ex["algo"] == "louvain") & (ex["k_target"] == 5)]
    ari = pd.read_csv(DATA_PROCESSED / "stability_results.csv").set_index("config").loc["NMF_5 / Cosine / Louvain", "mean_ari"]
    at = AppTest.from_file("../app/app.py", default_timeout=180).run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    assert f"{primary['silhouette'].iloc[0]:.3f}" in text and f"{ari:.3f}" in text


def test_canton_map_page_is_light_enough_to_load_quickly():
    """One simplified layer instead of 255 full-resolution ones (the old map sent ~30 MB)."""
    utils = _app_utils()
    m = utils.build_canton_map(utils.load_geojson(), utils.load_primary_assignment(), utils.load_political_features())
    assert len(m.get_root().render()) < 3_000_000


def test_per_election_map_outlines_the_towns_that_moved():
    utils = _app_utils()
    args = (utils.load_geojson(), utils.load_primary_assignment(), utils.load_political_features())
    assert utils.MOVED_COLOR not in utils.build_canton_map(*args).get_root().render()
    assert utils.MOVED_COLOR in utils.build_canton_map(*args, outlined={"נחל שורק"}).get_root().render()


def test_router_opens_the_home_page_with_explore_and_research_sections():
    at = AppTest.from_file("../app/app.py", default_timeout=180).run()
    assert not at.exception, [e.message for e in at.exception]
    assert any("Largest Bloc" in df.value.columns for df in at.dataframe)


def test_compare_page_states_the_difference_in_words():
    at = AppTest.from_file("../app/pages/5_Compare_Cantons.py", default_timeout=180).run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    assert "points" in text and "METRO Tel Aviv" in text
    assert len(at.get("plotly_chart")) >= 1
