"""Coalition and opposition shares: how much of each town's vote went to the next government.

A description of each election (data/reference/parties.csv, column ``coalition``), not an
input to the cantons.
"""

from __future__ import annotations

import pandas as pd

from src.config import COALITION_LISTS


def coalition_shares(elections: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """One row per municipality and characterised election: coalition_pct and valid votes."""
    rows = []
    for k, lists in sorted(COALITION_LISTS.items()):
        df = elections[k]
        present = [c for c in sorted(lists) if c in df.columns]
        pct = df[present].sum(axis=1) / df["valid"].where(df["valid"] > 0) * 100
        rows.append(pd.DataFrame({"municipality": df["municipality"], "knesset": k,
                                  "coalition_pct": pct.fillna(0.0), "valid": df["valid"]}))
    return pd.concat(rows, ignore_index=True)


def canton_coalition(shares: pd.DataFrame, assignment: dict[str, int]) -> pd.DataFrame:
    """Coalition share of all valid votes in each canton, per characterised election."""
    s = shares[shares["municipality"].isin(assignment)].assign(canton=lambda d: d["municipality"].map(assignment))
    s = s.assign(coalition_votes=s["coalition_pct"] * s["valid"] / 100)
    out = s.groupby(["canton", "knesset"], as_index=False)[["coalition_votes", "valid"]].sum()
    out["coalition_pct"] = (out["coalition_votes"] / out["valid"] * 100).round(1)
    return out[["canton", "knesset", "coalition_pct", "valid"]]
