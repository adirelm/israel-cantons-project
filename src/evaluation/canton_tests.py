"""Differences between cantons in bloc vote shares, tested on an election the map did not use.

Municipalities are the units. Neighbouring municipalities vote alike, so p-values
are somewhat optimistic; report effect sizes and intervals alongside them.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu


def holm(pvalues: list[float]) -> list[float]:
    """Holm–Bonferroni adjusted p-values, in the input order."""
    m = len(pvalues)
    adjusted = [0.0] * m
    running = 0.0
    for rank, i in enumerate(np.argsort(pvalues)):
        running = max(running, (m - rank) * pvalues[i])
        adjusted[i] = min(1.0, running)
    return adjusted


def bootstrap_diff_ci(a, wa, b, wb, n_boot: int = 10_000, seed: int = 0, level: float = 0.95) -> tuple[float, float, float]:
    """Voter-weighted mean of ``a`` minus that of ``b``, with a percentile bootstrap CI.

    Municipalities are resampled with replacement within each canton.
    """
    a, wa, b, wb = map(np.asarray, (a, wa, b, wb))
    diff = float(np.average(a, weights=wa) - np.average(b, weights=wb))
    rng = np.random.default_rng(seed)
    ia = rng.integers(0, len(a), size=(n_boot, len(a)))
    ib = rng.integers(0, len(b), size=(n_boot, len(b)))
    boots = (a[ia] * wa[ia]).sum(1) / wa[ia].sum(1) - (b[ib] * wb[ib]).sum(1) / wb[ib].sum(1)
    low, high = np.quantile(boots, [(1 - level) / 2, 1 - (1 - level) / 2])
    return diff, float(low), float(high)


def _kruskal(groups: list[np.ndarray]) -> tuple[float, float]:
    if np.ptp(np.concatenate(groups)) == 0:  # every value identical: no evidence of a difference
        return 0.0, 1.0
    h, p = kruskal(*groups)
    return float(h), float(p)


def _mannwhitney(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    if np.ptp(np.r_[a, b]) == 0:
        return float(len(a) * len(b) / 2), 1.0
    u, p = mannwhitneyu(a, b, alternative="two-sided")
    return float(u), float(p)


def canton_tests(
    shares: pd.DataFrame, weights: pd.Series, assignment: dict[str, int], n_boot: int = 10_000, seed: int = 0
) -> pd.DataFrame:
    """Per bloc: Kruskal–Wallis across cantons, then every canton pair (Holm within the bloc).

    Per pair: the voter-weighted difference in share with a bootstrap interval (effect
    size), and a Mann–Whitney test of whether the typical municipality differs (p-value,
    Holm-adjusted across the pairs). They answer different questions and can disagree when
    a few large towns drive the weighted difference.
    """
    munis = [m for m in shares.index if m in assignment]
    canton = pd.Series({m: assignment[m] for m in munis})
    ids = sorted(canton.unique())
    rows = []
    for bloc in shares.columns:
        groups = {c: (shares.loc[canton.index[canton == c], bloc].to_numpy(),
                      weights.loc[canton.index[canton == c]].to_numpy()) for c in ids}
        h, kw_p = _kruskal([v for v, _ in groups.values()])
        eps2 = h / (len(munis) - 1)
        pair_rows = []
        for ca, cb in combinations(ids, 2):
            (va, wa), (vb, wb) = groups[ca], groups[cb]
            u, p = _mannwhitney(va, vb)
            diff, low, high = bootstrap_diff_ci(va, wa, vb, wb, n_boot=n_boot, seed=seed)
            pair_rows.append({"bloc": bloc, "canton_a": ca, "canton_b": cb, "n_a": len(va), "n_b": len(vb),
                              "mean_a": float(np.average(va, weights=wa)), "mean_b": float(np.average(vb, weights=wb)),
                              "diff": diff, "ci_low": low, "ci_high": high, "u_stat": u, "p_raw": p,
                              "kw_h": h, "kw_p": kw_p, "kw_eps2": eps2})
        for r, adj in zip(pair_rows, holm([r["p_raw"] for r in pair_rows])):
            r["p_holm"] = adj
        rows.extend(pair_rows)
    cols = ["bloc", "canton_a", "canton_b", "n_a", "n_b", "mean_a", "mean_b", "diff", "ci_low", "ci_high",
            "u_stat", "p_raw", "p_holm", "kw_h", "kw_p", "kw_eps2"]
    return pd.DataFrame(rows)[cols]
