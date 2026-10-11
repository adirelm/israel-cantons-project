"""Tests for the party-to-bloc mapping in src.config."""

import json

import pandas as pd
import pytest

from src.config import BLOC_COLS, BLOC_MAPPING, DATA_PROCESSED, KNESSET_IDS

# Any party at or above this share of the valid vote must belong to a bloc;
# smaller lists may fall into "other".
MIN_MAPPED_SHARE_PCT = 1.0

NON_PARTY = {"municipality", "eligible", "voters", "invalid", "valid", "knesset", "turnout_pct"}


def _matched_election(knesset: int) -> pd.DataFrame:
    path = DATA_PROCESSED / f"election_knesset_{knesset}_matched.csv"
    if not path.exists():
        pytest.skip(f"{path.name} not available")
    return pd.read_csv(path)


@pytest.mark.parametrize("knesset", KNESSET_IDS)
def test_every_party_above_threshold_is_mapped(knesset):
    df = _matched_election(knesset)
    parties = [c for c in df.columns if c not in NON_PARTY and not c.endswith("_pct")]
    shares = df[parties].sum() / df["valid"].sum() * 100
    unmapped = {
        p: round(s, 2) for p, s in shares.items()
        if s >= MIN_MAPPED_SHARE_PCT and p not in BLOC_MAPPING[knesset]
    }
    assert not unmapped, f"Knesset {knesset}: parties with no bloc: {unmapped}"


@pytest.mark.parametrize("knesset,code", [
    (23, "נץ"),  # Otzma Yehudit, March 2020
    (24, "ט"),   # Religious Zionist Party, March 2021
    (25, "ב"),   # Jewish Home, November 2022
])
def test_right_wing_lists_are_mapped_to_right(knesset, code):
    assert BLOC_MAPPING[knesset].get(code) == "right"


def test_mapping_uses_only_known_blocs():
    for knesset, mapping in BLOC_MAPPING.items():
        assert set(mapping.values()) <= set(BLOC_COLS), knesset


def test_saved_bloc_mappings_match_config():
    path = DATA_PROCESSED / "bloc_mappings.json"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert {int(k): v for k, v in saved.items()} == BLOC_MAPPING


EXPECTED_MAPPING = {
    21: {"מחל": "right", "פה": "center", "שס": "haredi", "ג": "haredi", "דעם": "arab", "ום": "arab",
         "טב": "right", "ל": "right", "מרצ": "left", "אמת": "left", "כ": "center", "נ": "right",
         "ז": "right", "נר": "center"},
    22: {"מחל": "right", "פה": "center", "שס": "haredi", "ג": "haredi", "ודעם": "arab", "ל": "right",
         "טב": "right", "אמת": "left", "מרצ": "left", "כף": "right"},
    23: {"מחל": "right", "פה": "center", "שס": "haredi", "ג": "haredi", "ודעם": "arab", "ל": "right",
         "טב": "right", "נץ": "right", "אמת": "left"},
    24: {"מחל": "right", "פה": "center", "שס": "haredi", "ג": "haredi", "ודעם": "arab", "ל": "right",
         "ב": "right", "ט": "right", "כן": "center", "מרצ": "left", "אמת": "left", "עם": "arab",
         "ת": "center"},
    25: {"מחל": "right", "פה": "center", "שס": "haredi", "ג": "haredi", "ט": "right", "ב": "right",
         "ל": "right", "ד": "arab", "ום": "arab", "מרצ": "left", "אמת": "left", "עם": "arab",
         "כן": "center"},
}


def test_mapping_from_party_table_matches_previous_dict():
    assert BLOC_MAPPING == EXPECTED_MAPPING


def test_party_table_rows_are_unique_and_named():
    from src.config import PARTIES_CSV
    table = pd.read_csv(PARTIES_CSV)
    assert not table.duplicated(["knesset", "letters"]).any()
    assert table["bloc"].isin(BLOC_COLS).all()
    assert table["name_he"].str.strip().ne("").all()
    assert table["name_en"].str.strip().ne("").all()
    assert set(table["knesset"]) <= set(KNESSET_IDS)
