# Israel Cantons Project

Dividing Israel into politically homogeneous cantons based on Knesset election results using spatially-constrained clustering.

**Public map (Hebrew/English):** https://adirelm.github.io/israel-cantons-project/

**Research app:** https://israel-cantons-project-5j7kgq8acxrbiflraqnhgb.streamlit.app/

## Project Overview

This M.Sc. project develops a data-driven algorithmic approach to partition Israeli municipalities into "cantons" of neighbouring municipalities that maximize internal political similarity. The system uses town-level election results from the five most recent Knesset elections (2019-2022) combined with municipal boundary data.

**Author:** Adir Elmakais — M.Sc. Computer Science, Bar-Ilan University
**Advisor:** Dr. Oren Glickman

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

Party classification lives in `data/reference/parties.csv`; run `rebuild_results.py` after changing it. The first two steps are needed only when boundaries change. Pushing `site/` to `main` deploys the public page (`.github/workflows/pages.yml`); to preview it locally, run `python -m http.server --directory site` and open http://localhost:8000. The notebooks document the original exploratory analysis; notebooks 05 and 06 save their outputs under separate names so they do not overwrite the published results.

## Key Results

- **255 municipalities**, including the 23 Israeli local authorities in Judea and Samaria, partitioned into **5 cantons** (primary result: NMF_5 / Cosine / Louvain)
- Best silhouette score: **0.987** (BlocShares / Cosine / Agglomerative, K=3); primary K=5 partition: **0.142**
- Temporal stability: ARI **0.992** (BlocShares Louvain), **0.954** (Agglomerative), **0.927** (primary partition)
- Held-out test: cantons built from 2019-2021 differ in every bloc's vote share in the 2022 election (44 of 50 canton pairs)
- 264 experiment configurations, 0 failures
- Cantons: METRO Tel Aviv, RIGHT Jerusalem & South, RIGHT North, ARAB, and HAREDI Cities (seven non-contiguous cities)

Results were regenerated in October 2026 after fixing the party-to-bloc mapping, adding the Judea and Samaria authorities and switching the party-level representation to vote shares per list and election (see `CHANGELOG.md`).

## Data Sources

- **Election Data:** Israel Central Bureau of Statistics (CBS), Knesset elections 21-25
- **Geographic Data:** CBS GIS repository, municipal boundary polygons
