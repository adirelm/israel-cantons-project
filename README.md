# Israel Cantons Project

Dividing Israel into politically homogeneous cantons based on Knesset election results using spatially-constrained clustering.

## Project Overview

This M.Sc. project develops a data-driven algorithmic approach to partition Israeli municipalities into geographically contiguous "cantons" that maximize internal political similarity. The system uses town-level election results from the five most recent Knesset elections (2019-2022) combined with municipal boundary data.

## Directory Structure

```
israel-cantons-project/
├── data/
│   ├── raw/                 # Original downloaded data
│   │   ├── elections/       # Election CSV/Excel files
│   │   └── geo/             # Shapefiles, GeoJSON
│   └── processed/           # Cleaned and integrated datasets
├── src/
│   ├── data/                # Data loading and preprocessing
│   ├── clustering/          # Clustering algorithms
│   ├── graph/               # Contiguity graph construction
│   ├── evaluation/          # Metrics and analysis
│   └── visualization/       # Mapping and plots
├── notebooks/               # Jupyter notebooks for exploration
├── tests/                   # Unit tests
├── docs/                    # Project documentation
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

## Data Sources

- **Election Data:** Israel Central Bureau of Statistics (CBS)
- **Geographic Data:** CBS GIS repository, municipal boundary polygons

## Author

Adir Elmakais - M.Sc. Computer Science, Bar-Ilan University

Advisor: Dr. Oren Glickman
