# Changelog

## October 2026 — Judea and Samaria, per-election maps, held-out tests

### Coverage

- **Judea and Samaria.** The 23 Israeli local authorities there were in the election data but had no polygons. They are added from the CBS 2023 municipal layer (17 cities and local councils) and the Civil Administration's council and settlement-jurisdiction layers (6 regional councils), built by `scripts/build_boundaries.py`; sources and download queries are in `data/raw/geo/SOURCES.md`. Overlapping council areas in the source are resolved by a documented rule; points inside Palestinian cities are checked to fall outside every polygon.
- **Three municipalities inside the Green Line** had never matched the boundary file and were missing: Nof HaGalil (file still named Nazareth Illit), Sdot Dan (file named Emek Lod) and Shibli-Umm al-Ghanam (spelling).
- 229 → 255 municipalities. The adjacency graph keeps every previous edge; Judea and Samaria authorities are adjacent within 100 m, and Ariel and Elkana, which touch nothing within that distance, are joined to their nearest authority (`scripts/build_graph.py`).

### Primary K=5 map

The seven predominantly Haredi cities (Bnei Brak, El'ad, Rekhasim, Kiryat Ye'arim, Modi'in Illit, Beitar Illit, Immanuel) now form a canton of their own, joined by enclave edges rather than shared borders, and the two Arab cantons merge. K=6 was checked and is worse on every measure. Cantons are now named by anchor municipalities (`PRIMARY_CANTON_ANCHORS` in `scripts/rebuild_results.py`).

| Canton | Municipalities | Right / Haredi / Center / Left / Arab (%) |
|---|---|---|
| 0 METRO Tel Aviv | 53 | 41.1 / 7.1 / 39.0 / 10.6 / 1.3 |
| 1 RIGHT Jerusalem & South | 60 | 53.1 / 22.1 / 17.8 / 5.4 / 0.7 |
| 2 RIGHT North | 75 | 44.8 / 7.3 / 30.7 / 9.4 / 6.6 |
| 3 ARAB | 60 | 1.9 / 0.9 / 2.4 / 4.0 / 89.6 |
| 4 HAREDI Cities | 7 | 8.6 / 90.0 / 0.9 / 0.3 / 0.0 |

Silhouette 0.138 → 0.180; cross-election stability (ARI) 0.795 → 0.909; SA 30-seed silhouette -0.035 → 0.136.

### New analyses

- **Per-election maps** (`data/processed/per_election/`, `docs/figures/per_election_maps.png`, app Stability page): the primary configuration on each election alone, matched to the primary map. A canton sharing less than half its members with its match keeps its own number. 220 of 255 municipalities never change canton; in 2022 alone, 18 Arab towns in the Negev and the southern Triangle form a separate canton.
- **Held-out tests** (`data/processed/canton_tests.csv`, app Compare Cantons page): cantons rebuilt from 2019-2021 only and compared on 2022 results (Kruskal-Wallis per bloc; voter-weighted difference with bootstrap interval and Mann-Whitney test per pair, Holm-adjusted). All blocs differ across cantons; 44 of 50 pairs differ.

### Other changes

- **Party table:** the party-to-bloc mapping moved to `data/reference/parties.csv`, with Hebrew and English party names.
- **Citation:** Strenger & Yadid (2014), the first proposal of cantonization in the Israeli press, is cited in the report.
- **Administrative districts:** the comparison now assigns every municipality its most common district by locality code; the earlier name-based lookup matched only cities and local councils (149). ARI 0.360 over all 255.
- **Report:** new sections on Judea and Samaria data (4.2), per-election maps (7.4) and held-out tests (7.5), and case studies for Judea and Samaria and the Haredi cities.

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
