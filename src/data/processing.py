"""Data processing: aggregation, name fixes, and GeoJSON matching.

Transforms raw locality-level election data into municipality-level
DataFrames ready for feature engineering.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import geopandas as gpd

from src.config import (
    NAME_FIXES,
    NON_PARTY_COLS,
    KNESSET_IDS,
)
from src.data.loader import (
    load_all_elections,
    load_cbs_localities,
    load_municipality_geojson,
    build_locality_to_municipality_mapping,
)


# ---------------------------------------------------------------------------
# Column helpers
# ---------------------------------------------------------------------------

def get_party_columns(df: pd.DataFrame) -> list[str]:
    """Return column names that represent party vote counts (not pct, not metadata)."""
    return [
        c for c in df.columns
        if c not in NON_PARTY_COLS
        and not c.endswith("_pct")
        and c != "סמל ועדה"
    ]


def standardize_columns(
    df: pd.DataFrame, knesset: int
) -> tuple[pd.DataFrame, list[str]]:
    """Rename Hebrew metadata columns to English; identify party columns.

    Returns ``(standardised_df, party_column_names)``.
    """
    df = df.copy()
    cols = df.columns.tolist()

    name_idx = cols.index("שם ישוב") if "שם ישוב" in cols else 0
    code_idx = cols.index("סמל ישוב") if "סמל ישוב" in cols else 1

    col_map = {
        cols[name_idx]: "locality_name",
        cols[code_idx]: "locality_code",
        "בזב": "eligible",
        "מצביעים": "voters",
        "פסולים": "invalid",
        "כשרים": "valid",
    }
    df = df.rename(columns=col_map)

    std_cols = {"locality_name", "locality_code", "eligible", "voters", "invalid", "valid"}
    party_cols = [c for c in df.columns if c not in std_cols and c != "סמל ועדה"]
    return df, party_cols


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate_to_municipalities(
    df: pd.DataFrame,
    knesset: int,
    locality_to_muni: dict[int, str | None],
) -> tuple[pd.DataFrame, list[str]]:
    """Aggregate locality-level votes to municipality level.

    Returns ``(aggregated_df, party_columns)``.
    """
    df, party_cols = standardize_columns(df.copy(), knesset)
    df["municipality"] = df["locality_code"].map(locality_to_muni)

    # Drop unmapped localities
    df = df[df["municipality"].notna()].copy()

    agg_cols = ["eligible", "voters", "invalid", "valid"] + [
        c for c in party_cols if c in df.columns
    ]
    agg_dict = {col: "sum" for col in agg_cols}
    result = df.groupby("municipality").agg(agg_dict).reset_index()
    result["knesset"] = knesset
    return result, party_cols


def add_vote_percentages(
    df: pd.DataFrame, party_cols: list[str]
) -> pd.DataFrame:
    """Add ``<party>_pct`` columns and ``turnout_pct``."""
    df = df.copy()
    for party in party_cols:
        if party in df.columns:
            df[f"{party}_pct"] = df[party].div(df["valid"].replace(0, np.nan)).mul(100).round(2).fillna(0.0)
    df["turnout_pct"] = df["voters"].div(df["eligible"].replace(0, np.nan)).mul(100).round(2).fillna(0.0)
    return df


# ---------------------------------------------------------------------------
# Name fixing & GeoJSON matching
# ---------------------------------------------------------------------------

def apply_name_fixes(
    df: pd.DataFrame, fixes: dict[str, str] | None = None
) -> pd.DataFrame:
    """Replace municipality spelling variants to match GeoJSON names."""
    df = df.copy()
    df["municipality"] = df["municipality"].replace(fixes or NAME_FIXES)
    return df


def filter_to_geojson_matches(
    elections: dict[int, pd.DataFrame],
    geo: gpd.GeoDataFrame | None = None,
    name_col: str = "MUN_HEB",
) -> dict[int, pd.DataFrame]:
    """Keep only municipalities present in GeoJSON."""
    if geo is None:
        geo = load_municipality_geojson()
    geo_names = set(geo[name_col].str.strip())
    return {
        k: df[df["municipality"].isin(geo_names)].copy()
        for k, df in elections.items()
    }


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def process_all_elections(
    knesset_ids: list[int] | None = None,
) -> dict[int, pd.DataFrame]:
    """Run the full processing pipeline.

    Load → standardise → aggregate → add percentages → fix names → match GeoJSON.

    Returns ``{knesset_id: matched_DataFrame}``.
    """
    knesset_ids = knesset_ids or KNESSET_IDS

    raw = load_all_elections()
    cbs = load_cbs_localities()
    locality_to_muni = build_locality_to_municipality_mapping(cbs)
    geo = load_municipality_geojson()

    elections: dict[int, pd.DataFrame] = {}
    party_cols_by_knesset: dict[int, list[str]] = {}

    for k_id in knesset_ids:
        agg_df, party_cols = aggregate_to_municipalities(raw[k_id], k_id, locality_to_muni)
        agg_df = add_vote_percentages(agg_df, party_cols)
        agg_df = apply_name_fixes(agg_df)
        elections[k_id] = agg_df
        party_cols_by_knesset[k_id] = party_cols

    matched = filter_to_geojson_matches(elections, geo)
    return matched
