"""Tests for src.graph.boundaries."""

import geopandas as gpd
import pytest
from shapely.geometry import Polygon, box

from src.graph.boundaries import ITM, build_regional_council, clip_overlaps, match_names, points_inside


def test_match_names_uses_fixes_and_reports_missing():
    assert match_names(["מודיעין עלית", "אריאל"], ["מודיעין עילית", "אריאל"],
                       {"מודיעין עלית": "מודיעין עילית"}) == {"מודיעין עילית": "מודיעין עלית", "אריאל": "אריאל"}
    with pytest.raises(ValueError, match="אפרת"):
        match_names(["אריאל"], ["אריאל", "אפרת"], {})


def test_regional_council_merges_own_area_and_members_minus_excluded():
    own = gpd.GeoSeries([box(0, 0, 1000, 1000)], crs=ITM)
    members = gpd.GeoSeries([box(1020, 0, 1500, 1000), box(5000, 0, 5100, 100)], crs=ITM)
    exclude = box(0, 0, 200, 200)
    geom = build_regional_council(own, members, exclude, close_m=50)
    assert geom.area == pytest.approx(1000 * 1000 + 480 * 1000 + 20 * 1000 + 100 * 100 - 200 * 200, rel=0.01)
    assert geom.geom_type == "MultiPolygon" and len(geom.geoms) == 2  # 20 m gap closed, far piece kept


def test_regional_council_repairs_invalid_input():
    bowtie = Polygon([(0, 0), (1000, 1000), (1000, 0), (0, 1000)])  # self-intersecting, as in the source layers
    geom = build_regional_council(gpd.GeoSeries([bowtie], crs=ITM), gpd.GeoSeries([], crs=ITM), None)
    assert geom.is_valid and geom.area == pytest.approx(500_000, rel=0.01)


def test_clip_overlaps_removes_occupied_area():
    gdf = gpd.GeoDataFrame({"MUN_HEB": ["א"]}, geometry=[box(0, 0, 100, 100)], crs=ITM)
    out = clip_overlaps(gdf, box(50, 0, 100, 100))
    assert out.geometry.iloc[0].area == pytest.approx(5000)


def test_points_inside_reports_only_covered_points():
    gdf = gpd.GeoDataFrame({"MUN_HEB": ["א"]}, geometry=[box(35.0, 31.0, 35.1, 31.1)], crs=4326)
    assert points_inside(gdf, {"in": (31.05, 35.05), "out": (31.5, 35.5)}) == ["in"]


def test_council_overlap_goes_to_council_with_settlements_inside():
    from src.graph.boundaries import resolve_council_overlaps
    out = resolve_council_overlaps({1: box(0, 0, 10, 10), 2: box(5, 0, 15, 10)},
                                   {1: box(6, 1, 8, 3), 2: box(14, 0, 15, 1)})
    assert out[1].area == pytest.approx(100) and out[2].area == pytest.approx(50)
    assert out[1].intersection(out[2]).area == pytest.approx(0)


def test_council_overlap_without_settlements_goes_to_larger_share():
    from src.graph.boundaries import resolve_council_overlaps
    from shapely.geometry import GeometryCollection
    out = resolve_council_overlaps({1: box(0, 0, 10, 10), 2: box(8, 0, 108, 10)},
                                   {1: GeometryCollection(), 2: GeometryCollection()})
    assert out[1].area == pytest.approx(100) and out[2].area == pytest.approx(980)


def test_settlements_stay_with_their_own_council():
    from src.graph.boundaries import resolve_council_overlaps
    out = resolve_council_overlaps({1: box(0, 0, 10, 10), 2: box(5, 0, 15, 10)},
                                   {1: box(6, 1, 8, 3), 2: box(6, 5, 7, 6)})
    assert out[2].contains(box(6, 5, 7, 6).buffer(-0.01))
    assert out[1].intersection(box(6, 5, 7, 6)).area == pytest.approx(0)
    assert out[1].intersection(out[2]).area == pytest.approx(0)
