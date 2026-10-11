#!/usr/bin/env python3
"""Build data/raw/geo/municipalities_js.geojson: Israeli local authorities in Judea and Samaria.

    python scripts/build_boundaries.py

Inputs: data/raw/geo/js/*.geojson (see data/raw/geo/SOURCES.md for the download queries).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import geopandas as gpd
import pandas as pd
import shapely
from shapely import make_valid
from shapely.ops import unary_union

from src.config import GEO_DIR
from src.data.loader import load_municipality_geojson
from src.data.processing import aggregate_all_elections
from src.graph.boundaries import (
    ITM, build_regional_council, clip_overlaps, match_names, points_inside, resolve_council_overlaps,
)

JS_DIR = GEO_DIR / "js"
OUT = GEO_DIR / "municipalities_js.geojson"
SIMPLIFY_M = 5.0

# Civil Administration council code → (name in the election data, English name).
# Codes confirmed by their member settlements (data/raw/geo/SOURCES.md).
REGIONAL_COUNCILS = {
    100: ("שומרון", "Shomron"),
    200: ("מטה בנימין", "Mateh Binyamin"),
    300: ("ערבות הירדן", "Arvot HaYarden"),
    400: ("גוש עציון", "Gush Etzion"),
    500: ("הר חברון", "Har Hevron"),
    600: ("מגילות ים המלח", "Megilot"),
}

PALESTINIAN_CITIES = {  # (lat, lon); none may fall inside an Israeli authority polygon
    "Ramallah": (31.9038, 35.2034), "Al-Bireh": (31.9100, 35.2167), "Nablus": (32.2211, 35.2544),
    "Jericho": (31.8667, 35.4500), "Bethlehem": (31.7054, 35.2024), "Hebron old city": (31.5247, 35.1101),
}


def english(name: str) -> str:
    """CBS upper-case transliteration → title case ("MA'ALE ADUMMIM" → "Ma'ale Adummim")."""
    return " ".join("-".join(p.capitalize() for p in w.split("-")) for w in name.split())


def target_authorities() -> list[str]:
    """Municipalities with votes in every election but no polygon inside the Green Line."""
    in_all = set.intersection(*(set(df["municipality"]) for df in aggregate_all_elections().values()))
    return sorted(in_all - set(load_municipality_geojson(include_js=False)["MUN_HEB"]))


def main() -> None:
    targets = target_authorities()
    rc_names = {name for name, _ in REGIONAL_COUNCILS.values()}
    cities = [t for t in targets if t not in rc_names]
    print(f"{len(targets)} authorities to add: {', '.join(targets)}")

    cbs = gpd.read_file(JS_DIR / "cbs_munc2023.geojson").to_crs(ITM)
    cbs["name"] = cbs["MAX_MUNC_NAME"].str.strip()
    source_of = match_names(cbs["name"], cities, {})
    city_gdf = gpd.GeoDataFrame([{
        "MUN_HEB": target,
        "MUN_ENG": english(cbs.loc[cbs["name"] == source_of[target], "MAX_MUNC_NAME_ENG"].iloc[0]),
        "geometry": unary_union([make_valid(g) for g in cbs.loc[cbs["name"] == source_of[target], "geometry"]]),
    } for target in cities], crs=ITM)

    rc = gpd.read_file(JS_DIR / "ca_regional_councils.geojson").to_crs(ITM)
    st = gpd.read_file(JS_DIR / "ca_settlements.geojson").to_crs(ITM)
    cities_union = city_gdf.union_all()
    codes = [c for c, (name, _) in REGIONAL_COUNCILS.items() if name in targets]
    members = {c: unary_union([make_valid(g) for g in st.loc[st["MUNICIPAL_NAME"].astype(str) == str(c), "geometry"]])
               for c in codes}
    closed = {c: build_regional_council(rc[rc["MUNICIPAL_DISTR"].astype(str) == str(c)].geometry,
                                        st[st["MUNICIPAL_NAME"].astype(str) == str(c)].geometry, None)
              for c in codes}
    councils = resolve_council_overlaps(closed, members)
    rc_rows = [{"MUN_HEB": REGIONAL_COUNCILS[c][0], "MUN_ENG": REGIONAL_COUNCILS[c][1],
                "geometry": councils[c].difference(cities_union)} for c in codes]
    missing_rc = sorted((rc_names & set(targets)) - {r["MUN_HEB"] for r in rc_rows})
    if missing_rc:
        raise ValueError(f"No regional-council polygon for: {', '.join(missing_rc)}")
    js = gpd.GeoDataFrame(pd.concat([city_gdf, gpd.GeoDataFrame(rc_rows, crs=ITM)], ignore_index=True), crs=ITM)

    existing = load_municipality_geojson(include_js=False).to_crs(ITM)
    js = clip_overlaps(js, existing.geometry.make_valid().union_all())
    js = js[~js.geometry.is_empty]
    # Closing buffers add many vertices. Simplify all polygons together so shared borders
    # stay shared; 5 m is far below the 100 m adjacency tolerance.
    js["geometry"] = shapely.coverage_simplify(js.geometry.values, tolerance=SIMPLIFY_M)

    geoms = list(js.geometry)
    overlap_m2 = sum(a.intersection(b).area for i, a in enumerate(geoms) for b in geoms[i + 1:])
    assert overlap_m2 < 1_000, f"New polygons overlap each other by {overlap_m2:.0f} m²"
    assert set(js["MUN_HEB"]) == set(targets), set(targets) ^ set(js["MUN_HEB"])
    inside = points_inside(js, PALESTINIAN_CITIES)
    assert not inside, f"Palestinian city points inside Israeli authority polygons: {inside}"

    js["area_km2"] = (js.geometry.area / 1e6).round(2)
    js["parts"] = js.geometry.apply(lambda g: len(getattr(g, "geoms", [g])))
    print(js[["MUN_HEB", "MUN_ENG", "area_km2", "parts"]].sort_values("area_km2").to_string(index=False))
    print("vertices:", int(js.geometry.count_coordinates().sum()))
    js[["MUN_HEB", "MUN_ENG", "geometry"]].to_crs(4326).to_file(OUT, driver="GeoJSON", COORDINATE_PRECISION=6)
    print(f"Wrote {OUT} ({len(js)} authorities)")


if __name__ == "__main__":
    main()
