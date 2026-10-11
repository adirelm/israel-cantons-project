"""Tests for src.evaluation.canton_tests."""

import numpy as np
import pandas as pd
import pytest

from src.evaluation.canton_tests import bootstrap_diff_ci, canton_tests, holm


def _data(shift: float, n: int = 40, seed: int = 1):
    rng = np.random.default_rng(seed)
    munis = [f"m{i}" for i in range(2 * n)]
    vals = np.r_[rng.normal(40, 5, n), rng.normal(40 + shift, 5, n)]
    shares = pd.DataFrame({"right": vals, "left": 100 - vals}, index=munis)
    assignment = {m: (0 if i < n else 1) for i, m in enumerate(munis)}
    return shares, pd.Series(1000.0, index=munis), assignment


def test_holm_matches_manual_computation():
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_identical_distributions_are_not_significant():
    t = canton_tests(*_data(shift=0.0), n_boot=2000)
    row = t[t.bloc == "right"].iloc[0]
    assert row.p_holm > 0.05 and row.ci_low < 0 < row.ci_high


def test_shifted_distributions_are_significant_and_ci_covers_shift():
    t = canton_tests(*_data(shift=10.0), n_boot=2000)
    row = t[t.bloc == "right"].iloc[0]
    assert row.p_holm < 0.001 and row.kw_p < 0.001
    assert row.ci_low < -10 + 3 and row.ci_high > -10 - 3  # diff = mean_a - mean_b ≈ -10


def test_bootstrap_is_reproducible_and_weighted():
    a, b = np.array([10.0, 20.0]), np.array([0.0, 0.0])
    d, lo, hi = bootstrap_diff_ci(a, np.array([3.0, 1.0]), b, np.array([1.0, 1.0]), n_boot=500, seed=7)
    assert d == pytest.approx(12.5)
    assert (d, lo, hi) == bootstrap_diff_ci(a, np.array([3.0, 1.0]), b, np.array([1.0, 1.0]), n_boot=500, seed=7)


def test_constant_values_do_not_crash():
    shares, w, assignment = _data(shift=0.0)
    shares["right"] = 50.0
    row = canton_tests(shares, w, assignment, n_boot=200).query("bloc == 'right'").iloc[0]
    assert row.p_raw == 1.0 and row.kw_p == 1.0


def test_training_map_ignores_the_test_election():
    """Scrambling the held-out election's party votes must not change the training map."""
    import sys
    sys.path.insert(0, "scripts")
    import rebuild_results as rr
    from src.config import NON_PARTY_COLS
    from src.data.processing import process_all_elections

    elections = process_all_elections()
    reference = dict(pd.read_csv("data/processed/cantons_final.csv").values)
    base = rr.training_map(elections, rr.TRAIN_ELECTIONS, reference)
    scrambled = {k: df.copy() for k, df in elections.items()}
    test_df = scrambled[rr.TEST_ELECTION]
    party_cols = [c for c in test_df.columns if c not in NON_PARTY_COLS and not c.endswith("_pct")]
    test_df[party_cols] = test_df[party_cols].sample(frac=1, random_state=0).to_numpy()
    assert rr.training_map(scrambled, rr.TRAIN_ELECTIONS, reference) == base

