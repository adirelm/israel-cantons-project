# Changelog

## October 2026 — corrected results

All results in `data/processed/`, the report (`docs/Elmakais_MSc_Project_2026.md` and `.pdf`), the figures and the app were regenerated with `scripts/rebuild_results.py`, `scripts/make_report_figures.py` and `scripts/sa_sensitivity.py`.

### Fixes

- **Party-to-bloc mapping** (`src/config.py`). Three right-wing lists were not assigned to any bloc and were counted as "other":
  - March 2021: Religious Zionist Party (ballot letter Tet, 4.1% of the vote in the 229 municipalities). The 2021 entry assumed Yamina still ran as Tet-Bet; in 2021 Yamina ran as Bet.
  - March 2020: Otzma Yehudit (Nun-Tsadi, 0.4%).
  - November 2022: Jewish Home (Bet, 1.0%).

  `tests/test_bloc_mapping.py` now fails if any list with at least 1% of the vote has no bloc.
- **Simulated Annealing reproducibility** (`src/clustering/simulated_annealing.py`). Moves were drawn from lists built from Python sets of municipality names, whose order changes between processes, so `random_seed` did not fix the result. The lists are now sorted; a test runs the same fit under different hash seeds.
- **`scripts/sa_sensitivity.py`** failed on import after being moved into `scripts/`.

### Results that were out of date

These were already inconsistent with the code before the mapping fix:

- **Silhouette scores** in `experiment_results.csv` were produced before silhouette was computed in each configuration's own metric, so every Cosine and Jensen-Shannon score was really a Euclidean score.
- **Canton profiles** (`cantons_final_stats.csv`, report Table 5) were unweighted means over municipalities. They are now weighted by voters, as `canton_profiles()` computes them.
- **Cross-election stability of the primary partition** was reported as ARI = 1.0, a value measured for a different configuration (BlocShares / Euclidean / Louvain). Measured for NMF_5 / Cosine / Louvain it is 0.795. It is now part of `stability_results.csv`.
- **Comparison with administrative districts** reported ARI = 0.435, computed for an earlier Simulated Annealing map. For the primary partition it is 0.286.

### Effect on the primary K=5 partition (NMF_5 / Cosine / Louvain)

- One municipality changes canton: Kiryat Shmona moves from RIGHT North to RIGHT South, through enclave edges to Sderot and Dimona.
- Silhouette 0.121 → 0.138. The mapping fix alone accounts for 0.121 → 0.123 (both measured the old way, with Euclidean distance); the rest comes from scoring in Cosine distance.
- Canton profiles (Right / Haredi / Center / Left / Arab, %):

  | Canton | Before | After |
  |---|---|---|
  | 0 CENTER Metro | 29.7 / 14.4 / 42.0 / 11.0 / 1.1 | 33.9 / 14.0 / 38.5 / 11.7 / 1.0 |
  | 1 RIGHT South | 44.9 / 10.8 / 30.0 / 10.3 / 1.0 | 49.5 / 17.4 / 24.7 / 6.2 / 1.1 |
  | 2 RIGHT North | 38.0 / 6.9 / 31.2 / 10.9 / 10.4 | 44.6 / 7.5 / 31.1 / 9.5 / 6.2 |
  | 3 ARAB Galilee | 1.9 / 1.1 / 2.2 / 3.8 / 89.9 | 1.9 / 0.9 / 2.1 / 3.4 / 90.6 |
  | 4 ARAB Periphery | 2.2 / 1.0 / 4.3 / 5.0 / 86.1 | 2.0 / 0.7 / 3.6 / 6.0 / 86.1 |

### Other changes

- `scripts/rebuild_results.py` regenerates every output that depends on the bloc mapping and keeps canton IDs and names stable across rebuilds.
- `scripts/make_report_figures.py` regenerates `docs/figures/` (except the static `pipeline.png`).
- `data/processed/cantons_final.geojson` (dissolved canton polygons) and `adjacency_graph_augmented.json` (the graph every clustering run uses) are now regenerated with the results.
- Notebooks 05 and 06 no longer overwrite the published map and canton names when re-run.
