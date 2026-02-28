"""Tests for src.data.processing module."""

import numpy as np
import pandas as pd
import pytest

from src.data.processing import (
    get_party_columns,
    standardize_columns,
    add_vote_percentages,
    apply_name_fixes,
)
from src.config import NON_PARTY_COLS, NAME_FIXES


class TestGetPartyColumns:
    def test_excludes_non_party_cols(self):
        df = pd.DataFrame({
            "municipality": ["A"],
            "eligible": [100],
            "voters": [80],
            "invalid": [2],
            "valid": [78],
            "knesset": [21],
            "turnout_pct": [80.0],
            "מחל": [40],
            "פה": [30],
        })
        party_cols = get_party_columns(df)
        assert "מחל" in party_cols
        assert "פה" in party_cols
        for col in NON_PARTY_COLS:
            assert col not in party_cols

    def test_empty_dataframe(self):
        df = pd.DataFrame({"municipality": [], "valid": []})
        party_cols = get_party_columns(df)
        assert party_cols == []


class TestAddVotePercentages:
    def test_percentages_computed(self):
        df = pd.DataFrame({
            "municipality": ["A", "B"],
            "eligible": [100, 200],
            "voters": [80, 160],
            "valid": [78, 156],
            "מחל": [39, 78],
        })
        result = add_vote_percentages(df, ["מחל"])
        assert "מחל_pct" in result.columns
        assert result["מחל_pct"].iloc[0] == pytest.approx(50.0, abs=0.1)

    def test_zero_valid_no_crash(self):
        """Division by zero should produce 0, not NaN or error."""
        df = pd.DataFrame({
            "municipality": ["A"],
            "eligible": [100],
            "voters": [0],
            "valid": [0],
            "מחל": [0],
        })
        result = add_vote_percentages(df, ["מחל"])
        assert result["מחל_pct"].iloc[0] == 0.0

    def test_turnout_pct_computed(self):
        df = pd.DataFrame({
            "municipality": ["A"],
            "eligible": [200],
            "voters": [120],
            "valid": [118],
        })
        result = add_vote_percentages(df, [])
        assert "turnout_pct" in result.columns
        assert result["turnout_pct"].iloc[0] == pytest.approx(60.0, abs=0.1)


class TestApplyNameFixes:
    def test_known_fix_applied(self):
        # Pick the first name fix
        old_name = list(NAME_FIXES.keys())[0]
        new_name = NAME_FIXES[old_name]
        df = pd.DataFrame({"municipality": [old_name, "unchanged"]})
        result = apply_name_fixes(df)
        assert result["municipality"].iloc[0] == new_name
        assert result["municipality"].iloc[1] == "unchanged"

    def test_no_mutation(self):
        df = pd.DataFrame({"municipality": ["test"]})
        result = apply_name_fixes(df)
        # Should return a copy, not mutate
        assert result is not df
