#!/usr/bin/env python3
"""Do the camps describe the cantons equally well in every election?

In each election 2019-2026 the lists that won seats are put in camps (the "camp" column of
data/reference/parties.csv): Netanyahu's bloc on election night, the Arab lists, and the rest (change).
Four classifications are compared:
    camps4  Zionist Netanyahu / Zionist change / Haredi (non-Zionist Jews) / Arab
    camps3  Netanyahu / change / Arab
    camps2  Netanyahu / everyone else
    blocs5  the five blocs of the paper (right / Haredi / centre / left / Arab), for reference
each against two maps: the primary map on all six elections, and the map of that election alone
(built as in experiment A: features and links from that election only).
Both readings of the two disputed lists (experiments_2026.DISPUTED) are run.

Run after scripts/experiments_2026.py:

    python scripts/camps_by_election.py

Writes data/processed/experiments_2026/E_*.csv and docs/figures/experiments_2026/E_*.png.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

import experiments_2026 as exp
from src.config import DATA_PROCESSED, KNESSET_IDS
from src.data.processing import process_all_elections
from src.evaluation.per_election import align_to_reference

OUT, FIG, BASELINE = exp.OUT, exp.FIG, exp.BASELINE
ELECTION_HE = {21: "אפריל 2019", 22: "ספטמבר 2019", 23: "מרץ 2020", 24: "מרץ 2021", 25: "נובמבר 2022", 26: "אוקטובר 2026"}
SCHEMES = ["camps4", "camps3", "camps2", "blocs5"]
SCHEME_HE = {"camps4": "ארבעה גושים", "camps3": "שלושה מחנות", "camps2": "שני מחנות", "blocs5": "חמשת הגושים של המאמר"}
VARIANTS = {"main": None, "disputed_in_change": exp.DISPUTED}
CAMP4_ORDER = ["zionist_netanyahu", "non_zionist", "zionist_change", "arab"]
# Checked with the dataviz palette validator (light surface): all checks pass; orange/green is in the 6-8 CVD band,
# so every segment carries a direct label.
CAMP4_COLORS = {"zionist_netanyahu": "#1d4ed8", "non_zionist": "#a855f7", "zionist_change": "#ea580c", "arab": "#16a34a"}
OTHER_COLOR = "#d1d5db"
CAMP4_HE = {"zionist_netanyahu": "ציונים, מחנה נתניהו", "non_zionist": "חרדים", "zionist_change": "ציונים, מחנה השינוי",
            "arab": "ערבים"}


def classifications(election: pd.DataFrame, knesset: int, overrides) -> pd.DataFrame:
    return exp.camp_shares(election, knesset, overrides).join(
        exp.bloc_shares(election, knesset).drop(columns="valid"))


def main() -> None:
    for name in ("Arial.ttf", "Arial Bold.ttf"):
        font_manager.fontManager.addfont(f"/System/Library/Fonts/Supplemental/{name}")
    plt.rcParams.update({"font.family": "Arial"})

    elections = process_all_elections()
    published = dict(pd.read_csv(BASELINE / "cantons_final.csv").values)
    primary = align_to_reference(dict(pd.read_csv(DATA_PROCESSED / "cantons_final.csv").values), published)
    labels = dict(pd.read_csv(BASELINE / "cantons_labeled.csv")[["canton", "label"]].drop_duplicates().values)
    he = {c["en"]: c["he"] for c in json.loads((BASELINE / "cantons.json").read_text(encoding="utf-8"))}
    names = {i: he[labels[i]] for i in labels}
    # Each election alone, as in experiment A: features and links both from that election only
    alone = {k: exp.align_any(exp.cluster(elections, [k]), primary) for k in KNESSET_IDS}
    c = dict(pd.read_csv(OUT / "A_partitions.csv")[["municipality", "c_2026"]].values)
    assert exp.ari(alone[exp.NEW], c) == 1.0, "2026 alone should equal experiment A's map"

    summary, by_canton = [], []
    for variant, overrides in VARIANTS.items():
        for k in KNESSET_IDS:
            camps = classifications(elections[k], k, overrides)
            for map_name, m in (("primary (2019-2026)", primary), ("that election alone", alone[k])):
                for scheme in SCHEMES:
                    summary.append({"variant": variant, "knesset": k, "election": ELECTION_HE[k], "map": map_name,
                                    "scheme": scheme, **exp.camp_match(m, camps, scheme)})
            for scheme in SCHEMES:
                table = exp.crosstab({t: primary[t] for t in camps.index if t in primary}, camps, scheme, names)
                by_canton.append(table.assign(variant=variant, knesset=k, election=ELECTION_HE[k], scheme=scheme))
    summary = pd.DataFrame(summary)
    summary.to_csv(OUT / "E_camps_by_election.csv", index=False, encoding="utf-8")
    by_canton = pd.concat(by_canton, ignore_index=True)
    by_canton.to_csv(OUT / "E_camps_by_canton.csv", index=False, encoding="utf-8")

    main_rows = by_canton.query("variant == 'main' and scheme == 'camps4'")
    draw_camps4_by_canton(main_rows, names, FIG / "E_camps4_by_canton.png")
    draw_match(summary.query("variant == 'main'"), FIG / "E_match_by_election.png")

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 20)
    print(summary.pivot_table(index=["variant", "map", "scheme"], columns="knesset", values="nmi").round(2))
    print(summary.pivot_table(index=["variant", "map", "scheme"], columns="knesset",
                              values="towns_in_their_cantons_leading_camp_pct").round(0))
    print(summary.pivot_table(index=["variant", "map", "scheme"], columns="knesset", values="variance_explained").round(2))
    print(main_rows.pivot_table(index="name", columns="knesset", values="leading_camp", aggfunc="first"))
    print(main_rows.pivot_table(index="name", columns="knesset", values="towns_led_by_it_pct"))


def draw_camps4_by_canton(rows: pd.DataFrame, names: dict[int, str], path: Path) -> None:
    """One panel per canton: the voter-weighted share of each of the four camps, election by election."""
    fig, axes = plt.subplots(3, 2, figsize=(11, 10.5), facecolor="white")
    order = list(ELECTION_HE)
    rtl = [axes[0, 1], axes[0, 0], axes[1, 1], axes[1, 0], axes[2, 1]]  # Hebrew readers start at the top right
    legend_ax = axes[2, 0]
    for ax, canton in zip(rtl, sorted(names)):
        sub = rows[rows["canton"] == canton].set_index("knesset").loc[order]
        y = np.arange(len(order))[::-1]
        left = np.zeros(len(order))
        for camp in CAMP4_ORDER + ["other"]:
            width = (100 - sub[CAMP4_ORDER].sum(axis=1)).clip(lower=0).values if camp == "other" else sub[camp].values
            ax.barh(y, width, left=left, height=0.72, color=OTHER_COLOR if camp == "other" else CAMP4_COLORS[camp],
                    edgecolor="white", linewidth=1.5)
            for yi, l, w in zip(y, left, width):
                if camp != "other" and w >= 7:
                    ax.text(l + w / 2, yi, f"{w:.0f}", ha="center", va="center", fontsize=8.5, color="white", weight="bold")
            left += width
        ax.set_yticks(y, [ELECTION_HE[k] for k in order], fontsize=9)
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"], fontsize=8, color="#6b7280")
        ax.set_title(f"{names[canton]} ({int(sub['towns'].iloc[0])} רשויות)", fontsize=11, weight="bold")
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color("#d1d5db")
        ax.tick_params(axis="y", length=0)
    legend_ax.set_axis_off()
    handles = [matplotlib.patches.Patch(color=CAMP4_COLORS[c], label=CAMP4_HE[c]) for c in CAMP4_ORDER]
    handles.append(matplotlib.patches.Patch(color=OTHER_COLOR, label="רשימות שלא עברו את אחוז החסימה"))
    legend_ax.legend(handles=handles, loc="center", fontsize=10, frameon=False, title="אחוז מהקולות הכשרים",
                     title_fontsize=10, markerfirst=False)
    fig.suptitle("ארבעת הגושים בכל קנטון, בכל מערכת בחירות", fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    print(path)


def draw_match(summary: pd.DataFrame, path: Path) -> None:
    """How well each classification matches the cantons (NMI with each town's leading camp), election by election."""
    colors = {"camps4": "#1d4ed8", "camps3": "#ea580c", "camps2": "#6b7280", "blocs5": "#a855f7"}
    styles = {"camps4": "-", "camps3": "-", "camps2": "--", "blocs5": ":"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), facecolor="white", sharey=True)
    order = list(ELECTION_HE)
    for ax, map_name, title in zip(axes, ("primary (2019-2026)", "that election alone"),
                                   ("המפה הראשית (כל שש מערכות הבחירות)", "המפה של אותה מערכת בחירות לבד")):
        for scheme in SCHEMES:
            s = summary.query("map == @map_name and scheme == @scheme").set_index("knesset").loc[order, "nmi"]
            ax.plot(range(len(order)), s.values, styles[scheme], color=colors[scheme], linewidth=2, marker="o",
                    markersize=5, label=SCHEME_HE[scheme])
        ax.set_xticks(range(len(order)), [ELECTION_HE[k] for k in order], fontsize=8)
        ax.set_title(title, fontsize=11, weight="bold")
        ax.set_ylim(0, 1)
        ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].set_ylabel("NMI: התאמה בין הקנטון לגוש המוביל ברשות", fontsize=9)
    axes[1].legend(fontsize=9, frameon=False, loc="upper right", markerfirst=False)
    fig.tight_layout()
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    print(path)


if __name__ == "__main__":
    main()
