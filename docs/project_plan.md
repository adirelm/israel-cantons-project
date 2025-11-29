# Work Plan for “Divide Israel into Cantons Based on Election Results”

Below is a detailed, end-to-end work plan for the project, structured into phases. You can paste this into an `.md` file and drive the implementation with Claude Code step by step.

---

## Phase 0 – Project Setup and Management (Week 1)

**Goal:** Prepare a clean, maintainable project infrastructure for the entire year.

**Tasks:**

* Create a GitHub repository, e.g.
  `israel-cantons-clustering`.

* Define an initial directory structure, for example:

  ```text
  /data
    /raw
    /processed
  /src
    /data
    /features
    /graph
    /clustering
    /evaluation
    /visualization
  /notebooks
  /reports
  ```

* Set up a development environment:

  * Use `conda` or `venv`.
  * Python 3.11+.
  * Dependencies (initial list):

    * `pandas`, `numpy`
    * `geopandas`, `shapely`
    * `networkx`
    * `scikit-learn`
    * `matplotlib`
    * `folium` (and/or `plotly`, `geoplot` if desired)

* Write a short `README.md` including:

  * One-paragraph description of the project.
  * Instructions for setting up the environment (`requirements.txt` or `environment.yml`).

* Maintain an internal specification / design document (you already have one):

  * Add a **“Project Log”** section where you record major decisions and changes over time.

**How Claude Code helps here:**
Ask Claude to generate a Python project skeleton: directory structure, basic `__init__.py` files, and optionally a `pyproject.toml` or `setup.cfg` if you want.

---

## Phase 1 – Literature, Problem Definition, and Criteria (Weeks 1–2)

**Goal:** Sharpen the conceptual framing and evaluation criteria for the project.

**Tasks:**

* Read:

  * The paper recommended by Oren (Brieden et al., constrained clustering & electoral districts).
  * 2–3 additional short sources on:

    * Spatial clustering.
    * Electoral districting / gerrymandering basics.

* Write notes on:

  * How your project differs from Brieden et al.:

    * They: LP, generalized Voronoi diagrams, hard population balance constraints.
    * You: simpler greedy algorithm, focus on political similarity + contiguity, exploratory rather than optimal.
  * Which **criteria** matter for you:

    * Political homogeneity within a canton.
    * Political distinction between cantons.
    * Spatial contiguity.
    * Optional: minimum population or minimum number of municipalities per canton.

**Deliverables:**

* Updated **“Related Work & Problem Framing”** section in your internal spec.
* A short list of **research questions**, e.g.:

  * How stable are canton boundaries across different elections?
  * How does the number of cantons (K) affect within-canton homogeneity?
  * How sensitive is the partition to representation (parties vs blocs vs reduced dimensions) and distance metric?

---

## Phase 2 – Data Acquisition and Initial EDA (Weeks 2–4)

**Goal:** Download all required data and ensure you can read and explore it.

**Tasks:**

* Download:

  * Town-level election result files for all 5 recent Knesset elections.
  * Municipal boundary polygons (shapefiles / GeoJSON) for Israeli municipalities (CBS or equivalent).

* Implement `src/data/loading.py` with functions like:

  ```python
  def load_election_results(election_id: str) -> pd.DataFrame:
      ...

  def load_municipal_polygons() -> gpd.GeoDataFrame:
      ...
  ```

* Create the first notebook: `notebooks/01_explore_data.ipynb`:

  * Inspect number of municipalities, column names, missing values.
  * Explore vote distributions for some major parties.
  * Roughly inspect geographic data (e.g., plot polygons for a small region).

**Deliverables:**

* Working data loading functions.
* A basic EDA notebook.
* A written list (in your log or spec) of data issues:

  * Inconsistent town names.
  * Missing values.
  * Mismatched IDs.
  * Elections with different party sets, etc.

---

## Phase 3 – Cleaning and Matching Municipalities (Weeks 4–6)

**Goal:** Obtain a clean `GeoDataFrame` where each row is a municipality with both election results and geometry.

**Tasks:**

* Implement `src/data/preprocess.py`:

  ```python
  def normalize_town_names(df: pd.DataFrame) -> pd.DataFrame:
      ...

  def match_elections_to_polygons(
      elections_df: pd.DataFrame,
      polygons_gdf: gpd.GeoDataFrame
  ) -> gpd.GeoDataFrame:
      ...
  ```

* Handle special cases:

  * Municipalities that merged or split between years.
  * Municipalities that appear in election data but not in polygons (and vice versa).
  * Decide how to deal with missing ones (drop, aggregate, or approximate).

* Save cleaned datasets to `data/processed/`, e.g.:

  * `municipal_elections_<election_id>.geojson`

**Deliverables:**

* For each election: a clean `GeoDataFrame` with:

  * Stable municipality identifier.
  * Election results (vote counts per party).
  * Geometry.

---

## Phase 4 – Political Representation and Distance Metrics (Weeks 6–9)

This implements what Oren suggested: “play around with representation and distance”.

**Goal:** Build an abstraction layer that allows you to switch easily between:

* Different municipality representations (feature vectors).
* Different distance metrics between these vectors.

**Tasks:**

* Implement `src/features/representation.py`, defining an interface like:

  ```python
  class Representation:
      def fit(self, df: pd.DataFrame):
          ...

      def transform(self, df: pd.DataFrame) -> np.ndarray:
          ...
  ```

* Implement at least 2–3 concrete representations:

  ```python
  class RawPartyShares(Representation):
      # vote shares for selected parties

  class BlocShares(Representation):
      # manual grouping of parties into blocs (e.g. right / center-left / Haredi / Arab)

  class DimensionalityReductionRep(Representation):
      # e.g., apply PCA to party vote-share vectors → 2–3 dimensions
  ```

* Implement `src/features/distance.py`:

  ```python
  SUPPORTED_METRICS = ["euclidean", "cosine", "jensen_shannon"]

  def compute_distance(x, y, metric: str = "euclidean") -> float:
      ...
  ```

* Ensure that the clustering layer can do **plug-and-play**:

  * Choose a `Representation`.
  * Choose a distance metric.
  * Pass these to the clustering algorithm without rewriting everything.

**Deliverables:**

* A clean API for multiple representations.
* At least 2–3 distance metrics implemented.
* A small notebook comparing distances between a few example municipalities under different metrics (sanity checks).

---

## Phase 5 – Building the Adjacency Graph (Weeks 8–10, Overlapping with Phase 4)

**Goal:** Build a `networkx.Graph` where:

* Nodes = municipalities.
* Edges = municipalities that are neighbors geographically.

**Tasks:**

* Implement `src/graph/build_graph.py`:

  ```python
  def build_adjacency_graph(gdf: gpd.GeoDataFrame) -> nx.Graph:
      ...
  ```

* Define adjacency:

  * Two municipalities are neighbors if their polygons `touch()` (share a border).
  * Alternatively, you can use centroid distance < threshold, but polygon adjacency is preferred.

* Perform sanity checks:

  * Compute the number of connected components.
  * Focus on a small region (e.g., Gush Dan) and verify that neighbors make sense.
  * Confirm that the graph is connected enough to form meaningful cantons.

**Deliverables:**

* An adjacency graph stored as `graphml` or `pickle`, e.g.:

  * `data/processed/adjacency_graph_<election_id>.graphml`
* A notebook `notebooks/02_check_graph.ipynb`:

  * Visualizing a small region with edges drawn.
  * Validating that the neighborhood structure is reasonable.

---

## Phase 6 – Greedy Spatial Clustering Algorithm (Weeks 10–16)

This is the core algorithmic component.

**Goal:** Implement a **Greedy Spatial Clustering** algorithm with a contiguity constraint.

**Tasks:**

* Implement `src/clustering/greedy_spatial.py` with a class like:

  ```python
  class GreedySpatialClustering:
      def __init__(self, graph, features, populations=None,
                   distance_metric="euclidean"):
          ...

      def initialize_clusters(self):
          # start with each municipality as its own cluster
          ...

      def find_best_merge(self):
          # find two adjacent clusters with minimal "merge cost"
          ...

      def merge_clusters(self, c1, c2):
          # update cluster assignment, centroid, etc.
          ...

      def run_until_k(self, k: int) -> dict:
          # return mapping: town_id -> cluster_id
          ...
  ```

* Decide on a **merge cost function**, e.g.:

  * Increase in within-cluster variance in feature space.
  * Weighted by population if available.

* Focus on efficiency:

  * Maintain a priority queue of candidate cluster pairs (adjacent clusters) keyed by merge cost.
  * After merging clusters, update only affected pairs.

* Test on:

  * Toy graphs (synthetic data).
  * A small subset of real data (e.g., 10–20 municipalities) to ensure:

    * Cantons remain connected.
    * Behavior is intuitive.

**Deliverables:**

* A working `GreedySpatialClustering` class.

* Simple tests (can be plain Python functions) such as:

  ```python
  def test_connectivity_after_clustering():
      # ensure each cluster induces a connected subgraph
      ...
  ```

* Basic experiments showing results for a region with small K (e.g., K=3, K=5).

---

## Phase 7 – Baselines and Ablation Experiments (Weeks 16–20)

**Goal:** Provide comparison points so the results of your greedy spatial algorithm are meaningful.

**Tasks:**

* Implement `src/clustering/baselines.py` with functions like:

  ```python
  def run_kmeans(features, k):
      ...

  def run_agglomerative(features, k):
      ...
  ```

* Run these baselines **without spatial constraints**:

  * Clusters may be geographically disjoint – that’s expected.

* Optionally, implement a simple graph-based baseline:

  * For example, a naive BFS/DFS-based region growing:

    * Choose seed nodes,
    * Add neighboring nodes greedily until cluster size targets reached.

* Provide a generic wrapper, e.g.:

  ```python
  def run_clustering(method, graph, features, k, **kwargs):
      ...
  ```

  where `method` can be `"greedy_spatial"`, `"kmeans"`, `"agglomerative"`, etc.

**Deliverables:**

* At least two baseline clustering methods:

  * One non-spatial (e.g., k-means).
  * Optionally one simple graph-based method.
* A unified API so that baselines and your main algorithm can be compared fairly in later experiments.

---

## Phase 8 – Metrics, Experiments, and Analysis (Weeks 20–28)

**Goal:** Show that you are not just running code, but **measuring and analyzing** the results.

**Tasks:**

* Implement `src/evaluation/metrics.py`:

  * **Within-canton homogeneity:**

    * Average / median distance between municipalities within the same canton.
  * **Between-canton separation:**

    * Distances between canton centroids (in feature space).
  * **Stability across elections:**

    * Adjusted Rand Index (ARI) or Jaccard-based metrics comparing cluster assignments across elections.
  * **Contiguity check:**

    * For each canton, verify that the induced subgraph is connected.

* Implement `src/evaluation/experiments.py`:

  * Experiment families:

    * Varying number of cantons (K) (e.g., 3, 5, 7, 10).
    * Different elections (5 election cycles).
    * Different representations (RawPartyShares / BlocShares / DimensionalityReductionRep).
    * Different distance metrics (Euclidean / cosine / Jensen–Shannon).

* Save results:

  * As CSV files summarizing metrics per experimental run.
  * Optionally as config JSONs documenting which parameters were used.

**Deliverables:**

* Tables / plots showing:

  * How within-canton variance changes with (K).
  * How stability changes across elections.
  * How greedy_spatial compares to baselines.
* Clear notes (in your log or draft report) about key observations.

---

## Phase 9 – Visualization and Interactive Tool (Weeks 24–32)

**Goal:** Provide visual and interactive ways to explore the canton partitions.

**Tasks:**

* Implement `src/visualization/maps.py`:

  ```python
  def plot_cantons_static(gdf, assignments, title: str):
      # static maps (matplotlib / geopandas)
      ...

  def plot_cantons_interactive(gdf, assignments, election_id, k):
      # interactive maps (folium / plotly)
      ...
  ```

* Create `notebooks/03_visualize_cantons.ipynb` with a simple “interface” via cells:

  * Select election.
  * Select K.
  * Select representation + metric.
  * Display:

    * Map with cantons colored.
    * Table with canton-level political profiles.

* If you have time and interest (stretch goals):

  * A small API (e.g., FastAPI) exposing:

    * `/api/cantons?election_id=...&k=...`
  * A simple UI (React, or Streamlit for faster prototyping) that consumes this API and shows maps + controls.

**Deliverables:**

* A set of maps for inclusion in the final report.
* An interactive way to demo the results to the advisor (Notebook at minimum, optional web UI).

---

## Phase 10 – Report, Polishing, and Final Delivery (Weeks 32–36)

**Goal:** Turn everything into a polished project, not just ad-hoc notebooks.

**Tasks:**

* Update the **internal specification** to match what you actually implemented:

  * Final algorithmic decisions.
  * Final representations & metrics used.
  * Limitations encountered.

* Write (or scaffold) the final report with chapters such as:

  1. Introduction & Motivation
  2. Data & Representation
  3. Method – Greedy Spatial Clustering
  4. Experiments & Results
  5. Case Studies (e.g., Tel Aviv area, Jerusalem area, Arab-majority regions)
  6. Limitations & Future Work

* Identify 3–5 key insights, for example:

  * Some regions (like Gush Dan) are very stable across elections.
  * Certain “borderline” areas flip canton assignment between elections.
  * Differences between representations/metrics.

* Clean up the codebase:

  * Add docstrings to all public functions/classes.
  * Remove unused files and dead code.
  * Ensure `README.md` explains:

    * How to run a basic experiment.
    * How to generate a map.

**Deliverables:**

* Final report ready (or nearly ready) for submission.
* A clean, well-organized repo that a reviewer can navigate and run.

---

## Working with Claude Code Throughout the Project

At each phase, you can use Claude Code as a “smart co-pilot” guided by this plan:

* At the start of each phase, tell Claude:

  > “According to my work plan, I’m now in Phase X, which focuses on Y. I already have the following code/files… Please help me implement [specific module/class/function] with this API…”

* Always provide:

  * The relevant part of this work plan.
  * The existing code skeleton or interfaces.
  * Clear input/output expectations.

This way, Claude is executing **your** design, not inventing a different project, and you stay aligned with the M.Sc.-level expectations and the advisor’s suggestions.
