#!/usr/bin/env python3
"""Print-quality map of the five cantons for the press, in Hebrew and English.

Run after scripts/build_site_data.py (it reads the page's canton names, colours and shares):

    python scripts/make_press_map.py

docs/figures/press_map_he.png, press_map_he.pdf   A4 portrait, 300 dpi PNG and vector PDF
docs/figures/press_map_en.png, press_map_en.pdf
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import geopandas as gpd
import matplotlib
import pandas as pd
import shapely

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle

from src.config import DATA_PROCESSED

SITE_DATA = ROOT / "site" / "data"
OUT = ROOT / "docs" / "figures"
SIMPLIFY_M = 20.0  # invisible at A4 size; keeps the PDF small
OUTSIDE_COLOR = "#d4d4d8"  # municipalities without results in every election
INK, SOFT = "#0f172a", "#475569"
FONTS = Path("/System/Library/Fonts/Supplemental")  # Arial has Hebrew and allows embedding

# Places named on the map: (Hebrew name in the data, Hebrew label, English label, side of the dot: w, e, n or s)
CITIES = [
    ("ירושלים", "ירושלים", "Jerusalem", "e"),
    ("תל אביב -יפו", "תל אביב־יפו", "Tel Aviv-Yafo", "w"),
    ("חיפה", "חיפה", "Haifa", "w"),
    ("באר שבע", "באר שבע", "Be'er Sheva", "w"),
    ("נצרת", "נצרת", "Nazareth", "e"),
    ("אילת", "אילת", "Eilat", "w"),
]
# The enlarged centre: Tel Aviv to Jerusalem, where most of the Haredi cities are
INSET_LONLAT = (34.70, 31.64, 35.30, 32.22)
INSET_LABELS = [
    ("בני ברק", "בני ברק", "Bnei Brak", "e"),
    ("אלעד", "אלעד", "El'ad", "e"),
    ("מודיעין עילית", "מודיעין עילית", "Modi'in Illit", "e"),
    ("ביתר עילית", "ביתר עילית", "Beitar Illit", "e"),
    ("עמנואל", "עמנואל", "Immanuel", "e"),
    ("קרית יערים", "קריית יערים", "Kiryat Ye'arim", "w"),
    ("תל אביב -יפו", "תל אביב־יפו", "Tel Aviv-Yafo", "s"),
    ("ירושלים", "ירושלים", "Jerusalem", "n"),
]
# Label offset (points) and alignment for each side of the dot
SIDES = {"w": ((-5, 0), "right", "center"), "e": ((5, 0), "left", "center"),
         "n": ((0, 5), "center", "bottom"), "s": ((0, -5), "center", "top")}
BLOC_NAMES = {
    "he": ["ימין", "חרדים", "מרכז", "שמאל", "רשימות ערביות"],
    "en": ["Right", "Haredi", "Center", "Left", "Arab lists"],
}

TEXT = {
    "he": {
        "title": "ישראל בחמישה קנטונים",
        "subtitle": lambda m: f"{m['towns']} רשויות מקומיות, מקובצות לפי דפוסי ההצבעה בחמש מערכות הבחירות {m['first']}–{m['last']}",
        "legend": "חמשת הקנטונים",
        "towns": "רשויות",
        "outside": "ללא תוצאות בכל מערכות הבחירות",
        "blank": "מחוץ לתחום הרשויות שבניתוח",
        "inset": "מרכז הארץ בהגדלה",
        "note": "קנטון אינו חייב להיות רצף אחד: הערים החרדיות,\nוהיישובים הערביים מהגליל ועד הנגב, מקובצים\nלפי דמיון בהצבעה ולא לפי גבול משותף.",
        "stable": lambda m: f"{m['towns_never_moved']} מתוך {m['towns']} הרשויות נשארות באותו קנטון\nגם כשמחלקים כל מערכת בחירות לבד.",
        "credit": "אדיר אלמקייס וד״ר אורן גליקמן, אוניברסיטת בר־אילן · פרופ׳ יוליה אלעד־שטרנגר, אוניברסיטת הבונדסוור במינכן",
        "sources": "מפה אינטראקטיבית: adirelm.github.io/israel-cantons-project · נתונים: תוצאות הבחירות לכנסת לפי רשות; גבולות: הלמ״ס והמנהל האזרחי",
    },
    "en": {
        "title": "Israel in five cantons",
        "subtitle": lambda m: f"{m['towns']} local authorities, grouped by how they voted in the five elections of {m['first']}–{m['last']}",
        "legend": "The five cantons",
        "towns": "municipalities",
        "outside": "No results in every election",
        "blank": "Outside the municipalities analysed",
        "inset": "The centre, enlarged",
        "note": "A canton need not be one piece: the Haredi cities,\nand the Arab towns from the Galilee to the Negev,\nare grouped by how they vote, not by shared borders.",
        "stable": lambda m: f"{m['towns_never_moved']} of {m['towns']} municipalities stay in the same canton\nwhen each election is divided on its own.",
        "credit": "Adir Elmakais and Dr. Oren Glickman, Bar-Ilan University · Prof. Julia Elad-Strenger, Bundeswehr University Munich",
        "sources": "Interactive map: adirelm.github.io/israel-cantons-project · Data: Knesset election results by local authority; boundaries: CBS and the Civil Administration",
    },
}


def canton_line(canton: dict, lang: str) -> str:
    """Size and leading blocs of a canton: "52 municipalities · Right 41% · Center 39%" (up to two blocs over 15%)."""
    blocs = sorted(zip(canton["blocs"], BLOC_NAMES[lang]), reverse=True)
    leading = [f"{name} {share:.0f}%" for share, name in blocs[:2] if share >= 15]
    return " · ".join([f"{canton['towns']} {TEXT[lang]['towns']}", *leading])


def load() -> tuple[gpd.GeoDataFrame, list[dict], dict]:
    cantons = json.loads((SITE_DATA / "cantons.json").read_text(encoding="utf-8"))
    meta = json.loads((SITE_DATA / "meta.json").read_text(encoding="utf-8"))
    years = [e["en"].split()[-1] for e in meta["elections"].values()]
    meta = {**meta, "first": years[0], "last": years[-1]}
    final = dict(pd.read_csv(DATA_PROCESSED / "cantons_final.csv").values)
    geo = gpd.read_file(DATA_PROCESSED / "municipalities_dissolved.geojson").to_crs(2039)
    geo["geometry"] = gpd.GeoSeries(shapely.coverage_simplify(geo.geometry.values, SIMPLIFY_M), crs=2039)
    colors = {c["id"]: c["color"] for c in cantons}
    geo["canton"] = geo["MUN_HEB"].map(final)
    geo["color"] = geo["canton"].map(colors).fillna(OUTSIDE_COLOR)
    return geo, cantons, meta


def _halo(width: float = 2.5):
    return [pe.withStroke(linewidth=width, foreground="white")]


def _draw(ax, geo: gpd.GeoDataFrame, linewidth: float) -> None:
    geo.plot(ax=ax, color=geo["color"], edgecolor="white", linewidth=linewidth)
    ax.set_axis_off()
    ax.set_aspect("equal")


def _label(ax, geo, names, lang, size):
    for he_name, he, en, side in names:
        point = geo.loc[geo["MUN_HEB"] == he_name, "geometry"].iloc[0].representative_point()
        ax.plot(point.x, point.y, "o", ms=3.2, mfc=INK, mec="white", mew=0.8, zorder=5)
        offset, ha, va = SIDES[side]
        ax.annotate(he if lang == "he" else en, (point.x, point.y), xytext=offset, textcoords="offset points",
                    ha=ha, va=va, fontsize=size, color=INK, weight="bold", path_effects=_halo(), zorder=6)


def render(lang: str, geo: gpd.GeoDataFrame, cantons: list[dict], meta: dict) -> plt.Figure:
    t = TEXT[lang]
    rtl = lang == "he"
    fig = plt.figure(figsize=(8.27, 11.69), facecolor="white")  # A4 portrait
    edge, align = (0.955, "right") if rtl else (0.045, "left")

    fig.text(edge, 0.955, t["title"], ha=align, va="top", fontsize=30, weight="bold", color=INK)
    fig.text(edge, 0.912, t["subtitle"](meta), ha=align, va="top", fontsize=11.5, color=SOFT)

    # The whole country on one side, the legend and the enlarged centre on the other
    map_box = [0.03, 0.075, 0.44, 0.81] if rtl else [0.53, 0.075, 0.44, 0.81]
    col = 0.53 if rtl else 0.045  # text column's left edge
    col_w = 0.425
    ax = fig.add_axes(map_box)
    _draw(ax, geo, 0.18)
    haredi = next(c for c in cantons if c["en"] == "HAREDI Cities")
    for shape in geo.loc[geo["canton"] == haredi["id"], "geometry"]:  # too small to see at country scale
        p = shape.representative_point()
        ax.plot(p.x, p.y, "o", ms=5, mfc=haredi["color"], mec="white", mew=1, zorder=4)
    _label(ax, geo, CITIES, lang, 8.5)

    (x0, y0), (x1, y1) = gpd.GeoSeries(gpd.points_from_xy(INSET_LONLAT[::2], INSET_LONLAT[1::2]), crs=4326) \
        .to_crs(2039).apply(lambda p: (p.x, p.y))
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec=INK, lw=0.9, ls="--", zorder=7))

    # Legend
    tx = col + col_w if rtl else col
    fig.text(tx, 0.865, t["legend"], ha=align, va="top", fontsize=14, weight="bold", color=INK)
    y = 0.825
    for c in cantons:
        sx = col + col_w - 0.032 if rtl else col
        fig.patches.append(Rectangle((sx, y - 0.019), 0.032, 0.022, color=c["color"], transform=fig.transFigure))
        nx = sx - 0.012 if rtl else sx + 0.044
        fig.text(nx, y, c[lang], ha=align, va="top", fontsize=12.5, weight="bold", color=INK)
        fig.text(nx, y - 0.021, canton_line(c, lang), ha=align, va="top", fontsize=9.5, color=SOFT)
        y -= 0.052
    sx = col + col_w - 0.032 if rtl else col
    for i, (key, face) in enumerate((("outside", OUTSIDE_COLOR), ("blank", "white"))):
        yy = y - i * 0.022
        fig.patches.append(Rectangle((sx, yy - 0.012), 0.032, 0.012, fc=face, ec="#cbd5e1", lw=0.6,
                                     transform=fig.transFigure))
        fig.text(sx - 0.012 if rtl else sx + 0.044, yy - 0.006, t[key], ha=align, va="center", fontsize=8.5,
                 color=SOFT)

    # The enlarged centre
    fig.text(tx, 0.512, t["inset"], ha=align, va="bottom", fontsize=11, weight="bold", color=INK)
    inset = fig.add_axes([col, 0.225, col_w, 0.28], anchor="NE" if rtl else "NW")
    _draw(inset, geo, 0.4)
    inset.set_xlim(x0, x1)
    inset.set_ylim(y0, y1)
    inset.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec=INK, lw=0.9, ls="--",
                              transform=inset.transData, clip_on=False))
    _label(inset, geo, INSET_LABELS, lang, 8)

    fig.text(tx, 0.215, t["note"], ha=align, va="top", fontsize=9.5, color=INK, multialignment=align, linespacing=1.4)
    fig.text(tx, 0.145, t["stable"](meta), ha=align, va="top", fontsize=9.5, color=INK, multialignment=align,
             linespacing=1.4)

    fig.add_artist(plt.Line2D([0.045, 0.955], [0.058, 0.058], color="#e2e8f0", lw=0.8, transform=fig.transFigure))
    fig.text(edge, 0.046, t["credit"], ha=align, va="top", fontsize=7.6, color=INK)
    fig.text(edge, 0.03, t["sources"], ha=align, va="top", fontsize=7, color=SOFT)
    return fig


def main(out: Path = OUT) -> None:
    for name in ("Arial.ttf", "Arial Bold.ttf"):
        font_manager.fontManager.addfont(str(FONTS / name))
    plt.rcParams.update({"font.family": "Arial", "pdf.fonttype": 42})
    geo, cantons, meta = load()
    out.mkdir(parents=True, exist_ok=True)
    for lang in ("he", "en"):
        fig = render(lang, geo, cantons, meta)
        for ext, kw in (("png", {"dpi": 300}), ("pdf", {})):
            path = out / f"press_map_{lang}.{ext}"
            fig.savefig(path, facecolor="white", **kw)
            print(f"{path}: {path.stat().st_size / 1e6:.2f} MB")
        plt.close(fig)


if __name__ == "__main__":
    main()
