"""The press map's legend and labels come from the page data and the boundary file."""

import json
import sys
from pathlib import Path

import geopandas as gpd

from src.config import DATA_PROCESSED

ROOT = Path(__file__).resolve().parent.parent


def _press():
    sys.path.insert(0, str(ROOT / "scripts"))
    import make_press_map
    return make_press_map


def test_legend_lines_give_size_and_leading_blocs():
    press = _press()
    cantons = {c["en"]: c for c in json.loads((ROOT / "site" / "data" / "cantons.json").read_text(encoding="utf-8"))}
    metro = cantons["METRO Tel Aviv"]
    assert press.canton_line(metro, "en") == \
        f"{metro['towns']} municipalities · Right {metro['blocs'][0]:.0f}% · Center {metro['blocs'][2]:.0f}%"
    assert press.canton_line(cantons["ARAB"], "he").endswith(f"רשימות ערביות {cantons['ARAB']['blocs'][4]:.0f}%")
    assert press.canton_line(cantons["HAREDI Cities"], "en").count("·") == 1  # one bloc over 15%


def test_every_labelled_place_is_in_the_boundary_file():
    press = _press()
    names = set(gpd.read_file(DATA_PROCESSED / "municipalities_dissolved.geojson")["MUN_HEB"])
    for he_name, _, _, side in press.CITIES + press.INSET_LABELS:
        assert he_name in names and side in press.SIDES, he_name
