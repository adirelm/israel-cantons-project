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
    assert str(table.loc["HAREDI Cities", "Dominant Bloc"]).lower() == "haredi"


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
