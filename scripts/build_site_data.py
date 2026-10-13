#!/usr/bin/env python3
"""Data files for the public map page (site/).

Run after scripts/rebuild_results.py:

    python scripts/build_site_data.py

site/data/towns.geojson   one feature per municipality: names, canton, voters, bloc shares
                          (five-election average and per election), canton in each election
site/data/cantons.json    one entry per canton: names, color, towns, voters, bloc shares, largest towns
site/data/meta.json       election labels and the headline numbers quoted on the page
site/og.png               preview image shown when the page is shared (1200 x 630)

Canton colors come from the Streamlit app (app/utils.py), so the page and the app agree.
"""

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

import geopandas as gpd
import pandas as pd
import shapely

import utils as app_utils
from src.config import BLOC_COLS, DATA_PROCESSED, ELECTION_LABELS, KNESSET_IDS
from src.data.processing import process_all_elections
from src.data.representations import BlocShares

SITE = ROOT / "site"
SITE_DATA = SITE / "data"
SIMPLIFY_M = 60.0  # invisible at country zoom; keeps towns.geojson near 1.5 MB
COORDINATE_DECIMALS = 4  # about 10 m

# Hebrew canton names, by the English names in cantons_labeled.csv
CANTON_NAMES_HE = {
    "METRO Tel Aviv": "מטרופולין תל אביב",
    "RIGHT Jerusalem & South": "ימין: ירושלים והדרום",
    "RIGHT North": "ימין: הצפון",
    "ARAB": "הקנטון הערבי",
    "HAREDI Cities": "ערים חרדיות",
}
# Common English names for CBS transliterations readers would not recognise (search finds both)
ENGLISH_DISPLAY = {
    "Yerushalayim (Jerusalem)": "Jerusalem",
    "Tel Aviv - Yafo": "Tel Aviv-Yafo",
    "Rishon Letsiyon": "Rishon LeZion",
    "Hertseliya": "Herzliya",
    "Modi'in - Makabim-Re'ut": "Modi'in-Maccabim-Re'ut",
    "Natsrat (Nazareth)": "Nazareth",
    "Ako (Acre)": "Acre",
    "Kiryat Motskin": "Kiryat Motzkin",
    "Nes Tsiyona": "Ness Ziona",
    "Ma'te Yehuda": "Mateh Yehuda",
    "Giv'atayim": "Givatayim",
    "Um Al-Fahem": "Umm al-Fahm",
}
ELECTION_SHORT = {21: "4/2019", 22: "9/2019", 23: "3/2020", 24: "3/2021", 25: "11/2022"}
ELECTION_LABELS_HE = {21: "אפריל 2019", 22: "ספטמבר 2019", 23: "מרץ 2020", 24: "מרץ 2021", 25: "נובמבר 2022"}
LINKS = {
    "site": "https://adirelm.github.io/israel-cantons-project/",
    "app": "https://israel-cantons-project-5j7kgq8acxrbiflraqnhgb.streamlit.app/",
    "repo": "https://github.com/adirelm/israel-cantons-project",
    "report": "https://github.com/adirelm/israel-cantons-project/blob/main/docs/Elmakais_MSc_Project_2026.pdf",
}


def _round(obj, nd: int):
    if isinstance(obj, (list, tuple)):
        return [_round(x, nd) for x in obj]
    return round(obj, nd) if isinstance(obj, float) else obj


def _shares(row, cols: list[str]) -> list[float]:
    return [round(float(row[c]), 1) for c in cols]


def towns_geojson(final: dict[str, int], features: pd.DataFrame) -> dict:
    geo = gpd.read_file(DATA_PROCESSED / "municipalities_dissolved.geojson")
    geo = geo[geo["MUN_HEB"].isin(final)].to_crs(2039).reset_index(drop=True)
    geo["geometry"] = gpd.GeoSeries(shapely.coverage_simplify(geo.geometry.values, SIMPLIFY_M), crs=2039)
    geo = geo.to_crs(4326)

    elections = process_all_elections()
    per_vote = {k: BlocShares(include_std=False, elections_to_use=[k]).fit_transform(elections).set_index("municipality")
                for k in KNESSET_IDS}
    per_canton = {k: dict(pd.read_csv(DATA_PROCESSED / "per_election" / f"knesset_{k}.csv").values) for k in KNESSET_IDS}
    avg_cols = [f"{b}_avg" for b in BLOC_COLS]

    out = []
    for _, row in geo.sort_values("MUN_HEB").iterrows():
        he = row["MUN_HEB"]
        f = features.loc[he]
        geom = shapely.geometry.mapping(row.geometry)
        out.append({
            "type": "Feature",
            "properties": {
                "he": he,
                "en": ENGLISH_DISPLAY.get(row["MUN_ENG"], row["MUN_ENG"]),
                **({"alt": row["MUN_ENG"]} if row["MUN_ENG"] in ENGLISH_DISPLAY else {}),
                "canton": int(final[he]),
                "voters": int(round(f["avg_votes"])),
                "blocs": _shares(f, avg_cols),
                "votes": {str(k): _shares(per_vote[k].loc[he], avg_cols) for k in KNESSET_IDS},
                "elections": {str(k): int(per_canton[k][he]) for k in KNESSET_IDS},
            },
            "geometry": {"type": geom["type"], "coordinates": _round(geom["coordinates"], COORDINATE_DECIMALS)},
        })
    return {"type": "FeatureCollection", "features": out}


def cantons_json(labeled: pd.DataFrame, features: pd.DataFrame) -> list[dict]:
    stats = pd.read_csv(DATA_PROCESSED / "cantons_final_stats.csv").set_index("canton")
    assignment = labeled[["municipality", "canton"]]
    colors = app_utils.canton_colors(app_utils.canton_profiles(assignment, features.reset_index()))
    names = dict(labeled[["canton", "label"]].drop_duplicates().values)
    geo = gpd.read_file(DATA_PROCESSED / "municipalities_dissolved.geojson")
    eng = dict(zip(geo["MUN_HEB"], geo["MUN_ENG"]))
    out = []
    for cid, row in stats.iterrows():
        members = labeled.loc[labeled["canton"] == cid, "municipality"]
        largest = features.loc[members].sort_values("avg_votes", ascending=False).head(5)
        out.append({
            "id": int(cid),
            "en": names[cid],
            "he": CANTON_NAMES_HE[names[cid]],
            "color": colors[cid],
            "towns": int(row["n_municipalities"]),
            "voters": int(row["total_voters"]),
            "blocs": [float(row[f"{b}_pct"]) for b in BLOC_COLS],
            "largest": [{"he": m, "en": ENGLISH_DISPLAY.get(eng[m], eng[m])} for m in largest.index],
        })
    return out


def meta_json(n_towns: int) -> dict:
    stab = pd.read_csv(DATA_PROCESSED / "stability_results.csv").set_index("config")["mean_ari"]
    changes = pd.read_csv(DATA_PROCESSED / "per_election" / "per_election_changes.csv")
    tests = pd.read_csv(DATA_PROCESSED / "canton_tests.csv")
    return {
        "towns": n_towns,
        "blocs": BLOC_COLS,
        "elections": {str(k): {"en": ELECTION_LABELS[k], "he": ELECTION_LABELS_HE[k], "short": ELECTION_SHORT[k]} for k in KNESSET_IDS},
        "stability_ari": round(float(stab["NMF_5 / Cosine / Louvain"]), 3),
        "towns_never_moved": int((changes["n_differ"] == 0).sum()),
        "heldout": {
            "pairs": len(tests),
            "significant": int((tests["p_holm"] < 0.05).sum()),
            "train": [int(k) for k in str(tests["train_elections"].iloc[0]).split(",")],
            "test": int(tests["test_election"].iloc[0]),
        },
        "links": LINKS,
        "built": date.today().isoformat(),
    }


def og_image(towns: dict, cantons: list[dict], meta: dict, site: Path = SITE) -> None:
    """The preview image social networks show for a shared link."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor="white")
    ax = fig.add_axes([0.02, 0.03, 0.36, 0.94])
    geo = gpd.GeoDataFrame.from_features(towns["features"], crs=4326)
    colors = {c["id"]: c["color"] for c in cantons}
    geo.plot(ax=ax, color=[colors[c] for c in geo["canton"]], edgecolor="white", linewidth=0.15)
    ax.set_axis_off()
    years = [v["en"].split()[-1] for v in meta["elections"].values()]
    fig.text(0.96, 0.82, "ישראל בחמישה קנטונים", ha="right", fontsize=42, weight="bold", color="#0f172a")
    fig.text(0.96, 0.73, f"Israel in five cantons · {meta['towns']} municipalities · "
             f"{len(years)} elections, {years[0]}–{years[-1]}", ha="right", fontsize=15, color="#475569")
    for i, c in enumerate(cantons):
        y = 0.58 - i * 0.085
        fig.patches.append(Rectangle((0.935, y - 0.012), 0.025, 0.045, color=c["color"], transform=fig.transFigure))
        fig.text(0.92, y, c["he"], ha="right", fontsize=21, color="#0f172a")
    fig.savefig(site / "og.png", facecolor="white")
    plt.close(fig)


def main(site: Path = SITE) -> None:
    """Write the page's data files and preview image under ``site`` (tests build into a temporary folder)."""
    (site / "data").mkdir(parents=True, exist_ok=True)
    labeled = pd.read_csv(DATA_PROCESSED / "cantons_labeled.csv")
    final = dict(labeled[["municipality", "canton"]].values)
    features = pd.read_csv(DATA_PROCESSED / "political_features.csv").set_index("municipality")

    towns = towns_geojson(final, features)
    files = {
        "towns.geojson": towns,
        "cantons.json": cantons_json(labeled, features),
        "meta.json": meta_json(len(towns["features"])),
    }
    for name, data in files.items():
        path = site / "data" / name
        path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"{path}: {path.stat().st_size / 1e6:.2f} MB")
    og_image(towns, files["cantons.json"], files["meta.json"], site)
    print(f"{site / 'og.png'}: {(site / 'og.png').stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
