"""The public page's data files (site/data/) must agree with the pipeline's outputs."""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.config import BLOC_COLS, DATA_PROCESSED, KNESSET_IDS

SITE_DATA = Path(__file__).resolve().parent.parent / "site" / "data"


@pytest.fixture(scope="module")
def towns():
    return json.loads((SITE_DATA / "towns.geojson").read_text(encoding="utf-8"))["features"]


@pytest.fixture(scope="module")
def cantons():
    return {c["id"]: c for c in json.loads((SITE_DATA / "cantons.json").read_text(encoding="utf-8"))}


@pytest.fixture(scope="module")
def meta():
    return json.loads((SITE_DATA / "meta.json").read_text(encoding="utf-8"))


def test_every_municipality_appears_once_in_its_canton(towns):
    final = dict(pd.read_csv(DATA_PROCESSED / "cantons_final.csv").values)
    page = {f["properties"]["he"]: f["properties"]["canton"] for f in towns}
    assert len(page) == len(towns) == len(final)
    assert page == final


def test_town_names_and_shares_match_the_features(towns):
    feats = pd.read_csv(DATA_PROCESSED / "political_features.csv").set_index("municipality")
    for f in towns:
        p = f["properties"]
        assert p["he"] and p["en"], p
        for i, bloc in enumerate(BLOC_COLS):
            assert p["blocs"][i] == pytest.approx(feats.loc[p["he"], f"{bloc}_avg"], abs=0.051), (p["he"], bloc)
        assert set(p["votes"]) == {str(k) for k in KNESSET_IDS}


def test_canton_per_election_matches_the_per_election_maps(towns):
    for k in KNESSET_IDS:
        per = dict(pd.read_csv(DATA_PROCESSED / "per_election" / f"knesset_{k}.csv").values)
        assert {f["properties"]["he"]: f["properties"]["elections"][str(k)] for f in towns} == per


def test_canton_summaries_match_the_report_table(cantons):
    stats = pd.read_csv(DATA_PROCESSED / "cantons_final_stats.csv").set_index("canton")
    assert set(cantons) == set(stats.index)
    for cid, row in stats.iterrows():
        c = cantons[cid]
        assert c["towns"] == row["n_municipalities"] and c["voters"] == row["total_voters"]
        assert c["blocs"] == [row[f"{b}_pct"] for b in BLOC_COLS]
        assert c["he"] and c["en"] and c["color"].startswith("#")
        assert len(c["largest"]) == min(5, row["n_municipalities"])


def test_headline_numbers_come_from_the_results(meta, towns):
    stab = pd.read_csv(DATA_PROCESSED / "stability_results.csv").set_index("config")["mean_ari"]
    assert meta["stability_ari"] == round(stab["NMF_5 / Cosine / Louvain"], 3)
    changes = pd.read_csv(DATA_PROCESSED / "per_election" / "per_election_changes.csv")
    assert meta["towns_never_moved"] == int((changes["n_differ"] == 0).sum())
    assert meta["towns"] == len(towns)
    tests = pd.read_csv(DATA_PROCESSED / "canton_tests.csv")
    assert meta["heldout"]["pairs"] == len(tests)
    assert meta["heldout"]["significant"] == int((tests["p_holm"] < 0.05).sum())
    assert set(meta["elections"]) == {str(k) for k in KNESSET_IDS}
    assert all(e["short"].endswith(e["en"].split()[-1]) for e in meta["elections"].values())


def test_town_file_stays_small_enough_for_phones():
    assert (SITE_DATA / "towns.geojson").stat().st_size < 2_000_000


def test_share_preview_image_has_the_standard_size():
    from PIL import Image

    with Image.open(SITE_DATA.parent / "og.png") as img:
        assert img.size == (1200, 630)
