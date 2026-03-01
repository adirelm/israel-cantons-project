"""About -- project methodology and information."""

import streamlit as st

st.set_page_config(page_title="About", page_icon=":information_source:", layout="wide")

st.title(":information_source: About This Project")

st.markdown("""
## Partitioning Israeli Municipalities into Politically Homogeneous Cantons

**Author:** Adir Elmakais
**Advisor:** Dr. Oren Glickman
**Program:** M.Sc. Computer Science (Project Track), Bar-Ilan University
**Academic Year:** 2025-2026

---

### Motivation

Over the past four years, Israel held five Knesset elections (April 2019, September 2019,
March 2020, March 2021, and November 2022). Public discourse repeatedly invoked the notion of
dividing Israel into separate "cantons" along political lines.

This project applies data-driven computational methods to answer: **if Israel were divided
into politically coherent regions based purely on voting patterns, what would those regions
look like?**

---

### Methodology

#### Data
- **Election data:** Municipality-level results from Knesset elections 21-25 (CBS)
- **Geographic data:** Municipal boundary polygons (CBS GIS)
- **229 municipalities** consistently matchable across all 5 elections

#### Feature Representations
| Representation | Dimensions | Description |
|---|---|---|
| **BlocShares** | 11 | Average + std of 5 political blocs across elections |
| **RawParty** | ~79 | Raw party vote percentages |
| **PCA (5)** | 5 | Principal component analysis on raw party shares |
| **NMF (5)** | 5 | Non-negative matrix factorization on raw party shares |

#### Distance Metrics
- **Euclidean** -- Standard L2 distance
- **Cosine** -- Angular distance (1 - cosine similarity)
- **Jensen-Shannon** -- Information-theoretic divergence for probability distributions

#### Clustering Algorithms
| Algorithm | Type | Contiguity |
|---|---|---|
| **Simulated Annealing** | Metaheuristic | Enforced (swap-based) |
| **Agglomerative** | Hierarchical | Enforced (merge-based) |
| **Louvain** | Community detection | Inherent (graph-based) |
| **KMeans (baseline)** | Centroid-based | None (baseline) |

#### Evaluation
- **Silhouette score** -- Cluster separation quality
- **WCSS** -- Within-cluster sum of squares
- **Population balance** -- Coefficient of variation of canton populations
- **Contiguity** -- Number of disconnected cantons
- **Temporal stability** -- ARI/NMI across independent per-election clusterings

---

### Key Results

- **264 experiment configurations** (4 representations x 3 metrics x 4 algorithms x 6 K values, minus incompatible)
- **Highest silhouette: 0.905** (BlocShares / Cosine / Agglomerative, K=3; contiguity enforced)
- **Temporal stability: ARI up to 1.0** (Louvain), **0.954** (Agglomerative)
- **K=5 identifies five politically coherent cantons:**
  1. CENTER Metro -- secular-center belt from Tel Aviv through the Sharon plain (42.0% Center)
  2. RIGHT South -- southern periphery arc from Jerusalem through the Negev (44.9% Right)
  3. RIGHT North -- mixed northern region including Haifa and the Galilee (38.0% Right)
  4. ARAB Galilee -- Arab-majority municipalities in the Galilee and Triangle (89.9% Arab)
  5. ARAB Periphery -- Bedouin towns in the Negev and central Arab towns (86.1% Arab)

---

### Data Sources

- **Election Data:** Israel Central Elections Committee (Knesset elections 21-25)
- **Geographic Data:** CBS GIS repository, municipal boundary polygons

### References

- Brieden, A. et al. (2017). *Constrained clustering problems*. [arXiv:1703.02867](https://arxiv.org/abs/1703.02867)

---

### Technology Stack

- **Analysis:** Python, pandas, scikit-learn, NetworkX, GeoPandas
- **Visualization:** Matplotlib, Folium (Leaflet.js), Plotly
- **Web App:** Streamlit
- **Deployment:** Streamlit Cloud
""")
