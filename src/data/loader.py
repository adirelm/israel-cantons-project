"""Raw data loading functions.

Loads election CSVs, CBS locality mapping, and municipality GeoJSON.
"""

from __future__ import annotations

import pandas as pd
import geopandas as gpd

from src.config import ELECTIONS_DIR, ELECTION_FILES, DATA_RAW, GEO_DIR


def load_election_csv(knesset: int) -> pd.DataFrame:
    """Load a single election CSV with encoding fallback.

    Returns the raw DataFrame with Hebrew column names.
    """
    filename = ELECTION_FILES[knesset]
    filepath = ELECTIONS_DIR / filename
    try:
        return pd.read_csv(filepath, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(filepath, encoding="iso-8859-8")


def load_all_elections() -> dict[int, pd.DataFrame]:
    """Load all 5 election CSVs.

    Returns ``{knesset_id: DataFrame}``.
    """
    return {k: load_election_csv(k) for k in ELECTION_FILES}


def load_cbs_localities() -> pd.DataFrame:
    """Load CBS ``localities_bycode.xlsx``."""
    return pd.read_excel(DATA_RAW / "localities_bycode.xlsx")


def load_municipality_geojson() -> gpd.GeoDataFrame:
    """Load raw ``municipalities.geojson``."""
    return gpd.read_file(GEO_DIR / "municipalities.geojson")


def build_locality_to_municipality_mapping(
    cbs: pd.DataFrame | None = None,
) -> dict[int, str | None]:
    """Map locality code → municipality name using CBS data.

    * Cities / local councils → locality name.
    * Regional councils → council name (strip prefix).
    * No municipal status → ``None``.
    """
    if cbs is None:
        cbs = load_cbs_localities()

    def _get_municipality(row: pd.Series) -> str | None:
        status = row["שם מעמד מונציפאלי"]
        if pd.isna(status):
            return None
        if status in ("עירייה", "מועצה מקומית"):
            return row["שם יישוב"]
        if status.startswith("מועצה אזורית "):
            return status.replace("מועצה אזורית ", "")
        if status == "חסר מעמד מוניציפלי":
            return None
        return status

    cbs = cbs.copy()
    cbs["municipality"] = cbs.apply(_get_municipality, axis=1)
    return dict(zip(cbs["סמל יישוב"], cbs["municipality"]))
