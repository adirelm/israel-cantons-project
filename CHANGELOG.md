# Changelog

## October 2026 — party-by-election representation

Following the advisor's suggestion, the party-level representation no longer averages each ballot letter over the five elections (a letter can belong to different parties: "פה" was Blue and White in 2019-2020 and Yesh Atid in 2021-2022). `RawPartyShares` now has one feature per list and election, for the lists that passed the 3.25% threshold (51 features; the 11, 9, 8, 13 and 10 lists that won seats). NMF_5 and PCA_5 are built on it, so the primary map uses no party-to-bloc grouping; blocs describe the cantons and still define the graph's enclave edges.

- Primary map: only Nahal Sorek moves (METRO Tel Aviv → RIGHT Jerusalem & South); METRO has 52 municipalities, RIGHT Jerusalem & South 61.
- Cross-election stability (ARI) 0.909 → 0.927; silhouette 0.180 → 0.142 (measured in the new feature space, so not directly comparable); administrative-district ARI 0.360 → 0.354.
- Per-election maps: 219 of 255 municipalities never change canton. In 2022 the southern metropolitan area and the coastal plain south of it (28 municipalities) form a separate canton, the seven Haredi cities join the metropolitan canton, and the Arab canton stays whole.
- Held-out tests: still 44 of 50 comparisons (10 canton pairs × 5 blocs) differ; effect sizes ε² 0.35–0.62.
- SA (NMF_5/Cosine, 30 seeds): silhouette -0.104 ± 0.026, CV 0.16. K=6 Louvain: silhouette 0.149, CV 0.90, ARI 0.847 (K=5 kept).
- **Public map page** (`site/`, published on GitHub Pages): Hebrew and English, map of the five cantons, canton cards, town search, a view per election with the towns that moved, links that open a town or canton, and a map image to download. `scripts/build_site_data.py` writes its data from the results.
- **Research app:** pages grouped into Explore and Research with a link to the public map; maps drawn as one simplified layer (the page dropped from about 30 MB to under 3 MB); per-election maps outline the towns that moved; canton profile charts are horizontal so names fit; the Compare Cantons page states each difference in words and charts every pair.
- The app, the README and the report no longer describe every canton as geographically contiguous: only RIGHT North is one piece on the map. ARAB and HAREDI Cities join many towns that share no borders through the enclave edges, Kiryat Shmona and Beit Jann join RIGHT Jerusalem & South, and Daliyat al-Karmel and Isfiya join the metropolitan canton through bridge edges. The report also corrects older statements that Louvain ignores K and that WCSS always falls with K. The app's home page reads its headline numbers from the data.

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
- **App maps and canton profiles:** canton profiles, colors and the "Largest Bloc" column are now voter-weighted, as in the report (towns counted equally made METRO Tel Aviv look Center-led: 41.7 vs 39.4; by voters it is Right 41.1 vs Center 39.0). A canton whose two largest blocs are within 5 points is drawn in a blend of both colors. The primary and per-election maps label cantons by name. The basemap is OpenStreetMap: CARTO basemaps now need an API key and showed "API key required" over the map.

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
