"""Central configuration for the Israel Cantons project.

All paths, constants, and mappings in one place.
"""

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

# Party-code → bloc mapping for each Knesset
BLOC_MAPPING: dict[int, dict[str, str]] = {
    21: {  # April 2019
        "מחל": "right",      # Likud
        "פה": "center",      # Blue & White (Kahol Lavan)
        "שס": "haredi",      # Shas
        "ג": "haredi",       # UTJ (Yahadut HaTorah)
        "דעם": "arab",       # Hadash-Ta'al
        "ום": "arab",        # Ra'am-Balad
        "טב": "right",       # Union of Right-Wing Parties
        "ל": "right",        # Yisrael Beiteinu
        "מרצ": "left",       # Meretz
        "אמת": "left",       # Labor
        "כ": "center",       # Kulanu
        "נ": "right",        # New Right
        "ז": "right",        # Zehut
        "נר": "center",      # Gesher
    },
    22: {  # September 2019
        "מחל": "right",      # Likud
        "פה": "center",      # Blue & White
        "שס": "haredi",      # Shas
        "ג": "haredi",       # UTJ
        "ודעם": "arab",      # Joint List
        "ל": "right",        # Yisrael Beiteinu
        "טב": "right",       # Yamina
        "אמת": "left",       # Labor-Gesher
        "מרצ": "left",       # Democratic Union (Meretz+)
        "כף": "right",       # Otzma Yehudit
    },
    23: {  # March 2020
        "מחל": "right",      # Likud
        "פה": "center",      # Blue & White
        "שס": "haredi",      # Shas
        "ג": "haredi",       # UTJ
        "ודעם": "arab",      # Joint List
        "ל": "right",        # Yisrael Beiteinu
        "טב": "right",       # Yamina
        "אמת": "left",       # Labor-Gesher-Meretz
    },
    24: {  # March 2021
        "מחל": "right",      # Likud
        "פה": "center",      # Yesh Atid
        "שס": "haredi",      # Shas
        "ג": "haredi",       # UTJ
        "ודעם": "arab",      # Joint List (Hadash-Ta'al)
        "ל": "right",        # Yisrael Beiteinu
        "טב": "right",       # Yamina
        "ב": "right",        # Religious Zionist Party
        "כן": "center",      # Blue & White
        "מרצ": "left",       # Meretz
        "אמת": "left",       # Labor
        "עם": "arab",        # Ra'am
        "ת": "center",       # New Hope
    },
    25: {  # November 2022
        "מחל": "right",      # Likud
        "פה": "center",      # Yesh Atid
        "שס": "haredi",      # Shas
        "ג": "haredi",       # UTJ
        "ט": "right",        # Religious Zionist Party
        "ל": "right",        # Yisrael Beiteinu
        "ד": "arab",         # Hadash-Ta'al
        "ום": "arab",        # Balad
        "מרצ": "left",       # Meretz
        "אמת": "left",       # Labor
        "עם": "arab",        # Ra'am
        "כן": "center",      # National Unity (Gantz)
    },
}

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
