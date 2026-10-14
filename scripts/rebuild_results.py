#!/usr/bin/env python3
"""Rebuild every output that depends on the party-to-bloc mapping.

Run after changing BLOC_MAPPING in src/config.py:

    python scripts/rebuild_results.py

Mirrors notebooks/04_political_features.ipynb and notebooks/06_experiments.ipynb,
then derives the primary K=5 map (NMF_5 / Cosine / Louvain, as reported in the
paper) from the experiment grid. Canton IDs and names are fixed by anchor municipalities
(PRIMARY_CANTON_ANCHORS).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import logging

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd

from src.config import BLOC_COLS, BLOC_MAPPING, DATA_PROCESSED, KNESSET_IDS
from src.data.processing import process_all_elections
from src.data.representations import BlocShares, RawPartyShares, PCARepresentation, NMFRepresentation
from src.data.distance_metrics import EuclideanDistance, CosineDistance, JensenShannonDistance
from src.graph.preprocessing import preprocess_graph
from src.clustering.simulated_annealing import SimulatedAnnealingClusterer
from src.clustering.agglomerative import AgglomerativeSpatialClusterer
from src.clustering.spectral import LouvainSpatialClusterer
from src.clustering.baseline import KMeansBaselineClusterer
from src.clustering.base import CantonAssignment
from src.evaluation.experiment import ExperimentRunner
from src.evaluation.stability import run_stability_analysis
from src.evaluation.canton_names import name_cantons
from src.evaluation.metrics import canton_profiles
from src.evaluation.canton_tests import canton_tests
from src.evaluation.per_election import align_to_reference, changes_table, per_election_maps
from src.data.coalition import canton_coalition, coalition_shares

PRIMARY_CONFIG = "nmf_5__cosine__louvain__k5"
# (anchor municipality, canton ID, name): one anchor per canton of the primary map
PRIMARY_CANTON_ANCHORS = [
    ("תל אביב -יפו", 0, "METRO Tel Aviv"),
    ("ירושלים", 1, "RIGHT Jerusalem & South"),
    ("חיפה", 2, "RIGHT North"),
    ("נצרת", 3, "ARAB"),
    ("בני ברק", 4, "HAREDI Cities"),
]
EXPERIMENTS_DIR = DATA_PROCESSED / "experiments"
TRAIN_ELECTIONS = [21, 22, 23, 24]
TEST_ELECTION = 25


def save_bloc_mappings() -> None:
    with open(DATA_PROCESSED / "bloc_mappings.json", "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in BLOC_MAPPING.items()}, f, ensure_ascii=False, indent=2)


def save_political_features(bloc_features: pd.DataFrame) -> None:
    """Same columns as notebook 04."""
    out = bloc_features.copy()
    out["dominant_bloc"] = out.apply(lambda r: BLOC_COLS[np.argmax([r[f"{b}_avg"] for b in BLOC_COLS])], axis=1)
    out["left_right_score"] = out["right_avg"] - out["left_avg"]
    out["religious_score"] = out["haredi_avg"] + out["arab_avg"] * 0.5
    out.to_csv(DATA_PROCESSED / "political_features.csv", index=False, encoding="utf-8")


def build_graph(bloc_features: pd.DataFrame, feature_cols: list[str]) -> nx.Graph:
    """Contiguity graph augmented from BlocShares features (notebook 06, cell 3)."""
    with open(DATA_PROCESSED / "adjacency_graph.json", "r", encoding="utf-8") as f:
        adj_list = json.load(f)
    G_raw = nx.Graph()
    for node, neighbors in adj_list.items():
        G_raw.add_node(node)
        for n in neighbors:
            G_raw.add_edge(node, n)
    G = G_raw.subgraph(set(bloc_features["municipality"]) & set(G_raw.nodes())).copy()
    return preprocess_graph(G, bloc_features.set_index("municipality"), feature_cols)


def save_matched_elections(elections: dict[int, pd.DataFrame]) -> None:
    """Municipality-level results per election (notebook 02's election_knesset_*_matched.csv)."""
    for k, df in elections.items():
        df.to_csv(DATA_PROCESSED / f"election_knesset_{k}_matched.csv", index=False, encoding="utf-8")


def save_elections_summary(elections: dict[int, pd.DataFrame]) -> None:
    """Per-election totals (notebook 02's elections_summary.csv)."""
    common = set.intersection(*(set(df["municipality"]) for df in elections.values()))
    rows = [{
        "knesset": k,
        "n_municipalities": len(df),
        "n_common": len(common),
        "total_eligible": int(df["eligible"].sum()),
        "total_voters": int(df["voters"].sum()),
        "avg_turnout": round(float(df["turnout_pct"].mean()), 2),
    } for k, df in sorted(elections.items())]
    pd.DataFrame(rows).to_csv(DATA_PROCESSED / "elections_summary.csv", index=False)


def save_augmented_graph(G_aug: nx.Graph) -> None:
    """The augmented graph every clustering run uses, in node-link form."""
    data = {
        "directed": False, "multigraph": False, "graph": {},
        "nodes": [{"id": n} for n in sorted(G_aug.nodes())],
        "edges": [{"source": u, "target": v} for u, v in sorted(G_aug.edges())],
    }
    with open(DATA_PROCESSED / "adjacency_graph_augmented.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def run_grid(elections, G_aug, weights) -> None:
    """Full 264-configuration grid (notebook 06, cells 5-8)."""
    runner = ExperimentRunner(
        representations=[
            BlocShares(include_std=True),
            RawPartyShares(),
            PCARepresentation(n_components=5),
            NMFRepresentation(n_components=5),
        ],
        distance_metrics=[EuclideanDistance(), CosineDistance(), JensenShannonDistance()],
        clusterers=[
            SimulatedAnnealingClusterer(max_iterations=5_000, random_seed=42),
            AgglomerativeSpatialClusterer(linkage="average"),
            LouvainSpatialClusterer(random_seed=42),
            KMeansBaselineClusterer(random_state=42),
        ],
        k_values=[3, 5, 7, 10, 15, 20],
        elections=elections,
        graph=G_aug,
        weights=weights,
    )
    results = runner.run_all(save_dir=EXPERIMENTS_DIR)
    print(f"Grid: {len(results)} configurations, {results['error'].notna().sum()} errors")


def run_stability(elections, G_aug) -> None:
    """Cross-election stability (notebook 06, cell 16)."""
    sa = lambda: SimulatedAnnealingClusterer(max_iterations=2000, random_seed=42)
    configs = [
        ("BlocShares / Euclidean / SA", BlocShares(include_std=False), EuclideanDistance(), sa()),
        ("BlocShares / Cosine / Agglom", BlocShares(include_std=False), CosineDistance(), AgglomerativeSpatialClusterer(linkage="average")),
        ("BlocShares / Euclidean / Louvain", BlocShares(include_std=False), EuclideanDistance(), LouvainSpatialClusterer(random_seed=42)),
        ("NMF_5 / Euclidean / SA", NMFRepresentation(n_components=5), EuclideanDistance(), sa()),
        ("PCA_5 / Euclidean / SA", PCARepresentation(n_components=5), EuclideanDistance(), sa()),
        ("RawParty / Cosine / SA", RawPartyShares(), CosineDistance(), sa()),
        ("NMF_5 / Cosine / Louvain", NMFRepresentation(n_components=5), CosineDistance(), LouvainSpatialClusterer(random_seed=42)),
    ]
    rows = []
    for label, rep, metric, clust in configs:
        _, _, summary = run_stability_analysis(
            elections=elections, representation=rep, distance_metric=metric,
            clusterer=clust, graph=G_aug, k=5,
        )
        rows.append({"config": label, **{k: round(v, 4) for k, v in summary.items()}})
        print(f"Stability {label}: ARI={summary['mean_ari']:.3f}")
    pd.DataFrame(rows).to_csv(DATA_PROCESSED / "stability_results.csv", index=False)


def save_primary_map(bloc_features: pd.DataFrame, weights: dict[str, float]) -> None:
    """cantons_final.* and cantons_labeled.csv from the primary grid configuration.

    Canton IDs and names come from PRIMARY_CANTON_ANCHORS, so the same region keeps
    the same ID and name across rebuilds; the run fails if the anchors no longer
    fall one per canton (the map changed shape and needs new names).
    """
    final = pd.read_csv(EXPERIMENTS_DIR / f"{PRIMARY_CONFIG}.csv")
    assigned, names = name_cantons(dict(zip(final["municipality"], final["canton"])), PRIMARY_CANTON_ANCHORS)
    assignment = CantonAssignment(assigned)
    assignment.to_dataframe().to_csv(DATA_PROCESSED / "cantons_final.csv", index=False, encoding="utf-8")
    canton_profiles(assignment, bloc_features, weights).to_csv(
        DATA_PROCESSED / "cantons_final_stats.csv", index=False, encoding="utf-8"
    )

    labeled = assignment.to_dataframe()
    labeled["label"] = labeled["canton"].map(names)
    labeled.to_csv(DATA_PROCESSED / "cantons_labeled.csv", index=False, encoding="utf-8")

    geo = gpd.read_file(DATA_PROCESSED / "municipalities_dissolved.geojson")
    geo["canton"] = geo["MUN_HEB"].map(assignment.assignments)
    geo = geo.dropna(subset=["canton"]).copy()
    geo["canton"] = geo["canton"].astype(int)
    geo.dissolve(by="canton").reset_index().to_file(DATA_PROCESSED / "cantons_final.geojson", driver="GeoJSON")


def save_per_election_maps(elections, G_aug) -> None:
    """Primary configuration per election, aligned to cantons_final.csv."""
    out_dir = DATA_PROCESSED / "per_election"
    out_dir.mkdir(exist_ok=True)
    reference = dict(pd.read_csv(DATA_PROCESSED / "cantons_final.csv").values)
    maps = per_election_maps(elections, G_aug, reference, KNESSET_IDS)
    for k, assignment in maps.items():
        pd.DataFrame(sorted(assignment.items()), columns=["municipality", "canton"]).to_csv(
            out_dir / f"knesset_{k}.csv", index=False, encoding="utf-8")
    changes_table(maps, reference).to_csv(out_dir / "per_election_changes.csv", index=False, encoding="utf-8")


def training_map(elections, train: list[int], reference: dict[str, int]) -> dict[str, int]:
    """Primary configuration built from ``train`` elections only (features, graph and weights)."""
    rep = BlocShares(include_std=True, elections_to_use=train)
    bf = rep.fit_transform(elections)
    G = build_graph(bf, rep.feature_names)
    weights = dict(zip(bf["municipality"], bf["avg_votes"]))
    nmf = NMFRepresentation(n_components=5, base_repr=RawPartyShares(elections_to_use=train))
    feats = nmf.fit_transform(elections)
    a = LouvainSpatialClusterer(random_seed=42).fit(
        features=feats, feature_cols=nmf.feature_names, graph=G, k=len(set(reference.values())),
        distance_metric=CosineDistance(), weights=weights)
    return align_to_reference(a.assignments, reference)


def save_canton_tests(elections) -> None:
    """Differences between training-map cantons, measured on the held-out election."""
    reference = dict(pd.read_csv(DATA_PROCESSED / "cantons_final.csv").values)
    train = training_map(elections, TRAIN_ELECTIONS, reference)
    pd.DataFrame(sorted(train.items()), columns=["municipality", "canton"]).to_csv(
        DATA_PROCESSED / "cantons_training.csv", index=False, encoding="utf-8")
    test = BlocShares(include_std=False, elections_to_use=[TEST_ELECTION]).fit_transform(elections)
    test = test.set_index("municipality")
    shares = test[[f"{b}_avg" for b in BLOC_COLS]].rename(columns=lambda c: c.removesuffix("_avg"))
    results = canton_tests(shares, test["avg_votes"], train)
    results.insert(0, "train_elections", ",".join(map(str, TRAIN_ELECTIONS)))
    results.insert(1, "test_election", TEST_ELECTION)
    results.to_csv(DATA_PROCESSED / "canton_tests.csv", index=False)


def save_coalition(elections) -> None:
    """Coalition share of each town and primary canton (2021, 2022): a description, not a clustering input."""
    shares = coalition_shares(elections)
    shares.round({"coalition_pct": 2}).to_csv(DATA_PROCESSED / "coalition_shares.csv", index=False, encoding="utf-8")
    final = dict(pd.read_csv(DATA_PROCESSED / "cantons_final.csv").values)
    canton_coalition(shares, final).to_csv(DATA_PROCESSED / "canton_coalition.csv", index=False, encoding="utf-8")


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    elections = process_all_elections()
    bloc_repr = BlocShares(include_std=True)
    bloc_features = bloc_repr.fit_transform(elections)
    weights = dict(zip(bloc_features["municipality"], bloc_features["avg_votes"]))
    G_aug = build_graph(bloc_features, bloc_repr.feature_names)
    print(f"Graph: {G_aug.number_of_nodes()} nodes, {G_aug.number_of_edges()} edges")

    save_bloc_mappings()
    save_political_features(bloc_features)
    save_matched_elections(elections)
    save_elections_summary(elections)
    save_augmented_graph(G_aug)
    run_grid(elections, G_aug, weights)
    run_stability(elections, G_aug)
    save_primary_map(bloc_features, weights)
    save_per_election_maps(elections, G_aug)
    save_canton_tests(elections)
    save_coalition(elections)
    print("Done.")


if __name__ == "__main__":
    main()
