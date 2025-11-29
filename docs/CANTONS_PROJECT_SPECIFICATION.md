# Project Specification: Divide Israel into Cantons Based on Election Results

**Internal Note:** This document is a detailed internal project specification for planning and implementation. A shorter overview document was sent separately. This file will be updated according to feedback and project progress.


## 1. Project Metadata

**Project Title:** Divide Israel into Cantons Based on Election Results

**Advisor:** Dr. Oren Glickman, Department of Computer Science, Bar-Ilan University

**Degree:** M.Sc. in Computer Science (Project Track / Non-Thesis)

**Student:** Adir Elmakais, ID 316413640

**Academic Year:** 2025-2026

**Contact Details:**
- Student Email: adir4455@gmail.com
- Advisor Email: oren.glickman@biu.ac.il
- Department: Computer Science, Bar-Ilan University, Ramat Gan, Israel

---

## 2. Abstract

Israeli society has experienced significant political polarization in recent years, reflected in five parliamentary elections held within a four-year period. Public discourse increasingly references hypothetical divisions of the country into politically homogeneous "cantons" or regions. In this project, I will develop a data-driven algorithmic approach to explore such divisions using publicly available town-level election results and geographic boundary data from the Israel Central Bureau of Statistics. My core methodology employs a spatially-constrained greedy clustering algorithm that partitions Israeli municipalities into geographically contiguous cantons while maximizing internal political similarity. I will build an interactive visualization platform allowing users to explore canton divisions across different election cycles and varying numbers of regions. My key contributions will include: (1) a novel application of constrained clustering to political geography in Israel, (2) methodological insights into balancing geographic contiguity with feature-space similarity, and (3) an analytical tool for examining political-geographic structure and its stability over time. This project bridges computer science, data science, geographic information systems, and political analysis.

---

## 3. Background and Motivation

### Political Context

Over the past four years, Israel has held five Knesset elections (April 2019, September 2019, March 2020, March 2021, and November 2022), reflecting deep political divisions and coalition-building challenges. This unprecedented frequency of elections highlights the polarization in Israeli society across multiple dimensions: secular-religious, left-right ideological spectrum, Arab-Jewish relations, and attitudes toward judicial reform and governance.

Throughout this period, public and media discourse has repeatedly invoked the notion of dividing Israel into separate "cantons" along political lines. Commentators reference distinct political cultures in different geographic areas——for example, contrasting Tel Aviv's liberal-secular majority with Jerusalem's religious-conservative population, or the Arab-majority towns in northern Israel with predominantly Jewish communities elsewhere. While such discourse is largely rhetorical and hypothetical, it raises an interesting computational question that I want to explore: if Israel were to be divided into politically coherent regions based purely on voting patterns, what would those regions look like, and how stable would they be across election cycles?

### Scientific and Technical Motivation

From a computer science and data science perspective, this question presents a compelling problem at the intersection of several research areas that interest me:

1. **Spatial Clustering:** The problem requires clustering municipalities based on political similarity (feature-space distance) while respecting geographic contiguity constraints. This is a challenging variant of clustering where clusters must form connected components in a spatial graph.

2. **Political Geography and Regionalization:** My project connects to established research on electoral geography, regional divisions, and the spatial structure of political preferences. It provides a quantitative, data-driven complement to qualitative political science analyses.

3. **Graph-based Algorithms:** Constructing and clustering on a contiguity graph of municipalities involves graph representation, adjacency detection from geographic polygons, and algorithms that operate on graph topology while optimizing feature-space objectives.

4. **Geospatial Data Processing:** My project involves substantial geographic information systems (GIS) work: handling polygon data, computing spatial relationships, and visualizing results on interactive maps.

5. **Algorithmic Design and Optimization:** I will design an efficient greedy clustering algorithm that balances multiple objectives (political homogeneity, geographic contiguity, canton size constraints), which presents non-trivial algorithmic challenges.

Importantly, this is a **descriptive and analytical project**, not a normative political proposal. My goal is to apply computational methods to understand the political-geographic structure of Israel as revealed through election data, not to advocate for any political outcome. I believe the project's value lies in its methodological contributions to constrained clustering and its provision of analytical tools for exploring electoral geography.

---

## 4. Related Work and Theoretical Foundations

### 4.1 Political Geography and Regionalization

Political geography examines the spatial distribution of political phenomena and the relationship between geographic location and political behavior. Regionalization—the process of dividing a territory into coherent regions—has been studied extensively in geography and regional science [REF1]. Classical work on functional regions and nodal regions provides conceptual foundations, though most such work predates modern computational clustering methods.

Electoral geography, a subfield of political geography, analyzes spatial patterns in voting behavior. Researchers have long observed that political preferences are not randomly distributed but exhibit strong spatial autocorrelation—nearby areas tend to vote similarly due to shared demographic characteristics, economic conditions, and social networks [REF2]. I plan to build on these observations by using computational clustering to formalize and visualize regional political divisions.

### 4.2 Gerrymandering, Redistricting, and Fairness

The problem of dividing a territory into regions has significant connections to redistricting and gerrymandering research. In democratic systems, electoral districts must be redrawn periodically to reflect population changes. However, the district-drawing process can be manipulated to favor particular parties or groups, a practice known as gerrymandering [REF3].

Recent computational research has developed algorithmic approaches to detect gerrymandering and generate fair district maps. These methods often use Markov Chain Monte Carlo (MCMC) sampling to explore the space of valid redistrictings and identify outlier maps that are statistically unlikely to arise from neutral processes [REF4]. Graph-based metrics like the cut-edge metric and spanning tree methods have been proposed to measure district compactness and contiguity.

My project differs from redistricting in key ways: (1) I aim to maximize political homogeneity *within* cantons (whereas fair redistricting seeks competitive, balanced districts), (2) I operate at the municipality level rather than individual voters or census blocks, and (3) my work is purely descriptive rather than prescriptive. However, the technical challenges—ensuring geographic contiguity, handling population constraints, and operating on spatial graphs—are closely related.

### 4.3 Clustering and Spatial Clustering

Clustering is a fundamental unsupervised learning task: partitioning data into groups such that intra-group similarity is high and inter-group similarity is low. Standard clustering algorithms include k-means (which minimizes within-cluster variance), hierarchical clustering (which builds a dendrogram of nested clusters), and spectral clustering (which leverages graph Laplacian eigenvectors) [REF5].

However, standard clustering methods operate purely in feature space and ignore spatial structure. Spatial clustering extends these methods by incorporating geographic constraints. One common requirement is *contiguity*: each cluster must form a connected region in geographic space. This is crucial for applications like regionalization, habitat delineation, and crime hotspot detection.

Spatially-constrained hierarchical clustering is a natural approach: begin with each spatial unit as its own cluster, then iteratively merge adjacent clusters that are most similar in feature space [REF6]. This agglomerative approach maintains contiguity by construction, as merging two connected clusters yields a connected cluster. Variations differ in how they measure cluster similarity (e.g., single-linkage, average-linkage, Ward's criterion) and how they handle population or size constraints.

SKATER (Spatial K'luster Analysis by Tree Edge Removal) is another influential method that constructs a minimum spanning tree on the adjacency graph, then removes edges to create clusters [REF7]. Region-growing algorithms start from seed points and expand regions by adding adjacent units, while constraint-based methods formulate clustering as an optimization problem with contiguity enforced via integer programming constraints.

### 4.4 Graph-based Methods and Contiguity Constraints

The contiguity requirement transforms clustering into a graph partitioning problem. Given a graph \( G = (V, E) \) where vertices represent spatial units (municipalities) and edges represent adjacency, the goal is to partition \( V \) into \( K \) subsets such that each subset induces a connected subgraph.

Graph connectivity can be verified efficiently using depth-first search or breadth-first search. Maintaining connectivity during clustering requires that merges only occur between adjacent clusters (clusters sharing at least one edge in the graph). This significantly constrains the solution space but ensures geographic coherence.

Efficient implementation requires careful data structure design. Candidate merges between adjacent cluster pairs can be maintained in a priority queue, with merge costs updated as clusters are combined. For large graphs, computational complexity can be reduced through heuristics that limit the number of candidate merges considered at each step.

Graph-based modularity metrics, originally developed for community detection in networks [REF8], can also be adapted to evaluate clustering quality in spatial contexts, balancing within-cluster homogeneity against between-cluster separation.

**References Note:** The above discussion includes placeholder references [REF1]—[REF8]. I will add complete bibliographic details in a subsequent revision. Example works include Assunção et al. (2006) on SKATER, Duque et al. on regionalization methods, and relevant electoral geography and computational redistricting literature.

---

## 5. Problem Definition

### 5.1 Data Entities and Notation

My problem operates on the following data entities:

- **Towns (Municipalities):** Let \( T = \{t_1, t_2, \dots, t_n\} \) denote the set of \( n \) municipalities in Israel for which election data is available.

- **Election Results:** For each town \( t_i \), let \( v_i \in \mathbb{R}^d \) denote a feature vector representing the political profile of the town. This vector may encode:
  - Vote shares for each political party (summing to 1 or 100%).
  - Aggregated vote shares for political blocs (e.g., right-wing bloc, left-wing bloc, center, Arab parties, ultra-Orthodox parties).
  - Other derived features if relevant.

- **Population/Voters:** Let \( p_i \) denote the number of eligible voters (or total population) of town \( t_i \). I will use this for population-weighted similarity measures and optional size constraints.

- **Contiguity Graph:** Let \( G = (V, E) \) denote the adjacency graph where:
  - \( V = T \) (vertices correspond to municipalities).
  - \( (t_i, t_j) \in E \) if and only if towns \( t_i \) and \( t_j \) share a geographic border (i.e., their polygons are adjacent).

  This graph encodes geographic contiguity and I will construct it from municipal boundary polygons.

### 5.2 Desired Output

My goal is to compute a partition of towns into \( K \) cantons:

\[
\mathcal{C} = \{C_1, C_2, \dots, C_K\}
\]

such that:

1. **Complete Partition:** \( \bigcup_{k=1}^K C_k = T \) and \( C_i \cap C_j = \emptyset \) for \( i \neq j \).

2. **Geographic Contiguity:** Each canton \( C_k \) induces a connected subgraph in \( G \). Formally, for any two towns \( t_i, t_j \in C_k \), there exists a path in \( G \) connecting \( t_i \) and \( t_j \) using only vertices in \( C_k \).

3. **Political Homogeneity:** Towns within the same canton should have similar political profiles (small intra-canton variance in feature space).

4. **Inter-Canton Distinction:** Different cantons should have dissimilar political profiles (large inter-canton variance).

### 5.3 Objectives

I can formulate the problem as an optimization problem with the following objectives:

- **Maximize Intra-Canton Political Similarity:** Minimize the within-canton sum of squared distances (WCSS) or variance in the political feature space:
  \[
  \text{WCSS} = \sum_{k=1}^K \sum_{t_i \in C_k} w_i \cdot d(v_i, \bar{v}_k)^2
  \]
  where \( \bar{v}_k \) is the (population-weighted) centroid of canton \( C_k \), \( w_i \) is a weight (e.g., population), and \( d(\cdot, \cdot) \) is a distance metric (e.g., Euclidean distance).

- **Ensure Geographic Contiguity:** Enforce that each \( C_k \) forms a connected component in \( G \).

- **Optional Size Constraints:** Optionally enforce minimum or maximum canton sizes in terms of number of towns or total population.

This is a constrained clustering problem. Unlike standard k-means or hierarchical clustering, the contiguity constraint makes the problem combinatorially complex and NP-hard in general. Therefore, I will use heuristic approaches such as greedy agglomerative clustering.

### 5.4 Research Questions

In this project, I aim to address the following research questions:

1. **Algorithm Design:** How can I design an efficient greedy clustering algorithm that produces geographically contiguous and politically coherent cantons? What merge criteria and data structures yield good results?

2. **Parameter Sensitivity:** How sensitive are the resulting cantons to the choice of \( K \) (number of cantons)? What happens as \( K \) varies from small (e.g., 3-5 cantons) to large (e.g., 20+ cantons)?

3. **Temporal Stability:** How stable are canton boundaries across the five election cycles? Do the same regions consistently cluster together, or do boundaries shift significantly depending on which election I analyze?

4. **Political Interpretability:** To what extent do the resulting cantons align with intuitive or commonly-discussed regional divisions (e.g., "Tel Aviv metro vs. Jerusalem metro," "Arab sector vs. Jewish sector," "secular coast vs. religious interior")? Can I meaningfully label or interpret the cantons?

5. **Methodological Comparison:** How does my greedy spatial clustering approach compare to baseline methods (e.g., standard hierarchical clustering without spatial constraints, purely graph-based clustering)?

6. **Practical Utility:** Can my system provide insights useful for political science research, journalism, or public discourse about regional political differences in Israel?

---

## 6. Data Sources and Preprocessing

### 6.1 Election Data

**Source:** The Israel Central Bureau of Statistics (CBS) publishes detailed election results at the municipality (town) level for all Knesset elections. These datasets are publicly available via the CBS website and the Israel National Data Portal.

**Elections Covered:** I will use data from the five most recent Knesset elections:
- April 9, 2019 (21st Knesset)
- September 17, 2019 (22nd Knesset)
- March 2, 2020 (23rd Knesset)
- March 23, 2021 (24th Knesset)
- November 1, 2022 (25th Knesset)

**Data Fields:** Typical fields include:
- Municipality code (unique identifier)
- Municipality name (Hebrew and possibly English)
- Total eligible voters
- Total valid votes cast
- Votes received by each political party/list
- Turnout percentage

**Format:** Data is typically provided in Excel (.xlsx) or CSV format, with one row per municipality and columns for each party.

**Data Sources:** Election and geographic data will be obtained from publicly available resources, including the Israel Central Bureau of Statistics (CBS) publications portal.

### 6.2 Geographic Data (Polygons)

**Source:** Municipal boundary polygons for Israeli municipalities are available from:
- The Israel CBS GIS repository.
- The Israeli government's open data portal.
- OpenStreetMap (though CBS data is generally more authoritative).

**Format:** Geographic data is expected in standard GIS formats such as:
- Shapefile (.shp, .shx, .dbf, .prj)
- GeoJSON (.geojson)
- KML/KMZ (convertible to other formats)

**Coordinate System:** Data is typically in Israel Transverse Mercator (ITM) or WGS84 coordinate systems. I may need to perform coordinate system transformations for consistency.

**Attributes:** Each polygon feature includes attributes such as municipality code, municipality name, area, and possibly population or administrative classification.

### 6.3 Data Integration Challenges

Integrating election data with geographic data presents several challenges that I anticipate:

1. **Inconsistent Municipality Codes and Names:**
   - Municipality codes may differ between datasets or change over time due to administrative reorganization.
   - Municipality names may be spelled differently (transliteration variations, Hebrew vs. English).
   - Some municipalities may have merged or split between election cycles.

2. **Missing or Incomplete Data:**
   - Small or newly-created municipalities may lack complete polygon data.
   - Some towns may not appear in all five election datasets (due to mergers, splits, or data collection issues).

3. **Special Administrative Cases:**
   - Certain areas (e.g., Area C in the West Bank, military zones) may have complex or unclear municipality definitions.
   - Settlement councils vs. municipalities may require careful handling.

**Mitigation Strategies:**
- I will perform careful name normalization and fuzzy matching.
- I will cross-reference multiple data sources to resolve ambiguities.
- I will maintain a mapping table between election municipality IDs and polygon municipality IDs.
- I will document any towns excluded due to data issues.

### 6.4 Feature Engineering

I need to transform the raw election data (vote counts per party) into feature vectors suitable for clustering:

1. **Vote Share Vectors:**
   - I will normalize vote counts to proportions (vote shares) for each party, so that \( \sum_j v_{ij} = 1 \) where \( v_{ij} \) is the vote share for party \( j \) in town \( i \).
   - This removes the effect of town size and focuses on political composition.

2. **Bloc Aggregation:**
   - Israeli elections typically feature 10-15 party lists, many of which are small.
   - I may optionally aggregate parties into political blocs:
     - **Right-wing bloc:** Likud, Religious Zionism, Shas, United Torah Judaism, etc.
     - **Center/Left bloc:** Yesh Atid, Labor, Meretz, etc.
     - **Arab parties:** Joint List, Ra'am, Hadash-Ta'al, etc.
     - **Other:** Smaller parties or those not fitting standard blocs.
   - Bloc-level features reduce dimensionality and may improve interpretability.

3. **Dimensionality Reduction (Optional):**
   - If using fine-grained party-level features, I could apply Principal Component Analysis (PCA) to reduce dimensions while retaining variance.
   - However, interpretability may decrease, so this is optional depending on algorithm performance.

4. **Handling Missing Values and Small Parties:**
   - Parties receiving less than a threshold (e.g., 1%) of votes in a town may be grouped into "Other."
   - Towns with very low turnout or missing data may be flagged or excluded.

### 6.5 Contiguity Graph Construction

I will construct the contiguity graph \( G = (V, E) \) from municipal polygons:

1. **Adjacency Detection:**
   - Two municipalities are considered adjacent if their polygons share a border (not just a single point).
   - I can compute this using GIS libraries (e.g., `geopandas`, `shapely`) by checking for non-empty intersection of polygon boundaries.

2. **Edge Weighting (Optional):**
   - Edges could optionally be weighted by the length of the shared border, though for most purposes binary adjacency is sufficient.

3. **Handling Disconnected Components and Islands:**
   - Some municipalities may be islands (e.g., locations surrounded by water or international borders) with no land neighbors.
   - Options:
     - Exclude such municipalities from clustering (document exclusions).
     - Add artificial edges to nearest neighbors based on centroid distance.
   - I will document and justify the chosen approach.

4. **Graph Validation:**
   - I will verify that the contiguity graph has reasonable properties:
     - Most towns have 3-8 neighbors (typical for planar graphs).
     - The graph is mostly connected (few isolated components).
   - I will visualize the graph to identify anomalies.

---

## 7. Methodology and Algorithms

### 7.1 Overall Approach

My project follows a multi-stage pipeline:

1. **Data Ingestion:** Load election data (CSV/Excel) and geographic data (Shapefiles/GeoJSON).
2. **Data Cleaning and Integration:** Match election records to polygon records, handle inconsistencies, normalize town names and codes.
3. **Feature Computation:** Compute political feature vectors (vote shares or bloc aggregations) for each town.
4. **Contiguity Graph Construction:** Build adjacency graph from polygons.
5. **Clustering:** Apply greedy spatial clustering algorithm to partition towns into \( K \) cantons.
6. **Evaluation:** Compute quality metrics, compare to baselines, analyze stability across elections.
7. **Visualization:** Generate interactive maps showing canton boundaries and political profiles.

### 7.2 Similarity / Distance Measures

Measuring similarity between towns (or clusters of towns) is central to my clustering algorithm. Candidate measures include:

1. **Euclidean Distance:**
   \[
   d(v_i, v_j) = \sqrt{\sum_{k=1}^d (v_{ik} - v_{jk})^2}
   \]
   where \( v_i, v_j \in \mathbb{R}^d \) are feature vectors (vote shares).
   - Simple and widely used.
   - Treats all dimensions equally.

2. **Cosine Similarity (or Distance):**
   \[
   \text{cosine\_similarity}(v_i, v_j) = \frac{v_i \cdot v_j}{\|v_i\| \|v_j\|}
   \]
   \[
   d_{\text{cosine}}(v_i, v_j) = 1 - \text{cosine\_similarity}(v_i, v_j)
   \]
   - Measures angle between vectors, ignoring magnitude.
   - May be useful if focusing on the *direction* of political preferences rather than absolute differences.

3. **Population-Weighted Distance:**
   - When comparing clusters, I will use population-weighted centroids:
     \[
     \bar{v}_k = \frac{\sum_{t_i \in C_k} p_i \cdot v_i}{\sum_{t_i \in C_k} p_i}
     \]
     where \( p_i \) is the population (or number of voters) in town \( t_i \).
   - This gives more weight to larger towns, which may better reflect regional political character.

**Chosen Approach:** My primary method will use **Euclidean distance with population-weighted cluster centroids**. This balances simplicity, interpretability, and the importance of population size. I will also test cosine similarity as an alternative for comparison.

### 7.3 Greedy Spatial Clustering Algorithm (Core of the Project)

The core algorithm I will implement is a **bottom-up agglomerative greedy clustering** approach with spatial contiguity constraints. The algorithm is inspired by spatially-constrained hierarchical clustering methods.

**Algorithm Outline:**

1. **Initialization:**
   - Start with each town as its own cluster: \( \mathcal{C} = \{\\{t_1\\}, \\{t_2\\}, \dots, \\{t_n\\}\} \).
   - Compute the political feature vector (centroid) for each singleton cluster.
   - Construct the set of candidate merges: all pairs of adjacent clusters in the contiguity graph.

2. **Iteration (Greedy Merge):**
   - While the number of clusters \( |\mathcal{C}| > K \) (target number of cantons):
     1. **Identify Candidate Merges:** For each pair of adjacent clusters \( (C_i, C_j) \), compute a merge cost \( \text{cost}(C_i, C_j) \).
     2. **Select Best Merge:** Choose the pair \( (C_i^*, C_j^*) \) with the lowest merge cost (or highest merge gain, depending on formulation).
     3. **Merge Clusters:** Combine \( C_i^* \) and \( C_j^* \) into a new cluster \( C_{\text{new}} = C_i^* \cup C_j^* \).
     4. **Update Centroids:** Compute the new centroid \( \bar{v}_{\text{new}} \) for \( C_{\text{new}} \) using population-weighted averaging.
     5. **Update Candidate Merges:** Remove obsolete candidate merges involving \( C_i^* \) or \( C_j^* \), and add new candidate merges involving \( C_{\text{new}} \) and its neighbors in the contiguity graph.

3. **Termination:**
   - Stop when the number of clusters reaches \( K \).
   - Return the partition \( \mathcal{C} = \{C_1, \dots, C_K\} \).

**Merge Cost Function:**

The merge cost \( \text{cost}(C_i, C_j) \) quantifies how "expensive" (undesirable) it is to merge clusters \( C_i \) and \( C_j \). Several options:

- **Increase in Within-Cluster Sum of Squares (Ward's Criterion):**
  \[
  \text{cost}(C_i, C_j) = \frac{|C_i| \cdot |C_j|}{|C_i| + |C_j|} \cdot d(\bar{v}_i, \bar{v}_j)^2
  \]
  where \( |C_i| \) is the population of cluster \( C_i \) and \( \bar{v}_i \) is its centroid.
  - This is the increase in total within-cluster variance resulting from the merge.
  - Commonly used in hierarchical clustering.

- **Simple Distance Between Centroids:**
  \[
  \text{cost}(C_i, C_j) = d(\bar{v}_i, \bar{v}_j)
  \]
  - Simpler but may not account for cluster size.

I will primarily use **Ward's criterion** (increase in WCSS) as it balances political similarity and cluster size.

**Adjacency Between Clusters:**

Two clusters \( C_i \) and \( C_j \) are adjacent if there exists at least one edge in the contiguity graph connecting a town in \( C_i \) to a town in \( C_j \):
\[
(C_i, C_j) \text{ adjacent} \iff \exists\, t_a \in C_i, t_b \in C_j \text{ such that } (t_a, t_b) \in E
\]

**Time Complexity:**

- Naive implementation: \( O(n^2 \log n) \) for \( n \) towns, as each of \( O(n) \) merge steps requires scanning \( O(n) \) candidate pairs and updating centroids.
- **Optimized implementation using priority queue:**
  - I will maintain candidate merges in a min-heap (priority queue) keyed by merge cost.
  - Each merge requires heap updates, which can be done in \( O(\log n) \) time.
  - Overall complexity: \( O(n \log n) \) to \( O(n^2 \log n) \) depending on graph density.

**Data Structures:**

- **Cluster Representation:** Each cluster will store:
  - List of member towns.
  - Population-weighted centroid \( \bar{v} \).
  - Total population \( p \).
  - Set of neighboring clusters in the current contiguity graph.

- **Candidate Merge Heap:** Min-heap (priority queue) of candidate merges, keyed by merge cost.

- **Adjacency Tracking:** Data structure (e.g., dictionary or adjacency list) to quickly determine which clusters are neighbors.

### 7.4 Alternative / Baseline Methods

To validate my proposed greedy spatial clustering algorithm, I will implement and compare against baseline methods:

1. **Standard Hierarchical Clustering (Without Spatial Constraints):**
   - I will apply agglomerative hierarchical clustering (e.g., Ward's method) to political feature vectors, ignoring geographic contiguity.
   - This will show the "pure" political clustering, which may result in non-contiguous cantons.
   - Useful for understanding how much the contiguity constraint affects results.

2. **K-Means Clustering (Without Spatial Constraints):**
   - I will run k-means clustering on political feature vectors.
   - Again, results may be geographically fragmented.

3. **Graph-Based Clustering (Topology Only):**
   - I will cluster based purely on the contiguity graph \( G \) using graph community detection algorithms (e.g., Louvain method, spectral clustering on \( G \)).
   - This ignores political features and clusters based only on graph topology.
   - Shows the effect of pure geographic structure.

4. **Administrative Regions Baseline:**
   - I will use existing administrative divisions (e.g., districts defined by the Israeli government) as a simple baseline partition.
   - I will compare political homogeneity within these predefined regions to my algorithmically-generated cantons.

**Comparison Metrics:**
- **Within-Canton Political Variance (WCSS):** Lower is better.
- **Silhouette Score:** Measures how well towns fit within their assigned canton vs. other cantons.
- **Contiguity:** Percentage of cantons that are geographically contiguous (100% for spatial algorithms, likely lower for standard clustering).
- **Adjusted Rand Index (ARI):** Measure agreement between different clustering results.

### 7.5 Stability Across Elections

A key research question is how stable canton boundaries are across the five election cycles. To analyze this, I will:

1. **Run Clustering on Each Election Separately:**
   - For a fixed \( K \), I will run my greedy spatial clustering algorithm on election data from each of the five elections.
   - Produce five partitions: \( \mathcal{C}^{(1)}, \dots, \mathcal{C}^{(5)} \).

2. **Measure Partition Agreement:**
   - I will use metrics such as:
     - **Adjusted Rand Index (ARI):** Measures similarity between two partitions, correcting for chance.
     - **Normalized Mutual Information (NMI):** Information-theoretic measure of partition similarity.
     - **Jaccard Index of Canton Membership:** For each pair of cantons from different elections, measure overlap.

3. **Visualize Changes:**
   - I will create maps showing which towns changed canton assignments between elections.
   - Highlight stable regions (towns that remain in the "same" canton across elections) vs. volatile regions.

4. **Aggregate Clustering Across Elections:**
   - Optionally, I will create a "consensus" clustering by averaging political feature vectors across all five elections and clustering the averaged data.
   - I will compare this consensus clustering to individual election clusterings.

### 7.6 Implementation Technologies

**Programming Language:** Python 3.9+

**Core Libraries:**

- **Data Manipulation:**
  - `pandas`: Data loading, cleaning, manipulation of tabular data.
  - `numpy`: Numerical operations, array handling.

- **Geospatial Processing:**
  - `geopandas`: Extends pandas to handle geospatial data, read/write Shapefiles and GeoJSON.
  - `shapely`: Geometry manipulation, adjacency detection, polygon operations.
  - `pyproj`: Coordinate system transformations.

- **Graph Algorithms:**
  - `networkx`: Graph representation, adjacency tracking, connectivity checks.

- **Machine Learning / Clustering:**
  - `scikit-learn`: Baseline clustering algorithms (k-means, hierarchical), distance metrics, evaluation metrics (silhouette score, ARI).

- **Visualization:**
  - `matplotlib`: Static plots and charts.
  - `folium`: Interactive web maps (for Jupyter notebook exploration).
  - Optionally: Web-based stack (React + Leaflet or Mapbox) for a more polished UI.

**Development Environment:**
- Jupyter Notebooks for exploratory analysis and prototyping.
- Python scripts for production pipeline.
- Version control using Git and GitHub.

**Data Storage:**
- File-based storage (CSV for election data, GeoJSON/Shapefile for polygons) for simplicity.
- Optionally: PostGIS (PostgreSQL with spatial extensions) as a stretch goal for more advanced geospatial queries.

---

## 8. System Architecture and Design

### 8.1 High-Level Architecture

My system will follow a modular, layered architecture:

1. **Data Layer:**
   - **Data Acquisition Module:** Scripts to download or ingest election data and polygon data from CBS or other sources.
   - **Data Cleaning Module:** Handles inconsistencies, missing values, name normalization, and matching between datasets.
   - **Data Storage:** File-based storage (CSV, GeoJSON) or optional database (PostGIS).

2. **Algorithm Layer:**
   - **Feature Engineering Module:** Computes political feature vectors (vote shares, bloc aggregations) from raw election data.
   - **Graph Construction Module:** Builds contiguity graph from polygons using `geopandas` and `shapely`.
   - **Clustering Module:** Implements greedy spatial clustering algorithm and baseline methods.
   - **Evaluation Module:** Computes clustering quality metrics, stability metrics, comparisons.

3. **API / Service Layer (Optional):**
   - If I build a web application, a lightweight API (e.g., Flask or FastAPI) can serve clustering results and handle user requests (e.g., "cluster using election X with K=7").

4. **Visualization / UI Layer:**
   - **Mapping Module:** Renders town polygons colored by canton assignment.
   - **Interactive Controls:** Allows user to select election, choose \( K \), and trigger clustering.
   - **Summary Statistics:** Displays canton-level political profiles, population, geographic area, etc.

### 8.2 Data Storage

**Approach:** For simplicity and reproducibility, I will primarily use **file-based storage**:

- **Election Data:** CSV files (one per election) containing town-level vote counts.
- **Geographic Data:** GeoJSON or Shapefile format for town polygons.
- **Intermediate Outputs:** Pickle files or JSON for storing processed feature vectors, contiguity graphs, clustering results.

**Optional Enhancement:** If time permits, I may use a **PostGIS database** (PostgreSQL with spatial extensions) for:
- Efficient spatial queries (e.g., finding all towns within a distance, intersection queries).
- Storing multiple elections and clustering results in a structured, queryable format.
- Handling large-scale data more efficiently.

However, given the relatively small number of municipalities in Israel (~250-300), file-based storage should be sufficient for the scope of my project.

### 8.3 Visualization and User Interface

The visualization component is critical for making my project results accessible and interpretable.

**Minimum Viable Product (MVP):**

- **Jupyter Notebook-Based Visualization:**
  - I will use `geopandas` and `matplotlib` to produce static maps of cantons.
  - I will use `folium` to generate interactive HTML maps viewable in a browser.
  - Users can modify parameters (election, \( K \)) in the notebook and re-run cells to see new results.

**Enhanced Interface (Stretch Goal):**

- **Web Application:**
  - **Frontend:** React or simple HTML/JavaScript interface.
  - **Mapping Library:** Leaflet or Mapbox GL JS for interactive, zoomable maps.
  - **Backend API:** Flask or FastAPI serving clustering results.
  - **User Interaction:**
    - Dropdown to select election round (or "All Elections Average").
    - Slider or input to choose number of cantons \( K \).
    - Button to trigger clustering computation.
    - Map updates to show resulting cantons.
  - **Canton Details Panel:**
    - Click on a canton to see:
      - Political profile (vote shares for parties/blocs).
      - Total population / number of voters.
      - List of municipalities in the canton.
      - Geographic area.
  - **Comparison View:** Side-by-side maps comparing different elections or different \( K \) values.

**Technology Suggestions:**

- **Python + Folium (Notebook MVP):**
  - Quick to implement.
  - Good for exploratory analysis and internal use.
  - Limited interactivity.

- **Web Stack (Stretch Goal):**
  - More polished and user-friendly.
  - Suitable for public sharing or demonstration.
  - Requires additional development effort.

I will prioritize the notebook-based MVP first, then consider a web interface if time allows.

### 8.4 Software Engineering Considerations

**Code Organization:**

- **Modular Structure:** I will create separate modules/scripts for data cleaning, feature engineering, graph construction, clustering, evaluation, and visualization.
- **Configuration Files:** I will use JSON or YAML configuration files to specify:
  - Paths to data files.
  - Election to analyze.
  - Number of cantons \( K \).
  - Distance metric and merge cost function.
  - Random seeds (if any randomization is involved).
- **Reproducibility:**
  - All my data processing and analysis will be fully reproducible from raw data.
  - I will include a `requirements.txt` or `environment.yml` specifying library versions.
  - I will document all manual data preprocessing steps (if any).

**Documentation:**

- **Code Comments and Docstrings:** All my functions and modules will have clear docstrings.
- **README:** High-level overview of project, setup instructions, usage examples.
- **Jupyter Notebooks:** Narrative notebooks explaining data exploration, algorithm development, and results.

**Testing:**

- **Unit Tests:** For core functions (e.g., distance computation, contiguity checking, merge operations).
- **Integration Tests:** End-to-end tests of the clustering pipeline.
- **Data Validation:** Checks for data integrity (e.g., vote shares sum to 1, all polygons are valid).

**Version Control:**

- I will use Git for version control.
- I will host the repository on GitHub (or GitLab).
- I will commit regularly with clear, descriptive commit messages.

**Performance:**

- I will profile my clustering algorithm to identify bottlenecks.
- I will optimize data structures (e.g., use priority queue for candidate merges).
- I will consider parallelization if needed (though unlikely to be necessary for ~300 towns).

---

## 9. Evaluation Plan

### 9.1 Quantitative Evaluation

I will evaluate clustering quality using multiple quantitative metrics:

**1. Within-Canton Sum of Squares (WCSS):**
\[
\text{WCSS} = \sum_{k=1}^K \sum_{t_i \in C_k} p_i \cdot d(v_i, \bar{v}_k)^2
\]
- Measures political homogeneity within cantons.
- Lower WCSS indicates tighter, more homogeneous clusters.
- I will compare across different values of \( K \) and different elections.

**2. Silhouette Score:**
- For each town \( t_i \), compute:
  \[
  s_i = \frac{b_i - a_i}{\max(a_i, b_i)}
  \]
  where \( a_i \) is the average distance to other towns in the same canton, and \( b_i \) is the average distance to towns in the nearest other canton.
- Silhouette score ranges from -1 to +1; higher is better.
- Provides a per-town and overall measure of clustering quality.

**3. Spatial Contiguity Verification:**
- I will verify that each canton \( C_k \) is a connected component in the contiguity graph \( G \).
- I will report percentage of cantons that are contiguous (should be 100% for my spatial clustering algorithm).
- For baseline methods without spatial constraints, I will measure how many non-contiguous clusters are produced.

**4. Between-Canton Separation:**
- I will measure the distance between canton centroids.
- Ideally, cantons should be well-separated in political feature space.

**5. Modularity (Optional):**
- If viewing the problem as a graph partitioning task, I will compute modularity:
  \[
  Q = \frac{1}{2m} \sum_{i,j} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)
  \]
  where \( A_{ij} \) is the adjacency matrix, \( k_i \) is the degree of node \( i \), \( m \) is the number of edges, and \( \delta(c_i, c_j) = 1 \) if nodes \( i \) and \( j \) are in the same canton.
- Modularity measures the strength of community structure in the graph.

**Experiments:**

- **Vary \( K \):** I will test \( K = 3, 5, 7, 10, 15, 20 \) and plot WCSS, silhouette score vs. \( K \).
- **Compare Algorithms:** I will run greedy spatial clustering, standard hierarchical clustering, k-means, graph-based clustering, and administrative regions baseline; compare metrics.
- **Vary Distance Metric:** I will test Euclidean distance vs. cosine distance.

### 9.2 Stability and Robustness

**Temporal Stability (Across Elections):**

- For a fixed \( K \), I will cluster each of the five elections separately.
- I will compute pairwise Adjusted Rand Index (ARI) and Normalized Mutual Information (NMI) between all pairs of election results.
- High ARI/NMI indicates stable canton boundaries; low values indicate volatility.
- I will create a stability matrix showing agreement between all election pairs.

**Sensitivity to Parameters:**

- **Initialization Sensitivity:** If any randomness is involved, I will test with multiple random seeds.
- **Sensitivity to Distance Metric:** I will compare results using Euclidean vs. cosine distance.
- **Sensitivity to Bloc Aggregation:** I will compare party-level features vs. bloc-level features.

**Robustness to Data Perturbations (Optional):**

- I may simulate missing data by randomly removing towns or introducing noise in vote shares.
- I will test whether clustering results remain qualitatively similar.

### 9.3 Qualitative Evaluation

Quantitative metrics alone do not capture whether the cantons "make sense" from a human or domain-expert perspective. My qualitative evaluation will include:

**1. Visual Inspection:**

- I will examine maps of cantons for different values of \( K \) and different elections.
- I will look for:
  - Geographic coherence (cantons forming recognizable regions).
  - Alignment with known political divisions (e.g., secular Tel Aviv vs. religious Jerusalem, Arab vs. Jewish towns).
  - Anomalies or counterintuitive groupings.

**2. Case Studies:**

I will conduct detailed case studies on specific regions:

- **Greater Tel Aviv Area:** Typically center-left, secular. Does it form a coherent canton?
- **Jerusalem and Surroundings:** Mix of ultra-Orthodox, Arab, and secular populations. How is this region partitioned?
- **Northern Arab Towns:** How do predominantly Arab municipalities cluster? Are they grouped together or separated by geography?
- **Settlements and West Bank Areas:** If included in data, how do these towns cluster?

**3. Canton Labeling and Interpretation:**

- I will attempt to assign meaningful labels to cantons based on their political profile:
  - "Left-secular coast"
  - "Ultra-Orthodox center"
  - "Arab sector"
  - "National-religious periphery"
  - Etc.
- I will assess whether labels are consistent and interpretable.

**4. Comparison to Existing Divisions:**

- I will compare my algorithmic cantons to:
  - Israeli government districts (North, Haifa, Center, Tel Aviv, Jerusalem, South).
  - Historical regional divisions.
  - Media/public discourse regions (e.g., "Gush Dan," "HaMerkaz," etc.).
- I will measure overlap and discuss differences.

### 9.4 Expert Feedback (Optional, but Good to Mention)

If feasible, I will seek feedback from domain experts:

- **Political Scientists or Geographers (Bar-Ilan University or external):** Consult on the political interpretability and validity of the cantons.
- **GIS Experts:** Feedback on the technical quality of spatial data processing and visualization.

Feedback will inform refinements to my algorithm, feature engineering choices, and how I communicate results.

---

## 10. Ethical, Social, and Political Considerations

My project operates at the intersection of computational methods and politically sensitive subject matter. I believe it's essential to address ethical and social considerations explicitly.

### Sensitivity of Political Data

Election results are public data, but their analysis can have political implications. I must:

- **Maintain Objectivity:** My project is a **descriptive, exploratory analysis**, not a normative political proposal. I am not advocating for splitting Israel into cantons or any specific political outcome.
- **Avoid Misinterpretation:** I will clearly communicate that the cantons are algorithmic constructs based on voting patterns, not recommendations for political action.
- **Contextualize Results:** I will emphasize that political preferences are multifaceted and cannot be fully captured by vote shares alone. Canton boundaries are simplifications.

### Privacy and Anonymity

- **Aggregated Data:** All data is aggregated at the municipality level. Individual voter identities and choices are not included or inferable from my analysis.
- **Public Data:** Both election results and municipal polygons are publicly available datasets. My project does not access or require any private or confidential information.

### Potential Misuse

Maps showing political divisions can be misused or misinterpreted:

- **Over-Generalization:** Users might over-generalize, assuming all individuals in a canton hold the same political views (ecological fallacy).
- **Inflammatory Rhetoric:** Political actors might exploit the maps to inflame divisions or support divisive policies.

**Mitigation:**

- **Clear Documentation and Caveats:** All my visualizations and reports will include disclaimers explaining the limitations and descriptive nature of the analysis.
- **Transparency:** I will publish code, data sources, and methodology openly so others can verify and critique my approach.
- **Educational Framing:** I will position the project as a computer science and data science exercise, with insights for political geography research, rather than a political statement.

### Inclusivity and Representation

Israeli society is diverse, including Jewish and Arab citizens, religious and secular populations, immigrants, and various socioeconomic groups. My project must:

- **Avoid Stereotyping:** Not reinforce simplistic stereotypes (e.g., "all Arabs vote the same way," "all religious Jews support the same parties"). I will recognize intra-group diversity.
- **Acknowledge Complexity:** Voting patterns reflect complex factors including ethnicity, religion, socioeconomic status, and local issues. I will acknowledge this complexity in my interpretation.

### Responsible Communication

When presenting results:

- **Academic Tone:** I will use formal, neutral language.
- **Emphasize Uncertainty:** I will acknowledge limitations, sensitivity to parameters, and areas of uncertainty.
- **Invite Critique:** I will encourage feedback and critical engagement from diverse perspectives.

---

## 11. Risks, Challenges, and Mitigation Strategies

### 11.1 Data-Related Risks

**Risk:** Incomplete, inconsistent, or incorrect data.

- **Examples:** Missing election results for some towns, inconsistent municipality codes, changes in municipal boundaries over time.
- **Impact:** Poor data quality can lead to inaccurate clustering results or inability to match election data with polygons.

**Mitigation:**

- **Multiple Data Sources:** I will cross-check election data from CBS with other sources (e.g., Central Elections Committee) if available.
- **Careful Preprocessing:** I will invest significant effort in data cleaning, name normalization, and matching logic.
- **Documentation:** I will document all data issues encountered and how I resolved them.
- **Robustness Checks:** I will test clustering with slightly perturbed data to ensure results are not overly sensitive to minor data errors.

**Risk:** Geographic data (polygons) may be outdated or misaligned.

- **Impact:** Incorrect adjacency relationships, poor map visualizations.

**Mitigation:**

- I will use the most recent and authoritative polygon data available (CBS or official government GIS).
- I will validate the contiguity graph by visual inspection and sanity checks (e.g., known neighbors).

### 11.2 Algorithmic Risks

**Risk:** Greedy algorithm may produce suboptimal results (local optima).

- **Impact:** Clustering may not be as good as theoretically possible; cantons may not align well with intuitive divisions.

**Mitigation:**

- **Baseline Comparisons:** I will compare greedy results to other methods to assess quality.
- **Multiple Initializations:** If randomness is involved (e.g., tie-breaking), I will test multiple runs.
- **Refinement Heuristics:** I may consider post-processing steps like local search or reassignment of border towns.

**Risk:** Computational complexity and runtime.

- **Impact:** Algorithm may be slow for large graphs or many iterations.

**Mitigation:**

- **Efficient Data Structures:** I will use priority queues and adjacency lists to minimize redundant computation.
- **Profiling and Optimization:** I will profile code to identify bottlenecks and optimize critical sections.
- **Early Stopping:** If \( K \) is reached, I will stop immediately (no need to continue).

Given the relatively small number of municipalities (~250-300), runtime is unlikely to be a major issue, but these mitigation strategies are good practice.

### 11.3 Project Management Risks

**Risk:** Scope creep—attempting to implement too many features or analyses, leading to incomplete core work.

- **Impact:** Project may not be finished on time or core components may be underdeveloped.

**Mitigation:**

- **Clear Prioritization:** I will define "core" deliverables (data pipeline, greedy clustering, basic visualization) vs. "stretch goals" (web UI, advanced baselines, extensive stability analysis).
- **Phased Development:** I will follow the timeline in Section 12, completing each phase before moving to the next.
- **Regular Check-Ins:** Quarterly progress reviews to adjust scope if needed.

**Risk:** Time constraints—M.Sc. project is limited to one academic year.

- **Impact:** Insufficient time to complete all planned work.

**Mitigation:**

- **Realistic Timeline:** The timeline in Section 12 is designed to be achievable within 12 months.
- **Incremental Development:** I will build and test components incrementally rather than waiting until the end.
- **Fallback Plan:** If time runs short, I will focus on core algorithm and evaluation; defer advanced UI or secondary analyses to future work.

### 11.4 Scope Control

To keep my project manageable:

- **Core Requirements (Must Have):**
  - Data cleaning and integration for at least 3 of the 5 elections.
  - Working greedy spatial clustering algorithm.
  - Basic contiguity graph construction.
  - At least one baseline comparison (e.g., hierarchical clustering without spatial constraints).
  - Quantitative evaluation (WCSS, silhouette score).
  - Static or basic interactive maps showing cantons.

- **Stretch Goals (Nice to Have):**
  - Analysis of all 5 elections.
  - Stability analysis across elections.
  - Polished web-based UI.
  - PostGIS database.
  - Extensive qualitative case studies.
  - Multiple baseline algorithms.

If time permits, I will pursue stretch goals. If not, I will note them as future work.

---

## 12. Work Plan and Timeline

I plan to complete this project over approximately **12 months** (two academic semesters plus summer), broken into six phases. Each phase has specific goals, deliverables, and dependencies.

### Phase 1: Literature Review and Data Acquisition (Months 1-2)

**Goals:**

- Understand relevant literature on spatial clustering, political geography, and gerrymandering.
- Identify and access election data and geographic polygon data.
- Set up development environment and project infrastructure.

**Tasks:**

- Review academic papers and resources on regionalization, constrained clustering, and electoral geography.
- Locate and download town-level election results for the five elections.
- Obtain municipal boundary polygons (Shapefiles or GeoJSON).
- Set up Python environment with necessary libraries (pandas, geopandas, networkx, scikit-learn, etc.).
- Initialize Git repository and project folder structure.

**Deliverables:**

- Annotated bibliography of 8-12 key references.
- Raw data files (election CSVs, polygon Shapefiles/GeoJSON).
- Configured development environment.
- Initial project README and folder structure.

**Dependencies:** None (starting phase).

---

### Phase 2: Data Cleaning, Integration, and Feature Engineering (Months 2-4)

**Goals:**

- Clean and standardize election data and polygon data.
- Match municipalities between election records and polygons.
- Compute political feature vectors for each municipality.

**Tasks:**

- Normalize municipality names and codes.
- Handle missing data, merge inconsistencies, and special cases (merged/split municipalities).
- Create a unified dataset linking each municipality to its election results and polygon.
- Compute vote share vectors (party-level and/or bloc-level).
- Validate data integrity (e.g., vote shares sum to 1, polygons are valid).

**Deliverables:**

- Cleaned and integrated dataset (CSV or DataFrame) with:
  - Municipality ID, name, polygon reference.
  - Political feature vectors for each election.
  - Population/voter counts.
- Data cleaning and integration scripts.
- Data validation report documenting issues and resolutions.

**Dependencies:** Phase 1 (raw data must be acquired).

---

### Phase 3: Graph Construction and Algorithm Implementation (Months 4-7)

**Goals:**

- Build the contiguity graph from polygons.
- Implement the greedy spatial clustering algorithm.
- Implement at least one baseline clustering method.

**Tasks:**

- Use `geopandas` and `shapely` to detect adjacency between municipalities.
- Construct contiguity graph \( G = (V, E) \) using `networkx`.
- Validate graph (check connectivity, visualize).
- Implement greedy agglomerative clustering with contiguity constraints:
  - Initialization, merge cost computation, priority queue, centroid updates.
- Implement baseline: standard hierarchical clustering (without spatial constraints).
- Test algorithms on a subset of data to verify correctness.

**Deliverables:**

- Contiguity graph (stored as `networkx` graph object or adjacency list).
- Working implementation of greedy spatial clustering algorithm.
- Baseline clustering implementation.
- Unit tests for key functions (distance computation, merge operations, contiguity checks).

**Dependencies:** Phase 2 (requires clean data and feature vectors).

---

### Phase 4: Evaluation, Experiments, and Stability Analysis (Months 7-9)

**Goals:**

- Run clustering experiments with different parameters.
- Evaluate clustering quality quantitatively and qualitatively.
- Analyze stability across elections.

**Tasks:**

- Run greedy spatial clustering for \( K = 3, 5, 7, 10, 15, 20 \) on at least 3 elections.
- Compute WCSS, silhouette score, and other metrics.
- Compare greedy spatial clustering to baselines.
- Perform stability analysis: cluster each election separately, compute ARI/NMI.
- Visualize results with basic maps (static plots using `matplotlib` and `geopandas`).
- Conduct qualitative case studies (Tel Aviv, Jerusalem, Arab towns).

**Deliverables:**

- Clustering results for multiple values of \( K \) and multiple elections.
- Evaluation report with tables and plots of metrics.
- Stability analysis results (ARI matrix, visualizations).
- Initial maps showing cantons for different parameters.

**Dependencies:** Phase 3 (requires working clustering algorithms).

---

### Phase 5: Visualization and User Interface Development (Months 9-11)

**Goals:**

- Develop an interactive visualization tool for exploring canton divisions.
- Enhance usability and clarity of results.

**Tasks:**

- Create Jupyter notebook with interactive maps using `folium`.
- Implement user controls (dropdowns, sliders) to select election and \( K \).
- Display canton-level summary statistics and political profiles.
- (Stretch goal) Develop a web-based interface with React + Leaflet and a Flask API.
- Refine visualizations based on feedback.

**Deliverables:**

- Jupyter notebook with interactive exploration capabilities (MVP).
- (Optional) Web application for public demonstration.
- User documentation explaining how to use the visualization tools.

**Dependencies:** Phase 4 (requires clustering results to visualize).

---

### Phase 6: Final Polishing and Documentation (Months 11-12)

**Goals:**

- Finalize all code, documentation, and reports.
- Prepare final project report.
- Conduct final review and quality assurance.

**Tasks:**

- Refactor and clean up code, add comprehensive comments and docstrings.
- Write final project report (incorporating sections from this specification, plus results and analysis).
- Ensure reproducibility: verify that all code runs from scratch with clear instructions.
- Submit deliverables to advisor and department.

**Deliverables:**

- Final project report (PDF).
- Polished, well-documented codebase.
- GitHub repository (if public) or submission package with all code and data.

**Dependencies:** Phases 1-5 (all prior work must be complete).

---

### Timeline Summary

| Phase | Timeframe    | Key Milestones |
|-------|--------------|----------------|
| 1     | Months 1-2   | Literature review, data acquisition, environment setup |
| 2     | Months 2-4   | Data cleaning, integration, feature engineering |
| 3     | Months 4-7   | Graph construction, algorithm implementation |
| 4     | Months 7-9   | Evaluation, experiments, stability analysis |
| 5     | Months 9-11  | Visualization and UI development |
| 6     | Months 11-12 | Final polishing, documentation |

**Note:** Some phases overlap slightly to allow for iterative development and refinement. Regular progress check-ins will occur approximately every 2-3 months (quarterly as required by the department).

---

## 13. Expected Deliverables

At the conclusion of my project, I will provide the following deliverables:

1. **Source Code:**
   - Modular, well-documented Python codebase including:
     - Data cleaning and integration scripts.
     - Feature engineering and graph construction modules.
     - Greedy spatial clustering algorithm implementation.
     - Baseline clustering methods.
     - Evaluation and stability analysis scripts.
     - Visualization tools (Jupyter notebooks and/or web application).
   - Version-controlled repository (Git/GitHub) with clear README and usage instructions.

2. **Data Processing Pipeline:**
   - Reproducible pipeline from raw election data and polygons to final clustering results.
   - Configuration files for easy adjustment of parameters (election, \( K \), distance metric, etc.).

3. **Interactive Visualization Tool:**
   - Minimum: Jupyter notebook with interactive maps (using `folium` or similar).
   - Stretch goal: Web-based application with user-friendly interface.

4. **Final Written Report:**
   - Comprehensive technical report (length according to departmental guidelines) covering:
     - Introduction and motivation.
     - Literature review.
     - Problem definition and methodology.
     - Data sources and preprocessing.
     - Algorithm design and implementation.
     - Experimental results and evaluation.
     - Stability analysis.
     - Qualitative case studies.
     - Discussion of limitations and future work.
     - Conclusion.
   - Report formatted in LaTeX or Markdown, submitted as PDF.

5. **Documentation:**
   - User guide for running the code and reproducing results.
   - Data dictionary explaining all datasets and variables.
   - README files in the code repository.

I will submit all deliverables to the Bar-Ilan University Computer Science Department as required for M.Sc. project completion.

---

## 14. Conclusion

In this project, I will apply computational methods from clustering, graph algorithms, and geospatial data science to explore the political-geographic structure of Israel. By developing a spatially-constrained greedy clustering algorithm and applying it to town-level election results, I aim to provide a data-driven lens on regional political divisions in a highly polarized society.

### Scientific and Technical Contributions

From a **computer science perspective**, my project will contribute:

- A novel application of constrained clustering to political geography, demonstrating the importance of balancing feature-space similarity with spatial contiguity.
- A well-designed greedy algorithm with careful attention to data structures, efficiency, and evaluation.
- A comprehensive analysis of clustering stability across multiple election cycles, providing insights into temporal robustness.
- An integration of GIS processing, graph algorithms, and machine learning in a unified pipeline.

From a **data science and applied analytics perspective**, my project will:

- Provide an analytical tool for exploring electoral geography in Israel.
- Offer insights into the degree of political regionalization and whether cantons align with intuitive or existing divisions.
- Demonstrate responsible handling of politically sensitive data with appropriate caveats and ethical considerations.

### Relevance and Feasibility

My project is directly relevant to **computer science** as a discipline, engaging with core topics in algorithms, data structures, machine learning, and geographic information systems. It is also of interest to political science and geography researchers studying spatial patterns in voting behavior.

I believe the project is **feasible within one academic year**, given the well-defined scope, phased timeline, and availability of public data. The core technical components (data cleaning, graph construction, clustering algorithm, basic visualization) are achievable within 6-8 months, leaving time for evaluation, refinement, and documentation.

### Broader Impact

While my project is descriptive and exploratory rather than prescriptive, it has the potential to inform public discourse and research on political polarization and regional divisions in Israel. By providing transparent, reproducible, and data-driven analysis, my project exemplifies how computational methods can contribute to understanding complex social phenomena.

Ultimately, I hope to demonstrate that politically and socially relevant questions can be approached rigorously using algorithmic thinking and computational tools, yielding insights that are both technically interesting and substantively meaningful.

---

**End of Project Specification**

---

**Internal Note:**

This specification will be updated according to advisor feedback and project progress throughout the academic year. The document serves as the primary reference for implementation planning, design decisions, and scope management.
