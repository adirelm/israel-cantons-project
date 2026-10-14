# Israel Cantons Project

Dividing Israel into politically homogeneous cantons based on Knesset election results using spatially-constrained clustering.

**Public map (Hebrew/English):** https://adirelm.github.io/israel-cantons-project/

**Research app:** https://israel-cantons-project-5j7kgq8acxrbiflraqnhgb.streamlit.app/

**Paper:** [arXiv:2603.11805](https://arxiv.org/abs/2603.11805)

## Project Overview

This M.Sc. project develops a data-driven algorithmic approach to partition Israeli municipalities into "cantons" of neighbouring municipalities that maximize internal political similarity. The system uses town-level election results from the five most recent Knesset elections (2019-2022) combined with municipal boundary data.

**Author:** Adir Elmakais — M.Sc. Computer Science, Bar-Ilan University
**Advisor:** Dr. Oren Glickman
**In collaboration with:** Prof. Julia Elad-Strenger, Bundeswehr University Munich

## Directory Structure

```
israel-cantons-project/
├── data/
│   ├── raw/                 # Original downloaded data
│   │   ├── elections/       # Election CSV/Excel files
│   │   └── geo/             # Shapefiles, GeoJSON
│   └── processed/           # Cleaned and integrated datasets
├── src/
│   ├── config.py            # Project paths, constants
│   ├── data/                # Data loading, processing, representations
│   ├── clustering/          # SA, Agglomerative, Louvain, KMeans (baseline)
│   ├── graph/               # Contiguity graph construction & preprocessing
│   ├── evaluation/          # Metrics, stability analysis, experiments
│   └── visualization/       # Maps and charts
├── notebooks/               # Jupyter notebooks (01-06)
├── app/                     # Streamlit research application
├── site/                    # Public map page (static; deployed to GitHub Pages)
├── scripts/                 # Standalone analysis scripts
├── tests/                   # Unit tests
├── docs/                    # Final report and documentation
├── requirements.txt
└── README.md
```

## Setup

**Requires Python 3.12+**

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Place raw data files:
   - Election Excel/CSV files in `data/raw/elections/`
   - Geographic shapefiles/GeoJSON in `data/raw/geo/`

## Quick Start

Run the notebooks in order to walk through the pipeline (to regenerate the committed results, see [Regenerating Results](#regenerating-results)):

```bash
jupyter notebook
```

| Notebook | Description |
|----------|-------------|
| `01_data_exploration.ipynb` | Explore raw election and geographic data |
| `02_data_processing.ipynb` | Process elections, match municipalities across 5 elections |
| `03_adjacency_graph.ipynb` | Build municipality adjacency graph from polygons |
| `04_political_features.ipynb` | Build feature representations (BlocShares, PCA, NMF) |
| `05_clustering.ipynb` | Run Simulated Annealing clustering (K=5) as a worked example, evaluate and map |
| `06_experiments.ipynb` | Full 264-configuration experiment grid and stability analysis |

## Running Tests

```bash
pytest tests/ -v
```

## Running the Experiment Grid

The full experiment grid (264 configurations) evaluates:
- **4 representations:** BlocShares, RawParty, PCA_5, NMF_5
- **3 distance metrics:** Euclidean, Cosine, Jensen-Shannon
- **4 algorithms:** Simulated Annealing, Agglomerative, Louvain, KMeans (baseline)
- **6 K values:** 3, 5, 7, 10, 15, 20

## Regenerating Results

The committed results in `data/processed/` and the report figures are produced by these scripts:

```bash
python scripts/build_boundaries.py     # Judea and Samaria polygons (needs data/raw/geo/js/, see data/raw/geo/SOURCES.md)
python scripts/build_graph.py          # adjacency graph and dissolved boundaries
python scripts/rebuild_results.py      # grid, stability, primary map, per-election maps, held-out tests (~40 min)
python scripts/make_report_figures.py  # docs/figures/*.png
python scripts/sa_sensitivity.py       # 30-seed SA sensitivity (~50 min)
python scripts/report_numbers.py       # every number the report and app quote
python scripts/build_site_data.py      # site/data/*.json and site/og.png for the public map page
```

Party classification lives in `data/reference/parties.csv`, including which lists formed the government after each election (`coalition`); run `rebuild_results.py` after changing it. The first two steps are needed only when boundaries change. Pushing `site/` to `main` deploys the public page (`.github/workflows/pages.yml`); to preview it locally, run `python -m http.server --directory site` and open http://localhost:8000. The notebooks document the original exploratory analysis; notebooks 05 and 06 save their outputs under separate names so they do not overwrite the published results.

## Adding an Election (October 2026)

The Central Elections Committee must publish the official results within eight days of the vote (Basic Law: The Knesset, section 11); in 2022 the final count came two days after the vote and the official results on the eighth day. A rehearsal with a copy of the 2022 results as a sixth election ran every step below end to end; only the two checks meant to fail until steps 3 and 6 are done failed. Steps once the results by locality are out:

1. **Results file.** Download the committee's results **by locality** (one row per locality, not per ballot box): `סמל ועדה, שם ישוב, סמל ישוב, בזב, מצביעים, פסולים, כשרים`, then one column per ballot letter. Save it as `data/raw/elections/knesset_26_oct2026.csv`, preferably UTF-8 (ISO-8859-8 and Windows-1255 are also read). Every other column is read as a list, so remove any extra text or count columns.
2. **Config.** Add `26: "knesset_26_oct2026.csv"` to `ELECTION_FILES` and `26: "October 2026"` to `ELECTION_LABELS` in `src/config.py` (the label must end with the year), and the same label to the copy in `app/utils.py`.
3. **Lists.** Add a row per list to `data/reference/parties.csv`: `knesset` 26, `letters` exactly as the column header, names, `bloc`; leave `coalition` empty until a government forms. Add the same letters and blocs to `EXPECTED_MAPPING` in `tests/test_bloc_mapping.py`, which also names any list with 1% or more that has no bloc.
4. **Check the towns.** Localities are matched to municipalities by code through the 2021 `data/raw/localities_bycode.xlsx`, so a locality founded since is dropped, and the analysis keeps only municipalities with votes in every election. Rebuilding prints the graph size: it should still be 255 nodes.
5. **Rebuild** (see Regenerating Results): `rebuild_results.py` (the held-out test becomes "built from 2019–2022, tested on 2026"), `make_report_figures.py`, `report_numbers.py`, `build_site_data.py`. If the cantons change, update `PRIMARY_CANTON_ANCHORS` in `rebuild_results.py` and `CANTON_NAMES_HE` in `build_site_data.py`; tests that pin today's cantons (sizes, names, colours) will point at what changed.
6. **Page text.** Update the years and the number of elections in the description at the top of `site/index.html` (a test checks both); the rest of the page reads them from the data.
7. **Publish.** Push to `main` (GitHub Pages deploys `site/`), then reboot the Streamlit app.
8. **When the government forms,** mark its lists `coalition=yes` in `parties.csv`, name it in `GOVERNMENTS` (`scripts/build_site_data.py`) and `COALITION_GOVERNMENTS` (`app/utils.py`), and rebuild. Until then the page says no government has been formed yet.

## Key Results

- **255 municipalities**, including the 23 Israeli local authorities in Judea and Samaria, partitioned into **5 cantons** (primary result: NMF_5 / Cosine / Louvain)
- Best silhouette score: **0.987** (BlocShares / Cosine / Agglomerative, K=3); primary K=5 partition: **0.142**
- Temporal stability: ARI **0.992** (BlocShares Louvain), **0.954** (Agglomerative), **0.927** (primary partition)
- Held-out test: cantons built from 2019-2021 differ in every bloc's vote share in the 2022 election (44 of 50 comparisons: 10 canton pairs × 5 blocs)
- 264 experiment configurations, 0 failures
- Cantons: METRO Tel Aviv, RIGHT Jerusalem & South, RIGHT North, ARAB, and HAREDI Cities (seven non-contiguous cities)
- Coalition and opposition, as a description of the cantons (never an input): the share of each canton's vote for the lists that formed the government after the election. HAREDI Cities gave 2.1% to the Bennett–Lapid coalition (2021) and 98.5% to the Netanyahu coalition (2022); ARAB 47.7% and 1.6%; METRO Tel Aviv 62.0% and 42.8%. No government was formed after either 2019 election, and after 2020 lists split, so those elections are not characterised.

Results were regenerated in October 2026 after fixing the party-to-bloc mapping, adding the Judea and Samaria authorities and switching the party-level representation to vote shares per list and election (see `CHANGELOG.md`).

## Data Sources

- **Election Data:** Israel Central Bureau of Statistics (CBS), Knesset elections 21-25
- **Geographic Data:** CBS GIS repository, municipal boundary polygons
