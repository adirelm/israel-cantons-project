"""Primary-configuration cantons for each election, aligned to the primary map."""

from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from src.clustering.spectral import LouvainSpatialClusterer
from src.data.distance_metrics import CosineDistance
from src.data.representations import NMFRepresentation
from src.evaluation.stability import cluster_single_election


MIN_JACCARD = 0.5


def align_to_reference(assignment: dict[str, int], reference: dict[str, int]) -> dict[str, int]:
    """Relabel cantons one-to-one so each takes the reference canton it overlaps most.

    A canton whose best one-to-one match shares less than ``MIN_JACCARD`` of their
    combined members gets a new ID above the reference IDs instead, so a region with
    no counterpart in the reference map is not shown under another region's label.
    """
    own_ids = sorted(set(assignment.values()))
    ref_ids = sorted(set(reference.values()))
    if len(own_ids) != len(ref_ids):
        raise ValueError(f"{len(own_ids)} cantons vs {len(ref_ids)} in the reference map")
    overlap = np.zeros((len(own_ids), len(ref_ids)))
    for m in set(assignment) & set(reference):
        overlap[own_ids.index(assignment[m]), ref_ids.index(reference[m])] += 1
    rows, cols = linear_sum_assignment(-overlap)
    relabel, next_id = {}, max(ref_ids) + 1
    for r, c in zip(rows, cols):
        size_own = sum(1 for x in assignment.values() if x == own_ids[r])
        size_ref = sum(1 for x in reference.values() if x == ref_ids[c])
        jaccard = overlap[r, c] / (size_own + size_ref - overlap[r, c])
        if jaccard >= MIN_JACCARD:
            relabel[own_ids[r]] = ref_ids[c]
        else:
            relabel[own_ids[r]] = next_id
            next_id += 1
    return {m: relabel[c] for m, c in assignment.items()}


def per_election_maps(
    elections: dict[int, pd.DataFrame], graph: nx.Graph, reference: dict[str, int], knesset_ids: list[int]
) -> dict[int, dict[str, int]]:
    """Cluster each election alone with the primary configuration; align to ``reference``."""
    maps = {}
    for k in knesset_ids:
        a = cluster_single_election(
            k, elections, NMFRepresentation(n_components=5), CosineDistance(),
            LouvainSpatialClusterer(random_seed=42), graph, len(set(reference.values())),
        )
        maps[k] = align_to_reference(a.assignments, reference)
    return maps


def changes_table(maps: dict[int, dict[str, int]], reference: dict[str, int]) -> pd.DataFrame:
    """One row per municipality: primary canton, canton in each election, elections that differ."""
    t = pd.DataFrame({"municipality": sorted(reference)})
    t["primary"] = t["municipality"].map(reference)
    for k in sorted(maps):
        t[f"knesset_{k}"] = t["municipality"].map(maps[k])
    t["n_differ"] = sum((t[f"knesset_{k}"] != t["primary"]).astype(int) for k in maps)
    return t
