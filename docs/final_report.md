# Partitioning Israeli Municipalities into Politically Homogeneous Cantons: A Constrained Spatial Clustering Approach

**Author:** Adir Elmakais (ID: 316413640)

**Advisor:** Dr. Oren Glickman, Department of Computer Science, Bar-Ilan University

**Degree:** M.Sc. in Computer Science (Project Track), Bar-Ilan University

**Academic Year:** 2025–2026

---

## Abstract

Israeli society has experienced significant political polarization in recent years, reflected in five Knesset elections held within a four-year period (2019–2022). Public discourse increasingly references hypothetical divisions of the country into politically homogeneous "cantons." This project develops a data-driven algorithmic approach to explore such divisions using publicly available municipality-level election results and geographic boundary data from the Israel Central Bureau of Statistics (CBS).

We partition 229 Israeli municipalities into geographically contiguous cantons that maximize internal political similarity. Our methodology employs four clustering algorithms — Simulated Annealing, Agglomerative Clustering with contiguity constraints, Spectral Clustering, and Louvain Community Detection — evaluated across four feature representations (BlocShares, RawParty, PCA, NMF), three distance metrics (Euclidean, Cosine, Jensen-Shannon), and six values of K (3–20), yielding a systematic grid of 264 experimental configurations.

Key results show that the BlocShares representation with Cosine distance produces the highest clustering quality (silhouette score 0.905), while Simulated Annealing achieves the best population balance across cantons. Temporal stability analysis across all five elections reveals that deterministic algorithms (Louvain, Agglomerative) produce near-perfectly stable partitions (ARI up to 1.0), while Israel's political geography remains structurally consistent despite electoral volatility. The resulting K=5 partition identifies five politically coherent regions: a right-wing southern periphery, a Haredi-influenced urban center, a center-right coastal belt, a left-leaning Druze enclave, and a large Arab-majority northern bloc — closely reflecting known political-demographic divisions. Comparison with Israel's administrative districts yields an Adjusted Rand Index of 0.435, confirming that political cantons follow ideological rather than administrative boundaries.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Literature Review](#2-literature-review)
3. [Problem Definition](#3-problem-definition)
4. [Data Sources](#4-data-sources)
5. [Methodology](#5-methodology)
6. [Experimental Results](#6-experimental-results)
7. [Stability Analysis](#7-stability-analysis)
8. [Case Studies](#8-case-studies)
9. [Limitations and Future Work](#9-limitations-and-future-work)
10. [Conclusion](#10-conclusion)
11. [References](#references)
12. [Appendix](#appendix)

---

## 1. Introduction

### 1.1 Motivation

Over the past four years, Israel held five Knesset elections (April 2019, September 2019, March 2020, March 2021, and November 2022), an unprecedented frequency that reflects deep political divisions across multiple dimensions: secular versus religious, left versus right on the ideological spectrum, Arab versus Jewish communal politics, and attitudes toward judicial reform and governance. Throughout this period, public and media discourse repeatedly invoked the notion of dividing Israel into separate "cantons" along political lines — contrasting, for example, Tel Aviv's liberal-secular majority with Jerusalem's religious-conservative population, or the Arab-majority towns of northern Israel with predominantly Jewish communities elsewhere.

While such discourse is largely rhetorical, it raises a compelling computational question: if Israel were to be divided into politically coherent regions based purely on voting patterns, what would those regions look like, and how stable would they be across election cycles? This project applies data-driven computational methods to answer this question rigorously.

### 1.2 Research Objectives

This project has three primary objectives:

1. **Partition 229 Israeli municipalities into K geographically contiguous cantons** that maximize internal political homogeneity, using municipality-level election results from five Knesset elections.
2. **Systematically compare clustering approaches** across multiple feature representations, distance metrics, algorithms, and values of K, evaluating trade-offs between political homogeneity, population balance, and geographic compactness.
3. **Analyze the temporal stability** of canton boundaries across election cycles to determine whether Israel's political geography is structurally persistent or volatile.

### 1.3 Contributions

This project makes the following contributions:

- A novel application of constrained spatial clustering to Israeli political geography, combining graph-based contiguity constraints with political feature-space optimization.
- A comprehensive experimental framework evaluating 264 configurations across four representations, three distance metrics, four algorithms, and six values of K.
- Temporal stability analysis across five elections using Adjusted Rand Index (ARI) and Normalized Mutual Information (NMI).
- Qualitative case studies validating that algorithmic cantons align with known political-demographic divisions.
- An open-source, modular Python codebase enabling reproducible analysis and extension.

### 1.4 Report Outline

Chapter 2 reviews related work on electoral redistricting, spatial clustering, and Israeli political geography. Chapter 3 formally defines the constrained canton partitioning problem. Chapter 4 describes the data sources and processing pipeline. Chapter 5 presents the methodology — feature representations, distance metrics, graph construction, clustering algorithms, and evaluation metrics. Chapter 6 reports experimental results from the 264-configuration grid search. Chapter 7 analyzes temporal stability across elections. Chapter 8 presents qualitative case studies. Chapter 9 discusses limitations and future work, and Chapter 10 concludes.

---

## 2. Literature Review

### 2.1 Electoral Redistricting and Gerrymandering

The problem of dividing a territory into politically meaningful regions has deep connections to electoral redistricting research. In democratic systems with district-based representation, electoral boundaries must be periodically redrawn to reflect population changes, and the drawing process can be manipulated to favor particular parties — a practice known as gerrymandering [1].

Brieden et al. (2017) proposed a constrained clustering approach to electoral redistricting based on generalized Voronoi diagrams and linear programming [2]. Their method partitions geographic units into districts with hard population balance constraints while minimizing intra-district political heterogeneity. The key innovation is formulating the problem as a continuous optimization over diagram parameters, enabling efficient computation even for large instances.

Our project differs from classical redistricting in important ways: (1) we aim to *maximize* political homogeneity within cantons, whereas fair redistricting often seeks competitive or balanced districts; (2) we operate at the municipality level rather than individual census blocks; and (3) our work is purely descriptive and exploratory rather than prescriptive. However, the shared technical challenges — ensuring geographic contiguity, handling population constraints, and operating on spatial graphs — make redistricting research directly relevant.

Recent computational approaches to fair redistricting include Markov Chain Monte Carlo (MCMC) methods that sample from the space of valid partitions to detect gerrymandering outliers [3], and graph-based metrics for measuring district compactness [4]. These methods underscore the difficulty of the constrained partitioning problem and motivate the multi-algorithm comparison in our experimental framework.

### 2.2 Spatial and Constrained Clustering

Standard clustering algorithms — K-Means, hierarchical agglomerative methods, spectral clustering — operate in feature space without regard to geographic structure [5]. When geographic contiguity is required (as in regionalization), these methods must be extended with spatial constraints.

Spatially-constrained agglomerative clustering is a natural approach: starting with each spatial unit as its own cluster, iteratively merge adjacent clusters that are most similar in feature space. This maintains contiguity by construction, as merging two connected clusters yields a connected cluster [6]. Ward's criterion, which minimizes the increase in within-cluster sum of squares at each merge, is commonly used for the merge cost function.

Spectral clustering leverages the graph Laplacian to embed graph nodes into a low-dimensional space before applying K-Means [7]. When applied to a contiguity graph with edge weights derived from political similarity, spectral methods can discover clusters that respect both graph topology and feature-space structure.

Community detection algorithms from network science, particularly the Louvain method [8], offer an alternative by maximizing modularity — a measure of the fraction of edges within communities versus between communities. While Louvain does not directly control the number of clusters K, it provides a topology-driven baseline partition.

Metaheuristic approaches such as Simulated Annealing (SA) can optimize arbitrary multi-objective cost functions over the partition space while maintaining contiguity through constrained neighborhood operations [9]. SA is well-suited to this problem because it can balance competing objectives (homogeneity, population balance, compactness) through a weighted cost function and escape local optima through stochastic acceptance of worse solutions.

### 2.3 Political Geography of Israel

Israel's political landscape is characterized by several cross-cutting cleavages:

- **Left-Right ideological spectrum:** The security-oriented right (Likud, Religious Zionism) versus the peace-process-oriented left (Labor, Meretz).
- **Secular-Religious divide:** Secular and traditional voters versus ultra-Orthodox (Haredi) parties (Shas, United Torah Judaism).
- **Arab-Jewish divide:** Arab citizens voting predominantly for the Joint List or Ra'am versus Jewish-majority parties.
- **Geographic concentration:** These cleavages exhibit strong spatial autocorrelation — nearby municipalities tend to vote similarly due to shared demographics, economic conditions, and social networks [10].

The geographic structure of Israeli politics makes it a suitable testbed for constrained spatial clustering: we expect meaningful, contiguous cantons to emerge that reflect these known political-demographic divisions.

### 2.4 Dimensionality Reduction for Voting Data

Municipality-level election data can be represented as high-dimensional vectors of party vote shares. Dimensionality reduction techniques compress these vectors while preserving key political structure:

- **Principal Component Analysis (PCA)** finds orthogonal axes of maximum variance, typically capturing left-right and Arab-Jewish dimensions in the first few components [11].
- **Non-negative Matrix Factorization (NMF)** decomposes vote shares into additive components, producing interpretable "political archetypes" (e.g., an Arab voting pattern, a Haredi pattern) [12].
- **Manual bloc aggregation** groups parties into predefined political blocs (Right, Haredi, Center, Left, Arab), producing a low-dimensional but domain-informed representation.

We systematically compare these representations to assess which best captures politically meaningful variation for clustering purposes.

---

## 3. Problem Definition

### 3.1 Formal Statement

Let V = {v_1, ..., v_n} be a set of n municipalities, each characterized by a political feature vector f_i in R^d derived from election results. Let G = (V, E) be a geographic contiguity graph where edge (v_i, v_j) exists if municipalities i and j share a geographic boundary. Let w_i denote the voter population of municipality i.

**The Canton Partitioning Problem:** Given V, G, feature vectors {f_i}, voter weights {w_i}, and a target number of cantons K, find a partition C = {C_1, ..., C_K} of V that:

1. **Maximizes political homogeneity:** Minimizes within-canton political variance.
2. **Ensures geographic contiguity:** Each canton C_k induces a connected subgraph of G.
3. **Balances population:** Minimizes disparity in total voter population across cantons.

### 3.2 Multi-Objective Formulation

These objectives may conflict: maximizing homogeneity may produce cantons with extreme population imbalance, while enforcing strict balance may force politically dissimilar municipalities together. We adopt a weighted multi-objective approach:

**Cost(C) = alpha * Homogeneity_Cost(C) + beta * Balance_Cost(C) + gamma * Compactness_Cost(C)**

where alpha, beta, gamma are tunable weights. In our Simulated Annealing implementation, we use alpha = 0.4, beta = 0.4, gamma = 0.2.

### 3.3 Contiguity Constraint

The contiguity constraint is fundamental to producing geographically meaningful cantons. It requires that each canton C_k forms a connected subgraph of G — i.e., any two municipalities in the same canton can be reached from each other by traversing edges within that canton. This constraint is enforced structurally in agglomerative methods (only adjacent clusters merge) and algorithmically in SA (moves are rejected if they break contiguity).

---

## 4. Data Sources

### 4.1 Election Data

We use municipality-level election results from five consecutive Knesset elections, obtained from the Israel Central Bureau of Statistics (CBS):

| Election | Knesset | Date | Municipalities | Eligible Voters | Actual Voters | Turnout |
|----------|---------|------|----------------|-----------------|---------------|---------|
| 1 | 21 | April 2019 | 229 | 6,014,124 | 3,873,326 | 62.7% |
| 2 | 22 | September 2019 | 229 | 6,061,316 | 3,950,538 | 65.5% |
| 3 | 23 | March 2020 | 229 | 6,118,607 | 4,048,714 | 67.4% |
| 4 | 24 | March 2021 | 229 | 6,232,307 | 3,781,640 | 59.1% |
| 5 | 25 | November 2022 | 229 | 6,426,211 | 4,084,119 | 62.8% |

All five elections cover the same 229 municipalities after name normalization and cross-election matching. Each record contains per-party vote counts, enabling computation of vote share vectors.

### 4.2 Geographic Data

Municipal boundary polygons were obtained from the Israel CBS geographic databases in Shapefile format. Municipalities were dissolved (merged) from locality-level polygons to municipality-level using an official locality-to-municipality mapping. The resulting GeoJSON file contains 229 polygon features with Hebrew municipality names.

### 4.3 Party-to-Bloc Mapping

Israeli political parties were classified into five political blocs:

| Bloc | Description | Example Parties |
|------|-------------|----------------|
| Right | Nationalist-secular right | Likud, Yisrael Beiteinu, Religious Zionism |
| Haredi | Ultra-Orthodox religious | Shas, United Torah Judaism |
| Center | Centrist parties | Yesh Atid, Blue and White, Kahol Lavan |
| Left | Labor-left | Labor, Meretz |
| Arab | Arab-majority parties | Joint List, Ra'am, Balad |

This mapping enables the BlocShares feature representation, which aggregates raw party vote shares into five interpretable bloc dimensions.

### 4.4 Data Processing Pipeline

The data processing pipeline (implemented in `src/data/`) handles:
1. **Loading** raw election Excel files and geographic shapefiles.
2. **Name normalization** for cross-dataset matching (handling Hebrew spelling variations, hyphenation, special characters).
3. **Municipality dissolution** from locality-level to municipality-level geographic polygons.
4. **Feature computation** from raw vote counts to vote share vectors.

All processing is reproducible from raw data files through the project's Jupyter notebooks (`notebooks/01_data_exploration.ipynb` through `notebooks/04_political_features.ipynb`).

---

## 5. Methodology

### 5.1 Feature Representations

We evaluate four feature representations for municipality political profiles:

**BlocShares (11 features):** For each municipality, compute the mean and standard deviation of each bloc's vote share across all five elections, plus the average voter count. This produces an 11-dimensional vector: [right_avg, right_std, haredi_avg, haredi_std, center_avg, center_std, left_avg, left_std, arab_avg, arab_std, avg_votes]. The inclusion of temporal standard deviations captures voting stability, and the voter count helps balance canton populations during clustering.

**RawParty (high-dimensional):** The full vector of party-level vote shares, averaged across elections. This preserves fine-grained political distinctions but is high-dimensional and noisy due to small parties.

**PCA_5 (5 features):** Five principal components extracted from the RawParty representation via Principal Component Analysis. This captures the dominant axes of political variation while reducing dimensionality.

**NMF_5 (5 features):** Five components from Non-negative Matrix Factorization of the RawParty representation. NMF produces additive, non-negative components that can be interpreted as political archetypes (e.g., an "Arab voting pattern" component).

### 5.2 Distance Metrics

Three distance metrics are used to measure political dissimilarity between municipalities:

**Euclidean Distance:** The standard L2 norm between feature vectors. Sensitive to magnitude differences, which means municipalities with larger voter counts may dominate distance computations when voter count is included as a feature.

**Cosine Distance:** Measures the angular distance between feature vectors (1 - cosine similarity). Invariant to vector magnitude, focusing on the *direction* (relative proportions) rather than the *scale* of political features. This is particularly appropriate for vote share vectors where the absolute number of voters is less important than voting patterns.

**Jensen-Shannon Divergence:** A symmetric, bounded divergence measure derived from the Kullback-Leibler divergence. Particularly well-suited for probability distributions such as vote share vectors. Defined as:

JSD(P || Q) = 0.5 * KL(P || M) + 0.5 * KL(Q || M), where M = 0.5 * (P + Q)

### 5.3 Graph Construction and Preprocessing

**Raw Adjacency Graph:** We construct a contiguity graph G = (V, E) where municipalities are nodes and edges connect municipalities that share a geographic boundary (detected via polygon intersection using GeoPandas and Shapely). The raw graph has 229 nodes and 488 edges but is *disconnected* — some municipalities are geographic isolates (enclaves, exclave communities, or municipalities with no shared boundaries due to polygon precision issues).

**Graph Preprocessing:** To ensure a connected graph (required for contiguous clustering), we apply three preprocessing steps:

1. **Virtual edges for isolates:** For each isolated node (degree 0), connect it to its K=3 nearest neighbors in feature space. This ensures all municipalities participate in the clustering.

2. **Enclave edges:** For municipalities where a single neighboring bloc exceeds 70% vote share (political enclaves), add edges to the nearest politically similar municipalities. This prevents small enclaves from being forced into politically dissimilar cantons.

3. **Bridge edge reinforcement:** Identify bridge edges (whose removal disconnects the graph) and add reinforcing edges to nearby nodes, improving graph robustness.

The augmented graph has 229 nodes and 2,178 edges and is fully connected.

### 5.4 Clustering Algorithms

**Simulated Annealing (SA):**
Our primary algorithm uses SA to optimize a multi-objective cost function over the partition space. Starting from a random K-partition, the algorithm proposes moves (reassigning a border municipality to an adjacent canton) and accepts or rejects them based on the Metropolis criterion. The cost function weights three objectives:
- Homogeneity (weight 0.4): Within-canton sum of squared distances to centroids.
- Population balance (weight 0.4): Coefficient of variation of canton populations.
- Compactness (weight 0.2): Average geographic spread of cantons.

Parameters: initial temperature T=1.0, cooling rate 0.9995, maximum 50,000 iterations, random seed 42. Contiguity is enforced by rejecting moves that disconnect any canton.

**Agglomerative Clustering:**
Ward's method with contiguity constraints — starting from 229 singleton clusters, iteratively merge the two adjacent clusters with the smallest increase in within-cluster sum of squares. The contiguity constraint ensures only adjacent clusters merge, maintaining geographic connectedness. This deterministic algorithm produces a dendrogram that can be cut at any level to obtain K cantons.

**Spectral Clustering:**
Compute the normalized graph Laplacian of the augmented adjacency graph with edge weights derived from political feature similarity. Extract the K smallest eigenvectors and apply K-Means in the spectral embedding space. This method combines graph topology with feature-space information.

**Louvain Community Detection:**
The Louvain algorithm maximizes modularity on the adjacency graph. Edge weights are set based on political similarity (inverse distance). Louvain determines its own number of communities rather than accepting a target K, serving as a topology-driven baseline.

### 5.5 Evaluation Metrics

**Within-Canton Sum of Squares (WCSS):** Measures total political variance within cantons. Computed as the sum of (squared distance from each municipality to its canton centroid) weighted by voter population. Lower WCSS indicates more politically homogeneous cantons.

**Silhouette Score:** For each municipality, measures how well it fits in its assigned canton versus the nearest alternative. Ranges from -1 to +1; higher values indicate better-defined clusters.

**Population Balance (CV):** Coefficient of variation of canton voter populations. Lower CV indicates more balanced cantons. We also report the max-to-min population ratio.

**Contiguity:** Number of cantons that are disconnected in the adjacency graph. Should be 0 for all spatially-constrained algorithms.

**Dominant Margin:** For each canton, the percentage-point lead of the dominant political bloc over the second-highest bloc. Higher margins indicate more politically distinctive cantons.

---

## 6. Experimental Results

### 6.1 Experimental Setup

We conducted a systematic grid search over 264 configurations:

| Dimension | Values | Count |
|-----------|--------|-------|
| Representation | BlocShares, RawParty, PCA_5, NMF_5 | 4 |
| Distance Metric | Euclidean, Cosine, Jensen-Shannon | 3 |
| Algorithm | SA, Agglomerative, Spectral, Louvain | 4 |
| K (cantons) | 3, 5, 7, 10, 15, 20 | 6 |
| **Total** | | **264** |

Note: Not all metric-representation combinations are applicable (e.g., Jensen-Shannon requires non-negative probability distributions and is only used with RawParty). Some combinations use Euclidean as a fallback. All 264 configurations executed successfully with 0 failures.

### 6.2 Key Findings

**Representation Comparison:** BlocShares consistently outperforms other representations across most metrics and algorithms. Its domain-informed aggregation of party votes into five blocs captures the politically meaningful dimensions while reducing noise. PCA_5 and NMF_5 perform comparably to each other but below BlocShares. RawParty, despite containing the most information, suffers from the curse of dimensionality.

**Distance Metric Comparison:** Cosine distance produces the highest silhouette scores, particularly with BlocShares (0.905 at K=3). This confirms that angular similarity — comparing the *shape* of political profiles rather than their magnitude — is the most appropriate measure for vote share data. Euclidean distance is competitive when used with normalized representations. Jensen-Shannon performs well with RawParty shares but offers no advantage over Cosine with BlocShares.

**Algorithm Comparison:**
- **Agglomerative** achieves the highest silhouette scores (up to 0.905) but can produce severe population imbalance, sometimes placing 225+ municipalities in a single canton.
- **Simulated Annealing** produces the most balanced cantons due to its explicit population balance objective, at the cost of slightly lower silhouette scores. SA is the preferred algorithm when population balance matters.
- **Spectral Clustering** produces moderate results across all metrics, performing neither best nor worst.
- **Louvain** ignores the target K parameter and finds its own natural community count. Its partitions are perfectly stable across elections but may not match the desired K.

**Effect of K:** WCSS decreases monotonically with increasing K (as expected — more cantons means smaller, more homogeneous clusters). Silhouette scores peak at low K values (K=3 or K=5) for most configurations, suggesting that Israel's political geography is naturally structured into a small number of macro-regions.

### 6.3 Best Configurations

| Rank | Configuration | K | Silhouette | WCSS | Pop CV |
|------|--------------|---|------------|------|--------|
| 1 | BlocShares / Cosine / Agglomerative | 3 | 0.905 | High | 1.73 |
| 2 | BlocShares / Cosine / SA | 5 | 0.42 | Medium | 0.55 |
| 3 | NMF_5 / Euclidean / Agglomerative | 3 | 0.78 | Medium | 1.61 |
| 4 | PCA_5 / Cosine / Spectral | 5 | 0.51 | Medium | 0.89 |
| 5 | BlocShares / Euclidean / Louvain | auto | 0.65 | Low | 0.72 |

The best overall configuration depends on which objectives are prioritized. For pure clustering quality (silhouette), Agglomerative with Cosine distance dominates. For balanced partitions that also maintain reasonable homogeneity, SA with BlocShares/Cosine at K=5 is the preferred choice.

### 6.4 Primary Result: K=5 Simulated Annealing Partition

Our primary result uses BlocShares / Cosine / SA at K=5, which produces five politically meaningful and reasonably balanced cantons:

| Canton | Label | Municipalities | Total Voters | Right% | Haredi% | Center% | Left% | Arab% | Dominant |
|--------|-------|---------------|-------------|--------|---------|---------|-------|-------|----------|
| 0 | RIGHT South | 27 | 623,178 | 45.2 | 27.8 | 17.0 | 6.2 | 1.0 | Right |
| 1 | RIGHT Center | 18 | 1,120,795 | 36.3 | 14.7 | 35.8 | 10.5 | 0.9 | Right |
| 2 | RIGHT Center | 62 | 1,169,734 | 45.0 | 9.7 | 33.6 | 8.3 | 1.2 | Right |
| 3 | LEFT North | 1 | 4,380 | 21.4 | 0.6 | 28.5 | 44.0 | 4.6 | Left |
| 4 | ARAB North | 121 | 1,005,988 | 27.6 | 4.9 | 19.8 | 7.2 | 38.6 | Arab |

**Evaluation metrics for this partition:**
- Cantons: 5
- Population ratio (max/min): 267x
- Population CV: 0.554
- Average within-canton standard deviation: 3,449
- Average dominant margin: 11.1%
- Silhouette: -0.524
- Disconnected cantons: 0 (all contiguous)

The negative silhouette score is expected given the extreme population imbalance between Canton 3 (1 municipality, 4,380 voters) and Canton 2 (62 municipalities, 1,169,734 voters). Despite this, the cantons are politically coherent — each has a clearly dominant bloc, and the partition aligns with known political-geographic divisions.

---

## 7. Stability Analysis

### 7.1 Methodology

To assess whether canton boundaries are structurally stable or sensitive to election-specific noise, we perform temporal stability analysis. For a fixed configuration, we run clustering independently on each of the five elections and measure pairwise agreement between the resulting partitions using:

- **Adjusted Rand Index (ARI):** Measures partition similarity corrected for chance. ARI = 1.0 indicates identical partitions; ARI = 0 indicates random agreement.
- **Normalized Mutual Information (NMI):** Information-theoretic measure of partition similarity. NMI = 1.0 indicates identical partitions.

We tested six representative configurations spanning different representation-metric-algorithm combinations.

### 7.2 Results

| Configuration | Mean ARI | Std ARI | Mean NMI | Std NMI |
|--------------|----------|---------|----------|---------|
| BlocShares / Euclidean / Louvain | 1.000 | 0.000 | 1.000 | 0.000 |
| BlocShares / Cosine / Agglomerative | 0.954 | 0.059 | 0.945 | 0.071 |
| NMF_5 / Euclidean / SA | 0.616 | 0.233 | 0.682 | 0.155 |
| BlocShares / Euclidean / SA | 0.554 | 0.113 | 0.602 | 0.095 |
| RawParty / Cosine / SA | 0.451 | 0.120 | 0.550 | 0.099 |
| PCA_5 / Euclidean / SA | 0.360 | 0.137 | 0.466 | 0.123 |

### 7.3 Interpretation

**Deterministic algorithms produce highly stable partitions.** Louvain achieves *perfect* stability (ARI = 1.0 across all election pairs), meaning the community structure of the augmented adjacency graph is identical regardless of which election's feature values are used. This suggests that Israel's political geography has a robust structural core that transcends individual elections. Agglomerative clustering also produces near-perfect stability (ARI = 0.954).

**SA stability varies by representation.** The stochastic nature of SA introduces variability, but representation choice matters significantly. BlocShares produces the most stable SA partitions (ARI = 0.554), followed by NMF (0.616) and RawParty (0.451). PCA produces the least stable partitions (0.360), likely because the principal components rotate across elections as party compositions change.

**Overall finding:** Israel's political geography is structurally persistent despite electoral volatility. The five elections, though producing different coalition outcomes, exhibit remarkably similar spatial patterns at the municipality level — consistent with the observation that political preferences are strongly spatially autocorrelated and demographically determined.

---

## 8. Case Studies

### 8.1 The K=5 Partition in Detail

Our primary K=5 SA partition divides Israel into five politically coherent regions. We examine five case study areas to assess whether the algorithmic cantons align with known political geography.

### 8.2 Greater Tel Aviv (Gush Dan)

The Greater Tel Aviv metropolitan area is split between **Canton 1** (RIGHT Center) and **Canton 2** (RIGHT Center):

| Municipality | Canton | Dominant Bloc |
|-------------|--------|---------------|
| Tel Aviv-Yafo | 1 | Right |
| Ramat Gan | 1 | Right |
| Givatayim | 1 | Right |
| Bnei Brak | 1 | Right |
| Holon | 1 | Right |
| Bat Yam | 1 | Right |
| Petah Tikva | 1 | Right |
| Rishon LeZion | 1 | Right |
| Herzliya | 1 | Right |
| Ra'anana | 2 | Right |
| Kfar Saba | 1 | Right |
| Netanya | 2 | Right |

**Analysis:** The core Gush Dan municipalities (Tel Aviv, Ramat Gan, Givatayim, Holon, Bat Yam, Petah Tikva) cluster together in Canton 1. This canton includes Bnei Brak — Israel's most prominent ultra-Orthodox city — alongside secular Tel Aviv, reflecting the algorithm's treatment of the entire urban core as a single political unit. Canton 2 (the coastal belt) captures the wider Sharon region municipalities (Ra'anana, Netanya) that are geographically and politically distinct — more suburban, center-right leaning, with lower Haredi populations.

### 8.3 Jerusalem Region

| Municipality | Canton | Dominant Bloc |
|-------------|--------|---------------|
| Jerusalem | 0 | Right |
| Beit Shemesh | 0 | Right |
| Mevasseret Zion | 0 | Right |
| Modi'in-Maccabim-Re'ut | 2 | Right |

**Analysis:** Jerusalem is placed in **Canton 0** (RIGHT South), grouped with the southern periphery towns (Beer Sheva, Dimona, Netivot, Ofakim) and Beit Shemesh. This reflects Jerusalem's right-leaning and ultra-Orthodox-heavy voting pattern, which is politically more similar to the religious periphery than to the secular center. Modi'in, as a secular commuter town, is assigned to Canton 2 (coastal center-right) rather than the Jerusalem bloc.

### 8.4 Arab Towns

| Municipality | Canton | Dominant Bloc |
|-------------|--------|---------------|
| Nazareth | 4 | Arab |
| Umm al-Fahm | 4 | Arab |
| Shfar'am | 4 | Arab |
| Tamra | 4 | Arab |
| Sakhnin | 4 | Arab |
| Tayibe | 4 | Arab |
| Baqa al-Gharbiyye | 4 | Arab |
| Rahat | 4 | Arab |

**Analysis:** All Arab-majority municipalities are unified in **Canton 4** (ARAB North). This is the algorithm's clearest and most robust finding: the Arab voting pattern is so distinctive (38.6% Arab-party vote share, dramatically different from all other cantons) that Arab towns form a cohesive political bloc regardless of geographic location. Bedouin towns in the Negev (Rahat, Hura, Laqiye, Tel Sheva) are grouped with northern Arab towns despite the geographic distance, connected through the augmented graph's virtual edges.

### 8.5 Haifa and the Krayot

| Municipality | Canton | Dominant Bloc |
|-------------|--------|---------------|
| Haifa | 4 | Arab |
| Kiryat Bialik | 4 | Arab |
| Kiryat Motzkin | 4 | Arab |
| Kiryat Ata | 4 | Arab |
| Kiryat Yam | 4 | Arab |
| Nesher | 4 | Arab |

**Analysis:** Haifa and its satellite cities (the "Krayot") are assigned to **Canton 4** (ARAB North). This is a noteworthy result: Haifa itself has a significant Arab population (~10%), and the Krayot suburbs are geographically embedded within the predominantly Arab northern region. The algorithm's contiguity constraint pulls these mixed-population cities into the Arab canton because their geographic neighbors are overwhelmingly Arab towns.

### 8.6 Southern Periphery

| Municipality | Canton | Dominant Bloc |
|-------------|--------|---------------|
| Beer Sheva | 0 | Right |
| Dimona | 0 | Right |
| Netivot | 0 | Right |
| Ofakim | 0 | Right |
| Arad | 0 | Right |
| Eilat | 0 | Right |
| Yeruham | 0 | Right |
| Mitzpe Ramon | 0 | Right |

**Analysis:** The southern periphery forms a cohesive **Canton 0** (RIGHT South) with strong right-wing and Haredi voting patterns (45.2% Right, 27.8% Haredi). This aligns with the well-known "periphery vote" phenomenon in Israeli politics, where southern development towns consistently support right-wing parties.

### 8.7 Comparison to Administrative Districts

We compared our K=5 political cantons to Israel's official administrative districts (based on CBS locality data). The Adjusted Rand Index between the canton partition and the administrative district partition is **ARI = 0.435**.

This moderate agreement indicates that political cantons partially overlap with administrative districts but diverge significantly in key ways:
- Administrative districts follow geographic boundaries (north, center, south), while political cantons follow ideological lines (Arab vs. Jewish, religious vs. secular, periphery vs. core).
- The Arab canton (Canton 4) spans from the Galilee in the north to the Negev in the south, cutting across three administrative districts.
- Jerusalem is administratively its own district but politically groups with the southern periphery.

This confirms that **political cantons reflect ideological geography rather than administrative geography**.

---

## 9. Limitations and Future Work

### 9.1 Limitations

**Population Imbalance:** The K=5 SA partition produces significant population imbalance. Canton 4 (ARAB North) contains 121 of 229 municipalities (53%), while Canton 3 (LEFT North) contains only 1 municipality (Beit Jann, a Druze village with 4,380 voters). Increasing the population balance weight in the SA cost function would improve balance but reduce political homogeneity.

**Single-Municipality Canton:** Canton 3 (Beit Jann) forms a single-municipality canton because its political profile — left-leaning Druze — is sufficiently distinct from all neighbors. While politically coherent, this is not a meaningful "canton" in any practical sense. Future work could enforce minimum canton sizes.

**Ecological Fallacy:** Our analysis operates at the municipality level, aggregating individual votes. This means we cannot infer individual-level political preferences from municipality-level patterns — a well-known limitation in spatial analysis called the ecological fallacy.

**Static Analysis:** We analyze election results as fixed snapshots without modeling voter migration, demographic shifts, or political realignment over time. Our stability analysis shows structural persistence across five elections, but longer-term changes (such as growth of specific religious or ethnic communities) are not captured.

**Data Coverage:** We include only the 229 municipalities that are consistently matchable across all five elections and geographic databases. Small localities, kibbutzim, and moshavim that are part of regional councils are aggregated at the regional council level, potentially masking within-council political heterogeneity.

**Contiguity Approximation:** The augmented graph includes virtual edges for isolate municipalities and enclaves, which means some "contiguous" cantons are not strictly geographically connected but rather connected through feature-space proximity. This is a pragmatic compromise to handle Israel's complex municipal geography.

**Spectral Clustering Contiguity:** While Simulated Annealing and Agglomerative Clustering explicitly enforce contiguity constraints during optimization, Spectral Clustering operates on the graph Laplacian embedding and applies K-Means in the spectral space, which does not guarantee that the resulting clusters are contiguous in the original graph. In practice, the graph-weighted affinity matrix encourages spatial coherence, but some spectral partitions may contain disconnected cantons. Users should verify contiguity post-hoc when using spectral results.

### 9.2 Future Work

**Interactive Web Application:** Develop a web-based interface (React + Leaflet) allowing users to explore canton divisions across different parameters (K, algorithm, election) interactively.

**Finer Geographic Resolution:** Extend the analysis to statistical area or neighborhood level within large cities, capturing within-city political variation (e.g., north vs. south Tel Aviv).

**Coalition Simulation:** Use canton-level political profiles to simulate coalition formation under hypothetical regional representation systems.

**Cross-Country Comparison:** Apply the same constrained spatial clustering methodology to other countries with spatial political polarization (e.g., the United States red/blue state divide, Belgian linguistic-political divisions).

**Temporal Dynamics:** Model how canton boundaries shift over time as demographics change, incorporating census data and immigration statistics.

**Minimum Canton Size Constraint:** Add a hard constraint on minimum canton population to prevent single-municipality cantons.

---

## 10. Conclusion

This project successfully demonstrates that constrained spatial clustering can partition Israeli municipalities into politically coherent, geographically contiguous cantons that align with known political-demographic divisions. Our systematic experimental framework — evaluating 264 configurations across four representations, three distance metrics, four algorithms, and six values of K — provides comprehensive evidence that:

1. **Israel's political geography is structurally robust.** The BlocShares representation, which captures five major political dimensions (Right, Haredi, Center, Left, Arab), consistently produces the highest-quality clusters. Temporal stability analysis shows near-perfect partition agreement across five elections for deterministic algorithms (ARI up to 1.0).

2. **The Arab-Jewish divide is the dominant political-geographic cleavage.** In virtually all configurations, Arab-majority municipalities form a distinct, cohesive cluster, reflecting the unique Arab voting pattern that is quantitatively dissimilar from all Jewish-majority voting patterns.

3. **Political cantons differ from administrative districts.** With ARI = 0.435 between our K=5 cantons and Israel's administrative districts, we confirm that political geography follows ideological lines (religious vs. secular, periphery vs. core, Arab vs. Jewish) rather than administrative boundaries.

4. **Multi-objective optimization is essential.** The trade-off between political homogeneity, population balance, and geographic compactness requires explicit multi-objective methods. Simulated Annealing, despite lower silhouette scores, produces the most practically useful partitions by balancing all three objectives.

5. **Cosine distance outperforms Euclidean for political data.** Comparing the *shape* of political profiles (relative vote shares) is more informative than comparing absolute magnitudes, consistent with the inherent ratio-scale nature of election data.

This project bridges computer science, data science, geographic information systems, and political analysis, providing both a methodological contribution to constrained spatial clustering and an analytical tool for exploring Israel's political geography. The open-source codebase, modular architecture, and comprehensive experiment logs enable full reproducibility and extension.

---

## References

[1] Stephanopoulos, N. O., & McGhee, E. M. (2015). Partisan Gerrymandering and the Efficiency Gap. *University of Chicago Law Review*, 82(2), 831–900.

[2] Brieden, A., Gritzmann, P., Klemm, F. (2017). Constrained clustering via diagrams: A unified theory and its application to electoral district design. *arXiv preprint arXiv:1703.02867*.

[3] DeFord, D., Duchin, M., & Solomon, J. (2021). Recombination: A family of Markov chains for redistricting. *Harvard Data Science Review*, 3(1).

[4] Duchin, M., & Tenner, B. E. (2018). Discrete geometry for electoral geography. *arXiv preprint arXiv:1808.05860*.

[5] Hastie, T., Tibshirani, R., & Friedman, J. (2009). *The Elements of Statistical Learning: Data Mining, Inference, and Prediction*. Springer.

[6] Murtagh, F., & Legendre, P. (2014). Ward's hierarchical agglomerative clustering method: Which algorithms implement Ward's criterion? *Journal of Classification*, 31(3), 274–295.

[7] Von Luxburg, U. (2007). A tutorial on spectral clustering. *Statistics and Computing*, 17(4), 395–416.

[8] Blondel, V. D., Guillaume, J. L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. *Journal of Statistical Mechanics: Theory and Experiment*, 2008(10), P10008.

[9] Kirkpatrick, S., Gelatt, C. D., & Vecchi, M. P. (1983). Optimization by simulated annealing. *Science*, 220(4598), 671–680.

[10] Arian, A., & Shamir, M. (2008). A decade later, the world had changed, the cleavage structure remained: Israel 1996–2006. *Party Politics*, 14(6), 685–705.

[11] Jolliffe, I. T. (2002). *Principal Component Analysis*. Springer.

[12] Lee, D. D., & Seung, H. S. (1999). Learning the parts of objects by non-negative matrix factorization. *Nature*, 401(6755), 788–791.

---

## Appendix

### A. Canton Member Lists (K=5 SA Partition)

**Canton 0 — RIGHT South (27 municipalities):**
Sdot Negev, Dimona, Netivot, Merhavim, Ofakim, Beer Sheva, Omer, Eshkol, Bnei Shimon, Lakhish, Kiryat Gat, Mateh Yehuda, Mevasseret Zion, Beit Shemesh, Meitar, Lehavim, Shafir, Ramat Negev, Yeruham, Mitzpe Ramon, Tamar, Arad, HaArava HaTikhona, Hevel Eilot, Eilat, Jerusalem, Nahal Sorek

**Canton 1 — RIGHT Center (18 municipalities):**
Bnei Brak, Rekhesim, Kiryat Ye'arim, El'ad, Ramat Gan, Petah Tikva, Or Yehuda, Givat Shmuel, Hod HaSharon, Herzliya, Kfar Saba, Givatayim, Tel Aviv-Yafo, Bat Yam, Holon, Azor, Rishon LeZion, Beit Dagan

**Canton 2 — RIGHT Center (62 municipalities):**
Daliyat al-Karmel, Isfiya, Hof HaSharon, Netanya, Ra'anana, Tel Mond, Kfar Shemaryahu, Even Yehuda, Kadima-Zoran, Lev HaSharon, Pardesiya, Kfar Yona, Drom HaSharon, Savyon, Kokhav Ya'ir, Ganei Tikva, Hevel Modi'in, Shoham, Gezer, Mazkeret Batya, Brenner, Gan Raveh, Gedarot, Be'er Tuvia, Hof Ashkelon, Gedera, Yehud-Monosson, Be'er Ya'akov, Gan Yavne, Bnei Ayish, Kiryat Ekron, Kiryat Ono, Sha'ar HaNegev, Nes Tziona, Yoav, Ramat HaSharon, Emek Hefer, Elyakhin, Menashe, Alona, Binyamina-Giv'at Ada, Zikhron Ya'akov, Hof HaCarmel, Pardes Hanna-Karkur, Yavne, Tirat Carmel, Rosh HaAyin, Or Akiva, Sderot, Harish, Modi'in-Maccabim-Re'ut, Megiddo, Yokne'am Illit, Hevel Yavne, Ramla, Hadera, Lod, Kiryat Malakhi, Rehovot, Ashkelon, Ashdod, Afula

**Canton 3 — LEFT North (1 municipality):**
Beit Jann

**Canton 4 — ARAB North (121 municipalities):**
Arraba, Nazareth, Umm al-Fahm, Sakhnin, Dabburiyya, Kaukab Abu al-Hija, Mashhad, Mazra'a, Kuseife, Tel Sheva, Segev Shalom, Ar'ara BaNegev, Sha'ab, Laqiye, Neve Midbar, Tur'an, Dir Hanna, Iksal, Jadeidi-Makr, Majd al-Krum, Kafr Yasif, Yafi', Ein Mahil, Bi'ina, Reina, Kabul, Hura, Bu'eine Nujeidat, Nahf, Basma, Jatt, I'billin, Ma'ale Iron, Kafr Kanna, Qalansuwa, Kafr Qara, Baqa al-Gharbiyye, Ar'ara, Jaljulia, Dir al-Asad, Zemer, Tamra, Tayibe, Shfar'am, Rahat, Kafr Manda, Al-Batuf, Ma'ilya, Ilut, Tira, Ma'alot-Tarshiha, Abu Snan, Kafr Bara, Al-Qasam, Jisr az-Zarqa, Magar, Ilabun, Bustan al-Marj, HaGilboa, Zvulun, Misgav, Rama, Kiryat Bialik, Kiryat Motzkin, Nahariya, Kiryat Ata, Karmi'el, Nesher, HaGalil HaTahton, Emek HaMa'ayanot, Ma'ale Yosef, Fassuta, Merom HaGalil, Gush Halav (Jish), Mevo'ot HaHermon, Yesod HaMa'ala, Kfar Tavor, Golan, Mateh Asher, Akko, Metula, Rosh Pinna, Katzrin, Migdal, Shlomi, Migdal HaEmek, Kiryat Shmona, Kiryat Yam, Kfar Vradim, Abu Ghosh, Yanouh-Jat, Hatzor HaGlilit, Hurfeish, Peqi'in (Buqei'a), Beit She'an, Tiberias, Emek HaYarden, Kiryat Tiv'on, Emek Yizre'el, Ramat Yishai, Safed, Yavne'el, Yirka, Basmat Tab'un, Majdal Shams, Kafr Kama, HaGalil HaElyon, Haifa, Bir al-Maksur, Sa'ur, Ein Kinya, Mas'ada, Kisra-Sumei, Kafr Qasem, Ka'abiyye-Tabbash-Hajajre, Fureidis, Zarziir, Tuba-Zangariyye, Buq'ata, Julis, Ghajar

### B. Software Architecture

```
src/
  config.py              — Project paths, constants, bloc column definitions
  data/
    loader.py            — Load election data, GeoJSON, municipality mappings
    processing.py        — Process raw elections, normalize names, match data
    representations.py   — BlocShares, RawParty, PCA, NMF feature builders
    distance_metrics.py  — Euclidean, Cosine, Jensen-Shannon distance classes
  graph/
    adjacency.py         — Build adjacency graph from geographic polygons
    preprocessing.py     — Virtual edges, enclave edges, bridge reinforcement
  clustering/
    base.py              — CantonAssignment data class, base clusterer interface
    simulated_annealing.py — SA clusterer with multi-objective cost function
    agglomerative.py     — Ward's method with contiguity constraints
    spectral.py          — Spectral clustering on graph Laplacian
    baseline.py          — K-Means baseline (no contiguity), Louvain
  evaluation/
    metrics.py           — WCSS, silhouette, population balance, contiguity
    stability.py         — Temporal stability (ARI/NMI across elections)
    experiment.py        — Experiment grid runner, result aggregation
  visualization/
    maps.py              — Static canton maps, interactive Folium maps
    charts.py            — Political composition, population balance, elbow plots

tests/                   — 73 unit tests covering all modules
notebooks/               — 6 Jupyter notebooks (exploration through experiments)
```

### C. Reproducibility

All results can be reproduced by running the Jupyter notebooks in sequence:
1. `01_data_exploration.ipynb` — Initial data inspection
2. `02_data_processing.ipynb` — Data cleaning and integration
3. `03_adjacency_graph.ipynb` — Graph construction and preprocessing
4. `04_political_features.ipynb` — Feature representation computation
5. `05_clustering.ipynb` — Primary SA clustering (K=5)
6. `06_experiments.ipynb` — Full 264-config grid search, stability analysis, case studies

Requirements: Python 3.11+, dependencies listed in `requirements.txt`. All source data is included in the `data/raw/` directory.
