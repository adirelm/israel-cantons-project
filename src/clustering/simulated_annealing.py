"""Simulated annealing spatial clustering.

Multi-phase hybrid algorithm refactored from notebook 05:
1. Seed-based initialisation (most politically extreme municipality per bloc).
2. Greedy growth with balance constraints.
3. Simulated annealing refinement.
"""

from __future__ import annotations

import math
import random
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.config import BLOC_COLS
from src.clustering.base import CantonAssignment
from src.data.distance_metrics import DistanceMetric


class SimulatedAnnealingClusterer:
    """Multi-phase hybrid clustering with simulated annealing refinement."""

    def __init__(
        self,
        balance_weight: float = 0.4,
        homogeneity_weight: float = 0.4,
        compactness_weight: float = 0.2,
        initial_temp: float = 1.0,
        cooling_rate: float = 0.9995,
        min_temp: float = 0.001,
        max_iterations: int = 50_000,
        random_seed: int | None = None,
    ) -> None:
        self._w_balance = balance_weight
        self._w_homogeneity = homogeneity_weight
        self._w_compactness = compactness_weight
        self._initial_temp = initial_temp
        self._cooling_rate = cooling_rate
        self._min_temp = min_temp
        self._max_iterations = max_iterations
        self._random_seed = random_seed

    @property
    def name(self) -> str:
        return "simulated_annealing"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(
        self,
        features: pd.DataFrame,
        feature_cols: list[str],
        graph: nx.Graph,
        k: int,
        distance_metric: DistanceMetric,
        weights: dict[str, float] | None = None,
        **kwargs: Any,
    ) -> CantonAssignment:
        if self._random_seed is not None:
            random.seed(self._random_seed)
            np.random.seed(self._random_seed)

        feat = features.copy()
        if "municipality" in feat.columns:
            feat = feat.set_index("municipality")

        municipalities = list(feat.index)
        G = graph.subgraph(municipalities).copy()

        if weights is None:
            weights = {m: 1.0 for m in municipalities}

        # Normalise features for cost computation
        scaler = StandardScaler()
        feat_norm = scaler.fit_transform(feat[feature_cols])
        feat_dict = {m: feat_norm[i] for i, m in enumerate(municipalities)}

        ctx = _Context(
            G=G,
            feat=feat,
            feature_cols=feature_cols,
            feat_dict=feat_dict,
            weights=weights,
            k=k,
            w_balance=self._w_balance,
            w_homogeneity=self._w_homogeneity,
            w_compactness=self._w_compactness,
        )

        # Phase 1 — seed-based init
        initial = self._initialize_with_seeds(ctx)

        # Phase 2 — simulated annealing
        final, cost = self._simulated_annealing(ctx, initial)

        # Renumber cantons 0..K-1
        old_ids = sorted(set(final.values()))
        id_map = {old: new for new, old in enumerate(old_ids)}
        final = {m: id_map[c] for m, c in final.items()}

        return CantonAssignment(
            assignments=final,
            metadata={
                "algorithm": self.name,
                "final_cost": cost,
                "k_target": k,
                "k_actual": len(set(final.values())),
            },
        )

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _initialize_with_seeds(self, ctx: _Context) -> dict[str, int]:
        """Seed cantons from the most politically extreme municipalities.

        When K > number of bloc columns, additional seeds are chosen via
        K-means on the feature space to ensure diversity.
        """
        from sklearn.cluster import KMeans as _KMeans

        assignments: dict[str, int] = {}
        canton_id = 0

        # Detect seed columns: prefer *_avg bloc columns
        seed_cols = [f"{b}_avg" for b in BLOC_COLS if f"{b}_avg" in ctx.feat.columns]
        if not seed_cols:
            seed_cols = ctx.feature_cols

        seed_munis: list[str] = []
        for col in seed_cols:
            max_muni = ctx.feat[col].idxmax()
            if max_muni not in seed_munis:
                seed_munis.append(max_muni)

        # If we still need more seeds (K > bloc-based seeds), use K-means
        if len(seed_munis) < ctx.k:
            X = ctx.feat[ctx.feature_cols].values
            munis_list = list(ctx.feat.index)
            km = _KMeans(n_clusters=ctx.k, n_init=10, random_state=42)
            km.fit(X)
            # For each cluster centre, pick the closest municipality not yet a seed
            for center in km.cluster_centers_:
                dists = np.linalg.norm(X - center, axis=1)
                order = np.argsort(dists)
                for idx in order:
                    cand = munis_list[idx]
                    if cand not in seed_munis:
                        seed_munis.append(cand)
                        break
                if len(seed_munis) >= ctx.k:
                    break

        for muni in seed_munis[: ctx.k]:
            assignments[muni] = canton_id
            canton_id += 1

        # Greedy growth
        unassigned = set(ctx.G.nodes()) - set(assignments.keys())
        while unassigned:
            best: tuple[str, int] | None = None
            best_cost = float("inf")

            for muni in list(unassigned):
                adj_cantons = {
                    assignments[n]
                    for n in ctx.G.neighbors(muni)
                    if n in assignments
                }
                if not adj_cantons:
                    continue
                for c in adj_cantons:
                    test = {**assignments, muni: c}
                    cost, _ = _compute_cost(ctx, test)
                    if cost < best_cost:
                        best_cost = cost
                        best = (muni, c)

            if best:
                assignments[best[0]] = best[1]
                unassigned.remove(best[0])
            else:
                # Fallback: assign to nearest feature-space canton
                muni = unassigned.pop()
                min_dist = float("inf")
                nearest_c = 0
                for m, c in assignments.items():
                    d = float(np.linalg.norm(ctx.feat_dict[muni] - ctx.feat_dict[m]))
                    if d < min_dist:
                        min_dist = d
                        nearest_c = c
                assignments[muni] = nearest_c

        return assignments

    # ------------------------------------------------------------------
    # Simulated annealing
    # ------------------------------------------------------------------

    def _simulated_annealing(
        self, ctx: _Context, initial: dict[str, int]
    ) -> tuple[dict[str, int], float]:
        assignments = initial.copy()
        current_cost, _ = _compute_cost(ctx, assignments)
        best = assignments.copy()
        best_cost = current_cost

        temp = self._initial_temp
        iteration = 0

        while temp > self._min_temp and iteration < self._max_iterations:
            boundary = _get_boundary_nodes(ctx, assignments)
            if not boundary:
                break

            node = random.choice(boundary)
            cur_canton = assignments[node]
            neighbor_cantons = {
                assignments[n]
                for n in ctx.G.neighbors(node)
                if n in assignments and assignments[n] != cur_canton
            }
            if not neighbor_cantons:
                iteration += 1
                temp *= self._cooling_rate
                continue

            new_canton = random.choice(list(neighbor_cantons))
            if not _is_valid_move(ctx, assignments, node, new_canton):
                iteration += 1
                temp *= self._cooling_rate
                continue

            assignments[node] = new_canton
            new_cost, _ = _compute_cost(ctx, assignments)
            delta = new_cost - current_cost

            if delta < 0 or random.random() < math.exp(-delta / max(temp, 1e-10)):
                current_cost = new_cost
                if new_cost < best_cost:
                    best_cost = new_cost
                    best = assignments.copy()
            else:
                assignments[node] = cur_canton

            temp *= self._cooling_rate
            iteration += 1

        return best, best_cost


# ======================================================================
# Private helpers (module-level for readability)
# ======================================================================

class _Context:
    """Bundles data needed by SA helpers to avoid long argument lists."""

    __slots__ = (
        "G", "feat", "feature_cols", "feat_dict", "weights",
        "k", "w_balance", "w_homogeneity", "w_compactness",
    )

    def __init__(self, **kwargs: Any) -> None:
        for key, val in kwargs.items():
            setattr(self, key, val)


def _compute_cost(
    ctx: _Context, assignments: dict[str, int]
) -> tuple[float, dict]:
    cantons = set(assignments.values())
    n = len(assignments)

    # 1. Population balance (CV)
    canton_w: dict[int, float] = {c: 0.0 for c in cantons}
    for m, c in assignments.items():
        canton_w[c] += ctx.weights.get(m, 1.0)
    wlist = list(canton_w.values())
    balance_cost = float(np.std(wlist) / max(np.mean(wlist), 1e-10))

    # 2. Homogeneity (within-canton variance)
    homogeneity_cost = 0.0
    for c in cantons:
        members = [m for m, cid in assignments.items() if cid == c]
        if len(members) > 1:
            feats = np.array([ctx.feat_dict[m] for m in members])
            canton_var = float(np.mean(np.var(feats, axis=0)))
            homogeneity_cost += canton_var * len(members) / n

    # 3. Compactness (cut ratio)
    cut = sum(
        1 for u, v in ctx.G.edges()
        if u in assignments and v in assignments and assignments[u] != assignments[v]
    )
    total = sum(
        1 for u, v in ctx.G.edges()
        if u in assignments and v in assignments
    )
    compactness_cost = cut / max(total, 1)

    total_cost = (
        ctx.w_balance * balance_cost
        + ctx.w_homogeneity * homogeneity_cost
        + ctx.w_compactness * compactness_cost
    )
    return total_cost, {
        "balance": balance_cost,
        "homogeneity": homogeneity_cost,
        "compactness": compactness_cost,
        "n_cantons": len(cantons),
    }


def _get_boundary_nodes(
    ctx: _Context, assignments: dict[str, int]
) -> list[str]:
    boundary: set[str] = set()
    for u, v in ctx.G.edges():
        if u in assignments and v in assignments and assignments[u] != assignments[v]:
            boundary.add(u)
            boundary.add(v)
    return list(boundary)


def _is_valid_move(
    ctx: _Context,
    assignments: dict[str, int],
    node: str,
    new_canton: int,
) -> bool:
    old_canton = assignments[node]

    # Must connect to new canton
    if not any(assignments.get(n) == new_canton for n in ctx.G.neighbors(node)):
        return False

    # Old canton must remain connected and non-empty
    old_members = [m for m, c in assignments.items() if c == old_canton and m != node]
    if not old_members:
        return False
    if not nx.is_connected(ctx.G.subgraph(old_members)):
        return False

    return True
