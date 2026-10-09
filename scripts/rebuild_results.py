#!/usr/bin/env python3
"""Rebuild every output that depends on the party-to-bloc mapping.

Run after changing BLOC_MAPPING in src/config.py:

    python scripts/rebuild_results.py

Mirrors notebooks/04_political_features.ipynb and notebooks/06_experiments.ipynb,
then derives the primary K=5 map (NMF_5 / Cosine / Louvain, as reported in the
paper) from the experiment grid. Canton names are carried over from the previous
cantons_labeled.csv by largest overlap.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import logging
from collections import Counter

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd

from src.config import BLOC_COLS, BLOC_MAPPING, DATA_PROCESSED
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
from src.evaluation.metrics import canton_profiles

PRIMARY_CONFIG = "nmf_5__cosine__louvain__k5"
EXPERIMENTS_DIR = DATA_PROCESSED / "experiments"


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

    Canton IDs and names are matched to the previous cantons_labeled.csv by largest
    overlap, so "Canton 1" keeps meaning the same region across rebuilds.
    """
    old_labels = pd.read_csv(DATA_PROCESSED / "cantons_labeled.csv")
    old_canton = dict(zip(old_labels["municipality"], old_labels["canton"]))
    name_of = dict(zip(old_labels["canton"], old_labels["label"]))

    final = pd.read_csv(EXPERIMENTS_DIR / f"{PRIMARY_CONFIG}.csv")
    raw = dict(zip(final["municipality"], final["canton"]))
    match = {}
    for cid in set(raw.values()):
        overlap = Counter(old_canton[m] for m, c in raw.items() if c == cid and m in old_canton)
        match[cid] = overlap.most_common(1)[0][0]
    if len(set(match.values())) != len(match):
        raise ValueError(f"Cantons no longer match the previous map one-to-one: {match}")

    assignment = CantonAssignment({m: match[c] for m, c in raw.items()})
    assignment.to_dataframe().to_csv(DATA_PROCESSED / "cantons_final.csv", index=False, encoding="utf-8")
    canton_profiles(assignment, bloc_features, weights).to_csv(
        DATA_PROCESSED / "cantons_final_stats.csv", index=False, encoding="utf-8"
    )

    labeled = assignment.to_dataframe()
    labeled["label"] = labeled["canton"].map(name_of)
    labeled.to_csv(DATA_PROCESSED / "cantons_labeled.csv", index=False, encoding="utf-8")

    geo = gpd.read_file(DATA_PROCESSED / "municipalities_dissolved.geojson")
    geo["canton"] = geo["MUN_HEB"].map(assignment.assignments)
    geo = geo.dropna(subset=["canton"]).copy()
    geo["canton"] = geo["canton"].astype(int)
    geo.dissolve(by="canton").reset_index().to_file(DATA_PROCESSED / "cantons_final.geojson", driver="GeoJSON")


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
    save_augmented_graph(G_aug)
    run_grid(elections, G_aug, weights)
    run_stability(elections, G_aug)
    save_primary_map(bloc_features, weights)
    print("Done.")


if __name__ == "__main__":
    main()
