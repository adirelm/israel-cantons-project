#!/usr/bin/env python3
"""Print every number the report, app and paper quote, from data/processed."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from sklearn.metrics import adjusted_rand_score

from src.config import DATA_PROCESSED, NAME_FIXES
from src.data.loader import build_locality_to_municipality_mapping, load_cbs_localities

P = DATA_PROCESSED


def admin_district_ari() -> tuple[float, int]:
    """ARI between the primary map and CBS districts, over every municipality with a district.

    Each municipality takes the most common district among its localities (by locality code;
    notebook 06 looked localities up by name, which dropped every regional council).
    """
    cbs = load_cbs_localities()
    l2m = build_locality_to_municipality_mapping(cbs)
    cbs = cbs.assign(municipality=cbs["סמל יישוב"].map(l2m).replace(NAME_FIXES)).dropna(subset=["municipality"])
    district = cbs.groupby("municipality")["שם מחוז"].agg(lambda s: s.mode().iloc[0])
    canton = dict(pd.read_csv(P / "cantons_final.csv").values)
    munis = sorted(set(canton) & set(district.index))
    return adjusted_rand_score([district[m] for m in munis], [canton[m] for m in munis]), len(munis)


def main() -> None:
    ex = pd.read_csv(P / "experiments" / "experiment_results.csv")
    key = ["repr", "metric", "algo", "k_target"]
    print("== Municipalities:", len(pd.read_csv(P / "political_features.csv")))
    print(pd.read_csv(P / "elections_summary.csv").to_string(index=False))
    print("== Primary configuration (NMF_5 / Cosine / Louvain, K=5)")
    primary = (ex.repr == "nmf_5") & (ex.metric == "cosine") & (ex.algo == "louvain") & (ex.k_target == 5)
    print(ex[primary][key + ["silhouette", "pop_cv"]].to_string(index=False))
    print("== Canton profiles"); print(pd.read_csv(P / "cantons_final_stats.csv").to_string(index=False))
    print("== Labels"); print(pd.read_csv(P / "cantons_labeled.csv").groupby(["canton", "label"]).size().to_string())
    print("== Top 5 silhouette")
    print(ex.sort_values("silhouette", ascending=False)[key + ["silhouette", "pop_cv"]].head(5).to_string(index=False))
    print("== Best per algorithm")
    print(ex.loc[ex.groupby("algo").silhouette.idxmax()][key + ["silhouette", "pop_cv"]].to_string(index=False))
    print("== Stability"); print(pd.read_csv(P / "stability_results.csv").to_string(index=False))
    ari, n = admin_district_ari()
    print(f"== Admin-district ARI: {ari:.3f} over {n} municipalities")
    s = pd.read_csv(P / "sa_seed_sensitivity.csv")
    print("== SA seeds"); print(s[["silhouette", "pop_cv"]].describe().loc[["mean", "std", "min", "max"]].round(3).to_string())
    for name in ("canton_tests.csv", "per_election/per_election_changes.csv"):
        if (P / name).exists():
            print(f"== {name}"); print(pd.read_csv(P / name).head(40).to_string(index=False))


if __name__ == "__main__":
    main()
