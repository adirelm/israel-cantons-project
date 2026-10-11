"""Build boundary polygons for Israeli local authorities in Judea and Samaria.

Pure helpers used by scripts/build_boundaries.py. Source layers contain
invalid geometries, so every input is repaired with ``make_valid`` first.
"""

from __future__ import annotations

from collections.abc import Iterable

import geopandas as gpd
from shapely import make_valid
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

ITM = "EPSG:2039"


def match_names(source_names: Iterable[str], targets: Iterable[str], fixes: dict[str, str]) -> dict[str, str]:
    """Map each target name to the source name that denotes it (after ``fixes``).

    Raises ``ValueError`` naming every target with no source, so no authority drops out silently.
    """
    by_target = {fixes.get(s.strip(), s.strip()): s for s in source_names}
    missing = [t for t in targets if t not in by_target]
    if missing:
        raise ValueError(f"No source polygon for: {', '.join(sorted(missing))}")
    return {t: by_target[t] for t in targets}


def build_regional_council(
    own: gpd.GeoSeries, members: gpd.GeoSeries, exclude: BaseGeometry | None, close_m: float = 50.0
) -> BaseGeometry:
    """Union of a council's own area and its member settlements, minus ``exclude``.

    A closing buffer (out, then in by ``close_m`` metres) joins pieces separated by
    slivers without moving outer edges. Inputs must be in a metric CRS.
    """
    geom = unary_union([make_valid(g) for g in list(own.geometry) + list(members.geometry)])
    geom = geom.buffer(close_m).buffer(-close_m)
    if exclude is not None:
        geom = geom.difference(make_valid(exclude))
    return geom


def resolve_council_overlaps(
    areas: dict[int, BaseGeometry], members: dict[int, BaseGeometry]
) -> dict[int, BaseGeometry]:
    """Make regional-council areas disjoint (the source layer has overlapping councils).

    1. Where two councils overlap, the overlap goes to the council with more of its
       member settlements' area inside it; if neither has any, to the council for
       which the overlap is the larger share of its own area.
    2. A member settlement's jurisdiction always stays with its own council.
    """
    original = {c: make_valid(g) for c, g in areas.items()}
    result = dict(original)
    codes = sorted(result)
    for i, a in enumerate(codes):
        for b in codes[i + 1:]:
            overlap = result[a].intersection(result[b])
            if overlap.area == 0:
                continue
            in_a, in_b = members[a].intersection(overlap).area, members[b].intersection(overlap).area
            if in_a != in_b:
                winner = a if in_a > in_b else b
            else:
                winner = a if overlap.area / original[a].area >= overlap.area / original[b].area else b
            loser = b if winner == a else a
            result[loser] = result[loser].difference(overlap)
    for c in codes:
        others = unary_union([members[o] for o in codes if o != c])
        result[c] = result[c].union(members[c]).difference(others)
    return result


def clip_overlaps(gdf: gpd.GeoDataFrame, occupied: BaseGeometry) -> gpd.GeoDataFrame:
    """Remove ``occupied`` from every geometry (keeps rows, drops nothing)."""
    out = gdf.copy()
    out["geometry"] = out.geometry.make_valid().difference(make_valid(occupied))
    return out


def points_inside(gdf: gpd.GeoDataFrame, points: dict[str, tuple[float, float]]) -> list[str]:
    """Names of (lat, lon) points that fall inside any polygon of ``gdf``."""
    union = gdf.to_crs(4326).union_all()
    return [name for name, (lat, lon) in points.items() if union.contains(Point(lon, lat))]
