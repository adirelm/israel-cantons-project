#!/usr/bin/env python3
"""The October 2026 election: what changed, and experiments A-D proposed by the advisor (4 Nov 2026).

Run after scripts/rebuild_results.py has rebuilt the results on all six elections:

    python scripts/experiments_2026.py

A  The primary configuration on 2019-2022 (the published map), 2019-2026 and 2026 alone.
B  Do those maps match the camps of 2026, in three classifications?
     camps3: change / Arab / Netanyahu
     camps2: anti-Netanyahu (change and Arab) / Netanyahu
     camps4: Zionist change / Zionist Netanyahu / non-Zionist Jews (Haredi) / Arab
   Camps are the lists that won seats, from the "camp" column of data/reference/parties.csv.
C  2019-2026 with no geographic constraint (Louvain on a similarity graph, and K-means), against B's map.
D  2019-2026 with 3, 4, 5, 6 and 10 cantons, and with stricter or looser links between towns.
Also the questions raised on 4 Nov: turnout (and in Arab towns), the Shas vote, and towns that swung.

Writes data/processed/experiments_2026/*.csv and docs/figures/experiments_2026/*.png.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import geopandas as gpd
import matplotlib
import networkx as nx
import numpy as np
import pandas as pd
import shapely
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

from src.clustering.baseline import KMeansBaselineClusterer
from src.clustering.spectral import LouvainSpatialClusterer
from src.config import BLOC_COLS, DATA_PROCESSED, KNESSET_IDS, PARTIES_CSV
from src.data.distance_metrics import CosineDistance
from src.data.processing import process_all_elections
from src.data.representations import BlocShares, NMFRepresentation, RawPartyShares
from src.evaluation.per_election import align_to_reference
from src.graph.preprocessing import add_bridge_edges, add_virtual_edges_for_isolated, preprocess_graph

OUT = DATA_PROCESSED / "experiments_2026"
FIG = ROOT / "docs" / "figures" / "experiments_2026"
BASELINE = OUT / "baseline_2019_2022"
NEW = 26
EXTRA_COLORS = ["#f59e0b", "#ec4899", "#14b8a6", "#a16207", "#84cc16", "#0ea5e9", "#f43f5e", "#64748b"]
CAMP_NAMES = {
    "camps3": {"change": "מחנה השינוי", "arab": "הערבים", "netanyahu": "מחנה נתניהו"},
    "camps2": {"anti": "נגד נתניהו (כולל ערבים)", "netanyahu": "מחנה נתניהו"},
    "camps4": {"zionist_change": "ציונים בשינוי", "zionist_netanyahu": "ציונים במחנה נתניהו",
               "non_zionist": "יהודים לא ציונים (חרדים)", "arab": "ערבים"},
}


# ---------------------------------------------------------------------------
# Building maps
# ---------------------------------------------------------------------------

def raw_graph(towns: set[str]) -> nx.Graph:
    """Towns that share a border (within 100 m in Judea and Samaria), with no added links."""
    adj = json.loads((DATA_PROCESSED / "adjacency_graph.json").read_text(encoding="utf-8"))
    # Built in the same order as scripts/rebuild_results.py: Louvain's result depends on node order
    G = nx.Graph()
    for node, neighbours in adj.items():
        G.add_node(node)
        for n in neighbours:
            G.add_edge(node, n)
    return G.subgraph(towns).copy()


def link_graph(bloc_features: pd.DataFrame, cols: list[str], mode: str, enclave_threshold: float = 70.0) -> nx.Graph:
    """The graph clustering runs on.

    augmented: shared borders, plus links between towns where the same bloc wins over
               ``enclave_threshold``% (the published method uses 70), plus links that
               connect isolated towns and leftover pieces to their most similar towns
    strict:    shared borders, plus only the links that connect isolated towns and pieces
    """
    feats = bloc_features.set_index("municipality")
    G = raw_graph(set(feats.index))
    if mode == "augmented":
        return preprocess_graph(G, feats, cols, enclave_threshold=enclave_threshold)
    if mode == "strict":
        return add_bridge_edges(add_virtual_edges_for_isolated(G, feats, cols), feats, cols)
    raise ValueError(mode)


def similarity_graph(features: pd.DataFrame, cols: list[str], k: int = 10) -> nx.Graph:
    """No geography at all: each town linked to its ``k`` most similar towns (cosine)."""
    feats = features.set_index("municipality")
    D = CosineDistance().pairwise(feats[cols].values)
    G = nx.Graph()
    G.add_nodes_from(feats.index)
    for i, town in enumerate(feats.index):
        for j in np.argsort(D[i])[1:k + 1]:
            G.add_edge(town, feats.index[j])
    return G


def cluster(elections, use: list[int], k: int = 5, graph: str = "augmented", enclave_threshold: float = 70.0,
            algorithm: str = "louvain") -> dict[str, int]:
    """The primary configuration (NMF_5 / Cosine / Louvain) built from the elections in ``use`` only."""
    blocs = BlocShares(include_std=True, elections_to_use=use)
    bloc_features = blocs.fit_transform(elections)
    weights = dict(zip(bloc_features["municipality"], bloc_features["avg_votes"]))
    nmf = NMFRepresentation(n_components=5, base_repr=RawPartyShares(elections_to_use=use))
    features = nmf.fit_transform(elections)
    if graph == "similarity":
        G = similarity_graph(features, nmf.feature_names)
    else:
        G = link_graph(bloc_features, blocs.feature_names, graph, enclave_threshold)
    clusterer = KMeansBaselineClusterer(random_state=42) if algorithm == "kmeans" else LouvainSpatialClusterer(random_seed=42)
    return clusterer.fit(features=features, feature_cols=nmf.feature_names, graph=G, k=k,
                         distance_metric=CosineDistance(), weights=weights).assignments


def align_any(assignment: dict[str, int], reference: dict[str, int]) -> dict[str, int]:
    """Renumber cantons to match ``reference`` by overlap, for any number of cantons.

    Each canton takes the ID of the reference canton it shares most towns with (one to one, by
    the Hungarian method); cantons left over get new IDs after the reference's.
    """
    from scipy.optimize import linear_sum_assignment

    own, ref = sorted(set(assignment.values())), sorted(set(reference.values()))
    overlap = np.array([[sum(1 for t, c in assignment.items() if c == o and reference.get(t) == r) for r in ref] for o in own])
    rows, cols = linear_sum_assignment(-overlap)
    relabel = {own[r]: ref[c] for r, c in zip(rows, cols)}
    extra = iter(range(max(ref) + 1, max(ref) + 1 + len(own)))
    relabel.update({o: next(extra) for o in own if o not in relabel})
    return {t: relabel[c] for t, c in assignment.items()}


# ---------------------------------------------------------------------------
# Measures
# ---------------------------------------------------------------------------

def ari(a: dict[str, int], b: dict[str, int]) -> float:
    towns = sorted(set(a) & set(b))
    return round(float(adjusted_rand_score([a[t] for t in towns], [b[t] for t in towns])), 3)


def nmi(a: dict[str, int], b: dict) -> float:
    towns = sorted(set(a) & set(b))
    return round(float(normalized_mutual_info_score([a[t] for t in towns], [b[t] for t in towns])), 3)


def explained(assignment: dict[str, int], shares: pd.DataFrame, weights: pd.Series) -> float:
    """Share of the voter-weighted variance in bloc shares between towns that the cantons explain (R²)."""
    towns = [t for t in shares.index if t in assignment]
    X, w = shares.loc[towns].values, weights.loc[towns].values
    labels = np.array([assignment[t] for t in towns])
    total = (w[:, None] * (X - np.average(X, axis=0, weights=w)) ** 2).sum()
    within = sum((w[labels == c, None] * (X[labels == c] - np.average(X[labels == c], axis=0, weights=w[labels == c])) ** 2).sum()
                 for c in np.unique(labels))
    return round(float(1 - within / total), 3)


def pieces(assignment: dict[str, int], G_raw: nx.Graph) -> int:
    """Separate pieces on the map: connected groups of towns in the same canton that share borders."""
    return sum(nx.number_connected_components(G_raw.subgraph([t for t, c in assignment.items() if c == canton]))
               for canton in set(assignment.values()))


def population_cv(assignment: dict[str, int], weights: pd.Series) -> float:
    sizes = pd.Series(weights).groupby(pd.Series(assignment)).sum()
    return round(float(sizes.std(ddof=0) / sizes.mean()), 2)


def describe(name: str, assignment: dict[str, int], reference: dict[str, int], shares, weights, G_raw) -> dict:
    return {"map": name, "cantons": len(set(assignment.values())), "ari_vs_reference": ari(assignment, reference),
            "towns_moved": sum(assignment[t] != reference.get(t) for t in assignment),
            "variance_explained": explained(assignment, shares, weights), "pieces": pieces(assignment, G_raw),
            "population_cv": population_cv(assignment, weights)}


# ---------------------------------------------------------------------------
# Camps of 2026
# ---------------------------------------------------------------------------

def camp_lists() -> dict[str, str]:
    """2026 ballot letters -> camp (change / arab / netanyahu), for the lists that won seats."""
    t = pd.read_csv(PARTIES_CSV, keep_default_na=False)
    t = t[(t["knesset"] == NEW) & (t["camp"] != "")]
    return dict(zip(t["letters"], t["camp"]))


def camp_shares(election: pd.DataFrame) -> pd.DataFrame:
    """Each town's share of the valid vote for each camp, in the three classifications (2026)."""
    lists = camp_lists()
    haredi = set(pd.read_csv(PARTIES_CSV).query("knesset == @NEW and bloc == 'haredi'")["letters"])
    df = election.set_index("municipality")
    pct = lambda letters: df[[l for l in letters if l in df.columns]].sum(axis=1) / df["valid"] * 100
    by = lambda camp: [l for l, c in lists.items() if c == camp]
    out = pd.DataFrame({
        "camps3_change": pct(by("change")), "camps3_arab": pct(by("arab")), "camps3_netanyahu": pct(by("netanyahu")),
    })
    out["camps2_anti"] = out["camps3_change"] + out["camps3_arab"]
    out["camps2_netanyahu"] = out["camps3_netanyahu"]
    out["camps4_zionist_change"] = out["camps3_change"]
    out["camps4_non_zionist"] = pct([l for l in by("netanyahu") if l in haredi])
    out["camps4_zionist_netanyahu"] = out["camps3_netanyahu"] - out["camps4_non_zionist"]
    out["camps4_arab"] = out["camps3_arab"]
    for scheme in CAMP_NAMES:
        cols = [c for c in out.columns if c.startswith(scheme + "_")]
        out[f"{scheme}_leader"] = out[cols].idxmax(axis=1).str.removeprefix(scheme + "_")
    out["valid"] = df["valid"]
    return out.round(2)


def crosstab(assignment: dict[str, int], camps: pd.DataFrame, scheme: str, names: dict[int, str]) -> pd.DataFrame:
    """Per canton: towns, the voter-weighted share of each camp, and the share of towns led by its leading camp."""
    cols = [c for c in camps.columns if c.startswith(scheme + "_") and not c.endswith("_leader")]
    rows = []
    for canton in sorted(set(assignment.values())):
        towns = [t for t, c in assignment.items() if c == canton]
        sub = camps.loc[towns]
        share = (sub[cols].mul(sub["valid"], axis=0).sum() / sub["valid"].sum()).round(1)
        top = share.idxmax().removeprefix(scheme + "_")
        rows.append({"canton": canton, "name": names.get(canton, f"קנטון {canton}"), "towns": len(towns),
                     **{c.removeprefix(scheme + "_"): v for c, v in share.items()},
                     "leading_camp": top, "towns_led_by_it_pct": round(float((sub[f"{scheme}_leader"] == top).mean() * 100), 1)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Maps
# ---------------------------------------------------------------------------

def load_geo() -> gpd.GeoDataFrame:
    geo = gpd.read_file(DATA_PROCESSED / "municipalities_dissolved.geojson").to_crs(2039)
    geo["geometry"] = gpd.GeoSeries(shapely.coverage_simplify(geo.geometry.values, 60.0), crs=2039)
    return geo


def colour(canton: int, palette: dict[int, str]) -> str:
    return palette.get(canton, EXTRA_COLORS[(canton - len(palette)) % len(EXTRA_COLORS)])


def draw_maps(geo, panels: list[tuple[str, dict]], palette: dict[int, str], path: Path, legend=None) -> None:
    fig, axes = plt.subplots(1, len(panels), figsize=(3.2 * len(panels), 8.2), facecolor="white")
    for ax, (title, assignment) in zip(np.atleast_1d(axes), panels):
        g = geo.assign(c=geo["MUN_HEB"].map(assignment))
        g[g["c"].isna()].plot(ax=ax, color="#e5e7eb", edgecolor="white", linewidth=0.1)
        g = g.dropna(subset=["c"])
        g.plot(ax=ax, color=[colour(int(c), palette) for c in g["c"]], edgecolor="white", linewidth=0.12)
        ax.set_title(title, fontsize=11, weight="bold")
        ax.set_axis_off()
    if legend:
        fig.legend(handles=[matplotlib.patches.Patch(color=c, label=l) for l, c in legend], loc="lower center",
                   ncol=min(len(legend), 5), fontsize=9, frameon=False)
    fig.tight_layout(rect=(0, 0.06 if legend else 0, 1, 0.97))
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    print(path)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def main() -> None:
    for name in ("Arial.ttf", "Arial Bold.ttf"):
        font_manager.fontManager.addfont(f"/System/Library/Fonts/Supplemental/{name}")
    plt.rcParams.update({"font.family": "Arial"})
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

    elections = process_all_elections()
    towns = set(elections[NEW]["municipality"])
    G_raw = raw_graph(towns)
    all_blocs = BlocShares(include_std=False).fit_transform(elections).set_index("municipality")
    shares = all_blocs[[f"{b}_avg" for b in BLOC_COLS]]
    weights = all_blocs["avg_votes"]

    published = dict(pd.read_csv(BASELINE / "cantons_final.csv").values)
    published_names = dict(pd.read_csv(BASELINE / "cantons_labeled.csv")[["canton", "label"]].drop_duplicates().values)
    current = dict(pd.read_csv(DATA_PROCESSED / "cantons_final.csv").values)
    cantons = json.loads((BASELINE / "cantons.json").read_text(encoding="utf-8"))  # names and colours of the published map
    palette = {c["id"]: c["color"] for c in cantons}
    he_names = {c["en"]: c["he"] for c in cantons}

    # A: the same method on 2019-2022, 2019-2026 and 2026 alone ------------------------------
    a = published
    b = align_to_reference(current, a)
    rebuilt = align_to_reference(cluster(elections, KNESSET_IDS), a)
    assert ari(b, rebuilt) == 1.0, "the rebuilt primary map should equal a fresh run on all six elections"
    c = align_to_reference(cluster(elections, [NEW]), a)
    partitions = pd.DataFrame({"municipality": sorted(towns)})
    for col, m in (("a_2019_2022", a), ("b_2019_2026", b), ("c_2026", c)):
        partitions[col] = partitions["municipality"].map(m)
    partitions.to_csv(OUT / "A_partitions.csv", index=False, encoding="utf-8")
    pd.DataFrame([
        describe("a: 2019-2022 (published)", a, a, shares, weights, G_raw),
        describe("b: 2019-2026", b, a, shares, weights, G_raw),
        describe("c: 2026 alone", c, a, shares, weights, G_raw),
    ]).assign(ari_vs_c=[ari(a, c), ari(b, c), 1.0]).to_csv(OUT / "A_summary.csv", index=False)
    moved = partitions[(partitions["b_2019_2026"] != partitions["a_2019_2022"]) | (partitions["c_2026"] != partitions["a_2019_2022"])]
    moved.assign(**{f"{col}_name": moved[col].map(lambda x: he_names.get(published_names.get(x), f"ללא מקבילה ({x})"))
                    for col in ("a_2019_2022", "b_2019_2026", "c_2026")}).to_csv(OUT / "A_moved.csv", index=False, encoding="utf-8")
    legend = [(he_names[published_names[i]], palette[i]) for i in sorted(palette)]
    draw_maps(load_geo(), [("2019–2022 (המפה שפורסמה)", a), ("2019–2026", b), ("2026 לבד", c)], palette,
              FIG / "A_maps.png", legend + ([("קנטון ללא מקבילה", EXTRA_COLORS[0])] if max(c.values()) >= len(palette) else []))

    # Questions of 4 Nov: turnout, Shas, swings (in the published cantons, so the same areas are compared)
    rows = []
    for k in (25, NEW):
        e = elections[k].set_index("municipality")
        e = e.assign(canton=e.index.map(a))
        for cid, g in list(e.groupby("canton")) + [(-1, e)]:
            rows.append({"knesset": k, "canton": cid, "name": "כל הרשויות" if cid == -1 else he_names[published_names[cid]],
                         "turnout": round(float(g["voters"].sum() / g["eligible"].sum() * 100), 1),
                         "shas": round(float(g["שס"].sum() / g["valid"].sum() * 100), 1)})
    trends = pd.DataFrame(rows).pivot_table(index=["canton", "name"], columns="knesset", values=["turnout", "shas"])
    trends.columns = [f"{m}_{k}" for m, k in trends.columns]
    trends = trends.reset_index()
    trends["turnout_change"] = (trends[f"turnout_{NEW}"] - trends["turnout_25"]).round(1)
    trends["shas_change"] = (trends[f"shas_{NEW}"] - trends["shas_25"]).round(1)
    trends.to_csv(OUT / "turnout_and_shas.csv", index=False, encoding="utf-8")

    camps = camp_shares(elections[NEW])
    camps.to_csv(OUT / "camps_2026_by_town.csv", encoding="utf-8")
    coalition_2022 = pd.read_csv(DATA_PROCESSED / "coalition_shares.csv").query("knesset == 25").set_index("municipality")
    swing = pd.DataFrame({
        "netanyahu_2022": coalition_2022["coalition_pct"].round(1),
        "netanyahu_2026": camps["camps3_netanyahu"].round(1),
        "valid_2026": camps["valid"],
        "canton_2019_2022": pd.Series(a), "canton_2026_alone": pd.Series(c),
    })
    swing["change"] = (swing["netanyahu_2026"] - swing["netanyahu_2022"]).round(1)
    per_election = {k: dict(pd.read_csv(DATA_PROCESSED / "per_election" / f"knesset_{k}.csv").values) for k in KNESSET_IDS}
    for k in KNESSET_IDS:
        swing[f"per_election_{k}"] = pd.Series(align_to_reference(per_election[k], a))
    swing.sort_values("change").to_csv(OUT / "swing_towns.csv", encoding="utf-8")

    # B: maps against the camps of 2026 -------------------------------------------------------
    rows = []
    for map_name, m in (("b: 2019-2026", b), ("c: 2026 alone", c)):
        for scheme in CAMP_NAMES:
            leader = camps[f"{scheme}_leader"].to_dict()
            table = crosstab(m, camps, scheme, {i: he_names.get(published_names.get(i), f"קנטון {i}") for i in set(m.values())})
            table.to_csv(OUT / f"B_{scheme}_{map_name[0]}.csv", index=False, encoding="utf-8")
            rows.append({"map": map_name, "scheme": scheme, "ari": ari(m, leader),
                         "nmi": nmi(m, leader), "towns_in_their_cantons_leading_camp_pct": round(float(
                             sum((table.set_index("canton")["leading_camp"].get(m[t]) == leader[t]) for t in m) / len(m) * 100), 1),
                         "cantons_per_camp": json.dumps(table.groupby("leading_camp")["canton"].count().to_dict())})
    pd.DataFrame(rows).to_csv(OUT / "B_summary.csv", index=False, encoding="utf-8")
    camp_palette = {0: "#2563eb", 1: "#22c55e", 2: "#f97316"}
    camp_ids = {"netanyahu": 0, "arab": 1, "change": 2}
    draw_maps(load_geo(), [("המחנה המוביל ב־2026", {t: camp_ids[v] for t, v in camps["camps3_leader"].items()})], camp_palette,
              FIG / "B_camp_map.png", [(CAMP_NAMES["camps3"][k], camp_palette[v]) for k, v in camp_ids.items()])

    # C: no geographic constraint ------------------------------------------------------------
    free = align_any(cluster(elections, KNESSET_IDS, graph="similarity"), b)
    kmeans = align_any(cluster(elections, KNESSET_IDS, algorithm="kmeans"), b)
    camp_leader = camps["camps3_leader"].to_dict()
    pd.DataFrame([
        describe("b: 2019-2026, with geography", b, b, shares, weights, G_raw) | {"nmi_vs_camps3": nmi(b, camp_leader)},
        describe("no geography: Louvain on a similarity graph", free, b, shares, weights, G_raw) | {"nmi_vs_camps3": nmi(free, camp_leader)},
        describe("no geography: K-means", kmeans, b, shares, weights, G_raw) | {"nmi_vs_camps3": nmi(kmeans, camp_leader)},
    ]).to_csv(OUT / "C_summary.csv", index=False)
    pd.DataFrame({"municipality": sorted(towns)}).assign(
        b=lambda d: d.municipality.map(b), no_geography=lambda d: d.municipality.map(free),
        kmeans=lambda d: d.municipality.map(kmeans)).to_csv(OUT / "C_partitions.csv", index=False, encoding="utf-8")
    profiles = []
    for name, m in (("with geography", b), ("no geography", free)):
        for cid in sorted(set(m.values())):
            members = [t for t, x in m.items() if x == cid]
            w = weights.loc[members]
            profiles.append({"map": name, "canton": cid, "towns": len(members),
                             **{bloc: round(float(np.average(shares.loc[members, f"{bloc}_avg"], weights=w)), 1) for bloc in BLOC_COLS}})
    pd.DataFrame(profiles).to_csv(OUT / "C_profiles.csv", index=False)
    draw_maps(load_geo(), [("2019–2026, עם גאוגרפיה", b), ("2019–2026, בלי גאוגרפיה", free)], palette, FIG / "C_maps.png")

    # D: other numbers of cantons, stricter and looser links ----------------------------------
    rows, panels = [], []
    for k in (3, 4, 5, 6, 10):
        m = align_any(cluster(elections, KNESSET_IDS, k=k), b)
        rows.append(describe(f"K={k}", m, b, shares, weights, G_raw))
        panels.append((f"{k} קנטונים", m))
    draw_maps(load_geo(), panels, palette, FIG / "D_k.png")
    panels = []
    for label, graph, threshold in (("רק גבולות משותפים", "strict", 70.0), ("קישור מעל 70% (הנוכחי)", "augmented", 70.0),
                                    ("קישור מעל 60%", "augmented", 60.0), ("קישור מעל 50%", "augmented", 50.0)):
        m = align_any(cluster(elections, KNESSET_IDS, graph=graph, enclave_threshold=threshold), b)
        rows.append(describe(f"K=5, {graph} {threshold:.0f}", m, b, shares, weights, G_raw))
        panels.append((label, m))
    pd.DataFrame(rows).to_csv(OUT / "D_summary.csv", index=False)
    draw_maps(load_geo(), panels, palette, FIG / "D_links.png")
    print("Done.")


if __name__ == "__main__":
    main()
