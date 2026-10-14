"""Adding an election (the next one is October 2026) must need only its results file, a label and the party table."""

import sys
from pathlib import Path

from src.config import ELECTION_FILES, ELECTION_LABELS, KNESSET_IDS

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _script(name: str):
    sys.path.insert(0, str(SCRIPTS))
    return __import__(name)


def test_the_elections_are_the_results_files():
    assert KNESSET_IDS == sorted(ELECTION_FILES)
    assert set(ELECTION_LABELS) == set(KNESSET_IDS)
    assert all(label.split()[-1].isdigit() for label in ELECTION_LABELS.values())  # the page reads the year


def test_page_labels_follow_from_the_english_label():
    build = _script("build_site_data")
    assert build.election_names("October 2026") == {"en": "October 2026", "he": "אוקטובר 2026", "short": "10/2026"}
    assert build.election_names("April 2019") == {"en": "April 2019", "he": "אפריל 2019", "short": "4/2019"}
    assert build.election_names("November 2022") == {"en": "November 2022", "he": "נובמבר 2022", "short": "11/2022"}


def test_an_election_before_its_government_forms_says_so():
    build = _script("build_site_data")
    reasons = build.no_coalition_reasons([21, 22, 23, 24, 25, 26], {24: {"פה"}, 25: {"מחל"}})
    assert set(reasons) == {21, 22, 23, 26}
    assert reasons[21] == build.NO_COALITION[21]
    assert "not been formed yet" in reasons[26]["en"] and "עדיין" in reasons[26]["he"]


def test_the_held_out_election_is_the_latest():
    rebuild = _script("rebuild_results")
    assert rebuild.TEST_ELECTION == KNESSET_IDS[-1]
    assert rebuild.TRAIN_ELECTIONS == KNESSET_IDS[:-1]


def test_a_results_file_in_windows_hebrew_can_be_read(tmp_path):
    """Windows-1255 files with geresh or gershayim fail both UTF-8 and ISO-8859-8."""
    from src.data.loader import read_election_csv

    path = tmp_path / "results.csv"
    path.write_bytes("סמל ישוב,שם ישוב,כשרים,מחל\n3616,מעלה אדומים ״ק׳״,8,8\n".encode("cp1255"))
    df = read_election_csv(path)
    assert df.loc[0, "שם ישוב"] == "מעלה אדומים ״ק׳״"
    assert df.loc[0, "מחל"] == 8


def test_page_text_does_not_count_the_elections_by_hand():
    site = SCRIPTS.parent / "site"
    js = (site / "app.js").read_text(encoding="utf-8")
    for phrase in ("חמש מערכות", "five elections", '["5"'):
        assert phrase not in js, phrase
