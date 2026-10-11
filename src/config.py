"""Central configuration for the Israel Cantons project.

All paths, constants, and mappings in one place.
"""

import csv
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
ELECTIONS_DIR = DATA_RAW / "elections"
GEO_DIR = DATA_RAW / "geo"

# ---------------------------------------------------------------------------
# Election metadata
# ---------------------------------------------------------------------------
ELECTION_FILES: dict[int, str] = {
    21: "knesset_21_apr2019.csv",
    22: "knesset_22_sep2019.csv",
    23: "knesset_23_mar2020.csv",
    24: "knesset_24_mar2021.csv",
    25: "knesset_25_nov2022.csv",
}

KNESSET_IDS: list[int] = [21, 22, 23, 24, 25]

# Columns that are NOT party vote columns
NON_PARTY_COLS: list[str] = [
    "municipality", "locality_name", "locality_code",
    "eligible", "voters", "invalid", "valid",
    "knesset", "turnout_pct",
]

# ---------------------------------------------------------------------------
# Political blocs
# ---------------------------------------------------------------------------
BLOC_COLS: list[str] = ["right", "haredi", "center", "left", "arab"]

PARTIES_CSV = PROJECT_ROOT / "data" / "reference" / "parties.csv"


def _load_bloc_mapping(path: Path) -> dict[int, dict[str, str]]:
    """Ballot letters → bloc for each Knesset, read from the party table."""
    mapping: dict[int, dict[str, str]] = {}
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            mapping.setdefault(int(row["knesset"]), {})[row["letters"]] = row["bloc"]
    return mapping


# Party-code → bloc mapping for each Knesset (names in data/reference/parties.csv)
BLOC_MAPPING: dict[int, dict[str, str]] = _load_bloc_mapping(PARTIES_CSV)

# ---------------------------------------------------------------------------
# Municipality name fixes (election spelling → GeoJSON spelling)
# ---------------------------------------------------------------------------
NAME_FIXES: dict[str, str] = {
    "באקה אל-גרביה": "באקה אל גרבייה",
    "בנימינה-גבעת עדה*": "בנימינה - גבעת עדה",
    "בוסתן אל-מרג'": "בוסתאן אל-מרג'",
    "ג'ולס": "ג'וליס",
    "ג'ש (גוש חלב)": "גוש חלב (ג'יש)",
    "גן רווה": "גן רוה",
    "יאנוח-ג'ת": "יאנוח - ג'ת",
    "יהוד-מונוסון": "יהוד -מונסון",
    "כסיפה": "כסייפה",
    "כסרא-סמיע": "כסרא - סמיע",
    "דבורייה": "דבוריה",
    "דייר אל-אסד": "דיר אל-אסד",
    "דייר חנא": "דיר חנא",
    "הרצלייה": "הרצליה",
    "טובא-זנגרייה": "טובא-זנגריה",
    "כעביה-טבאש-חג'אג'רה": "כעביה - טבאש - חג'אג'רה",
    "מגאר": "מג'אר",
    "מודיעין-מכבים-רעות*": "מודיעין-מכבים-רעות",
    "נהרייה": "נהריה",
    "סביון*": "סביון",
    "עיילבון": "עילבון",
    "עין קנייא": "עין קיניה",
    "עספיא": "עוספייא",
    "ערערה-בנגב": "ערערה בנגב",
    "פרדס חנה-כרכור": "פרדס חנה - כרכור",
    "פרדסייה": "פרדסיה",
    "קדימה-צורן": "קדימה - צורן",
    "קריית אונו": "קרית אונו",
    "קריית אתא": "קרית אתא",
    "קריית ביאליק": "קרית ביאליק",
    "קריית גת": "קרית גת",
    "קריית טבעון": "קרית טבעון",
    "קריית ים": "קרית ים",
    "קריית יערים": "קרית יערים",
    "קריית מוצקין": "קרית מוצקין",
    "קריית מלאכי": "קרית מלאכי",
    "קריית עקרון": "קרית עקרון",
    "קריית שמונה": "קרית שמונה",
    "שבלי - אום אל-ע'נם": "שבלי - אום אל-ג'נם",
    "שגב-שלום": "שגב שלום",
    "שוהם": "שהם",
}
