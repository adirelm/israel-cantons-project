# Israel Cantons Project

Dividing Israel into politically homogeneous cantons based on Knesset election results using spatially-constrained clustering.

## Project Overview

This M.Sc. project develops a data-driven algorithmic approach to partition Israeli municipalities into geographically contiguous "cantons" that maximize internal political similarity. The system uses town-level election results from the five most recent Knesset elections (2019-2022) combined with municipal boundary data.

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
│   ├── clustering/          # SA, Agglomerative, Spectral, Louvain
│   ├── graph/               # Contiguity graph construction & preprocessing
│   ├── evaluation/          # Metrics, stability analysis, experiments
│   └── visualization/       # Maps and charts
├── notebooks/               # Jupyter notebooks (01-06)
├── tests/                   # Unit tests
├── docs/                    # Final report and documentation
├── requirements.txt
└── README.md
```

## Setup

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

Run the notebooks in order to reproduce the full pipeline:

```bash
jupyter notebook
```

| Notebook | Description |
|----------|-------------|
| `01_data_exploration.ipynb` | Explore raw election and geographic data |
| `02_data_processing.ipynb` | Process elections, match municipalities across 5 elections |
| `03_adjacency_graph.ipynb` | Build municipality adjacency graph from polygons |
| `04_political_features.ipynb` | Build feature representations (BlocShares, PCA, NMF) |
| `05_clustering.ipynb` | Run Simulated Annealing clustering (K=5), evaluate and map |
| `06_experiments.ipynb` | Full 264-configuration experiment grid and stability analysis |

## Running Tests

```bash
pytest tests/ -v
```

## Running the Experiment Grid

The full experiment grid (264 configurations) is run in `notebooks/06_experiments.ipynb`. It evaluates:
- **4 representations:** BlocShares, RawParty, PCA_5, NMF_5
- **3 distance metrics:** Euclidean, Cosine, Jensen-Shannon
- **4 algorithms:** Simulated Annealing, Agglomerative, Spectral, Louvain
- **6 K values:** 3, 5, 7, 10, 15, 20

Results are saved to `data/processed/experiments/`.

## Key Results

- **229 municipalities** partitioned into **5 cantons** (primary result)
- Best silhouette score: **0.905** (BlocShares / Cosine / Agglomerative, K=3)
- Temporal stability: ARI up to **1.0** (Louvain), **0.954** (Agglomerative)
- 264 experiment configurations, 0 failures
- Cantons align with known political-geographic divisions (Arab sector, periphery Right, coastal Center-Right)

## Data Sources

- **Election Data:** Israel Central Bureau of Statistics (CBS), Knesset elections 21-25
- **Geographic Data:** CBS GIS repository, municipal boundary polygons
