"""Coalition and opposition: a description of each election, never an input to the cantons."""

import pandas as pd
import pytest

from src.config import COALITION_LISTS, DATA_PROCESSED


def test_coalition_lists_are_the_governments_formed_after_each_election():
    # March 2021 -> Bennett-Lapid (36th government); November 2022 -> Netanyahu (37th government)
    assert COALITION_LISTS[24] == {"פה", "כן", "ב", "אמת", "ל", "ת", "מרצ", "עם"}
    assert COALITION_LISTS[25] == {"מחל", "שס", "ג", "ט"}
    # 2019 (twice): no government formed; 2020: the lists split after the vote
    assert set(COALITION_LISTS) == {24, 25}


@pytest.fixture(scope="module")
def shares():
    from src.data.coalition import coalition_shares
    from src.data.processing import process_all_elections

    return coalition_shares(process_all_elections())


def test_coalition_share_is_the_share_of_valid_votes(shares):
    from src.data.processing import process_all_elections

    e = process_all_elections()[25].set_index("municipality")
    town = "בני ברק"
    expected = e.loc[town, sorted(COALITION_LISTS[25])].sum() / e.loc[town, "valid"] * 100
    row = shares[(shares.municipality == town) & (shares.knesset == 25)].iloc[0]
    assert row.coalition_pct == pytest.approx(expected)
    assert row.coalition_pct > 90  # Shas + UTJ + Likud + RZP


def test_every_town_has_a_share_in_each_characterised_election(shares):
    assert set(shares.knesset) == {24, 25}
    assert shares.groupby("knesset").municipality.nunique().eq(255).all()
    assert shares.coalition_pct.between(0, 100).all()


def test_canton_coalition_table_matches_the_town_shares():
    towns = pd.read_csv(DATA_PROCESSED / "coalition_shares.csv")
    cantons = pd.read_csv(DATA_PROCESSED / "canton_coalition.csv")
    final = dict(pd.read_csv(DATA_PROCESSED / "cantons_final.csv").values)
    towns["canton"] = towns.municipality.map(final)
    for (canton, k), g in towns.groupby(["canton", "knesset"]):
        expected = (g.coalition_pct * g.valid).sum() / g.valid.sum()
        got = cantons[(cantons.canton == canton) & (cantons.knesset == k)].coalition_pct.iloc[0]
        assert got == pytest.approx(expected, abs=0.051)
