---
title: "Partitioning Israeli Municipalities into Politically Homogeneous Cantons: A Constrained Spatial Clustering Approach"
author: "Adir Elmakais (ID: 316413640)"
date: "M.Sc. in Computer Science (Project Track), Bar-Ilan University, 2025-2026"
geometry: margin=2.5cm
fontsize: 12pt
header-includes:
  - \usepackage{amsmath}
  - \usepackage{amssymb}
---

**Advisor:** Dr. Oren Glickman, Department of Computer Science, Bar-Ilan University

*Revised October 2026.* All results were regenerated after correcting the party-to-bloc mapping: the Religious Zionist Party (March 2021), Otzma Yehudit (March 2020) and Jewish Home (November 2022) had not been assigned to any bloc. This revision also computes silhouette scores in each configuration's own distance metric, reports canton profiles weighted by voters, reports cross-election stability for the primary configuration itself, makes Simulated Annealing reproducible for a given seed, and corrects the comparison with administrative districts. It also adds the 23 Israeli local authorities in Judea and Samaria (Section 4.2), restores three municipalities inside the Green Line that had been dropped by name mismatches (Nof HaGalil, Sdot Dan and Shibli-Umm al-Ghanam), maps the cantons of each election separately (Section 7.4) and tests differences between cantons on an election the map did not use (Section 7.5). With these municipalities the primary partition changes: the seven predominantly Haredi cities form a canton of their own and the two Arab cantons merge.

---

## Abstract

Israeli society has experienced significant political polarization in recent years, reflected in five Knesset elections held within a four-year period (2019-2022). Public discourse increasingly references hypothetical divisions of the country into politically homogeneous "cantons." This project develops a data-driven algorithmic approach to explore such divisions using publicly available municipality-level election results and geographic boundary data from the Israel Central Bureau of Statistics (CBS).

We partition 255 Israeli municipalities, including the Israeli local authorities in Judea and Samaria, into geographically contiguous cantons that maximize internal political similarity. Our methodology employs four clustering algorithms - Simulated Annealing, Agglomerative Clustering with contiguity constraints, Louvain Community Detection, and K-Means (baseline) - evaluated across four feature representations (BlocShares, RawParty, PCA, NMF), three distance metrics (Euclidean, Cosine, Jensen-Shannon), and six values of K (3-20), yielding a comprehensive grid of experimental configurations.

Key results show that the BlocShares representation produces the highest clustering quality for unconstrained algorithms (silhouette score 0.987 with Cosine distance, 0.910 with Euclidean), while NMF_5 with Louvain community detection achieves the best balance between political homogeneity, silhouette quality (0.180), and interpretable canton assignments. Temporal stability analysis across all five elections reveals that deterministic algorithms (Louvain, Agglomerative) produce highly stable partitions (ARI 0.954--0.992 for the BlocShares configurations; 0.909 for the primary NMF_5/Louvain partition), while Israel's political geography remains structurally consistent despite electoral volatility. The resulting K=5 partition identifies five politically coherent regions: a mixed center-right metropolitan core around Tel Aviv, a right-wing region from Jerusalem through the south and the Judea and Samaria authorities, a right-leaning northern region, an Arab canton, and a canton of the seven predominantly Haredi cities, which is held together by political similarity rather than shared borders. Built from the 2019--2021 elections only, the cantons still differ significantly in every bloc's vote share in the held-out 2022 election. Comparison with Israel's administrative districts yields an Adjusted Rand Index of 0.360, confirming that political cantons follow ideological rather than administrative boundaries. These findings provide a data-driven framework for understanding Israel's latent political geography and demonstrate the applicability of constrained spatial clustering to politically polarized societies.

---

## 1. Introduction

### 1.1 Motivation

Over the past four years, Israel held five Knesset elections (April 2019, September 2019, March 2020, March 2021, and November 2022), an unprecedented frequency that reflects deep political divisions across multiple dimensions: secular versus religious, left versus right on the ideological spectrum, Arab versus Jewish communal politics, and attitudes toward judicial reform and governance. Throughout this period, public and media discourse repeatedly invoked the notion of dividing Israel into separate "cantons" along political lines - contrasting, for example, Tel Aviv's liberal-secular majority with Jerusalem's religious-conservative population, or the Arab-majority towns of northern Israel with predominantly Jewish communities elsewhere. The proposal was first set out in the Israeli press by Strenger and Yadid, who argued that Israel could be divided into autonomous cantons along these lines [31].

While such discourse is largely rhetorical, it raises a compelling computational question: if Israel were to be divided into politically coherent regions based purely on voting patterns, what form would those regions take, and how stable would they be across election cycles? This project applies data-driven computational methods to answer this question rigorously.

### 1.2 Research Objectives

This project has three primary objectives:

1. **Partition 255 Israeli municipalities into K geographically contiguous cantons** that maximize internal political homogeneity, using municipality-level election results from five Knesset elections.
2. **Systematically compare clustering approaches** across multiple feature representations, distance metrics, algorithms, and values of K, evaluating trade-offs between political homogeneity, population balance, and geographic compactness.
3. **Analyze the temporal stability** of canton boundaries across election cycles to determine whether Israel's political geography is structurally persistent or volatile.

### 1.3 Contributions

This project makes the following contributions:

- A novel application of constrained spatial clustering to Israeli political geography, combining graph-based contiguity constraints with political feature-space optimization.
- A comprehensive experimental framework evaluating 264 configurations across four representations, three distance metrics, four algorithms, and six values of K.
- Temporal stability analysis across five elections using Adjusted Rand Index (ARI) and Normalized Mutual Information (NMI).
- Qualitative case studies validating that algorithmic cantons align with known political-demographic divisions.
- A held-out test of differences between cantons, using an election that did not shape the map.
- An interactive Streamlit web application for exploring canton partitions, experiment results, and stability analysis (live at https://israel-cantons-project-5j7kgq8acxrbiflraqnhgb.streamlit.app/).
- An open-source, modular Python codebase enabling reproducible analysis and extension.

### 1.4 Report Outline

Section 2 reviews related work on electoral redistricting, spatial clustering, and Israeli political geography. Section 3 formally defines the constrained canton partitioning problem. Section 4 describes the data sources and processing pipeline. Section 5 presents the methodology - feature representations, distance metrics, graph construction, clustering algorithms, and evaluation metrics. Section 6 reports experimental results from the 264-configuration grid search. Section 7 analyzes temporal stability across elections. Section 8 presents qualitative case studies. Section 9 discusses limitations and future work, and Section 10 concludes.

---

## 2. Literature Review

### 2.1 Electoral Redistricting and Gerrymandering

The problem of dividing a territory into politically meaningful regions has deep connections to electoral redistricting research. In democratic systems with district-based representation, electoral boundaries must be periodically redrawn to reflect population changes, and the drawing process can be manipulated to favor particular parties - a practice known as gerrymandering [1].

Brieden et al. (2017) proposed a constrained clustering approach to electoral redistricting based on generalized Voronoi diagrams and linear programming [2]. Their method partitions geographic units into districts with hard population balance constraints while minimizing intra-district political heterogeneity. The key innovation is formulating the problem as a continuous optimization over diagram parameters, enabling efficient computation even for large instances.

Our project differs from classical redistricting in important ways: (1) we aim to *maximize* political homogeneity within cantons, whereas fair redistricting often seeks competitive or balanced districts; (2) we operate at the municipality level rather than individual census blocks; and (3) our work is purely descriptive and exploratory rather than prescriptive. However, the shared technical challenges - ensuring geographic contiguity, handling population constraints, and operating on spatial graphs - make redistricting research directly relevant.

Recent computational approaches to fair redistricting include Markov Chain Monte Carlo (MCMC) methods that sample from the space of valid partitions to detect gerrymandering outliers [3], and graph-based metrics for measuring district compactness [4]. These methods underscore the difficulty of the constrained partitioning problem and motivate the multi-algorithm comparison in our experimental framework.

### 2.2 Spatial and Constrained Clustering

Standard clustering algorithms - K-Means, hierarchical agglomerative methods, spectral clustering - operate in feature space without regard to geographic structure [5]. When geographic contiguity is required (as in regionalization), these methods must be extended with spatial constraints.

Spatially-constrained agglomerative clustering is a natural approach: starting with each spatial unit as its own cluster, iteratively merge adjacent clusters that are most similar in feature space. This maintains contiguity by construction, as merging two connected clusters yields a connected cluster [6]. Ward's criterion, which minimizes the increase in within-cluster sum of squares at each merge, is commonly used for the merge cost function.

Spectral clustering leverages the graph Laplacian to embed graph nodes into a low-dimensional space before applying K-Means [7]. When applied to a contiguity graph with edge weights derived from political similarity, spectral methods can discover clusters that respect both graph topology and feature-space structure.

Community detection algorithms from network science, particularly the Louvain method [8], offer an alternative by maximizing modularity - a measure of the fraction of edges within communities versus between communities. While Louvain does not directly control the number of clusters $K$, it provides a topology-driven baseline partition. Louvain operates on a similar principle to spectral clustering (leveraging graph structure rather than feature-space distances) and was selected over spectral methods for our experiments due to its computational efficiency and natural handling of weighted adjacency graphs.

Metaheuristic approaches such as Simulated Annealing (SA) can optimize arbitrary multi-objective cost functions over the partition space while maintaining contiguity through constrained neighborhood operations [9]. SA is well-suited to this problem because it can balance competing objectives (homogeneity, population balance, compactness) through a weighted cost function and escape local optima through stochastic acceptance of worse solutions.

### 2.3 Political Geography of Israel

Israel's political landscape is characterized by several cross-cutting cleavages [24]:

- **Left-Right ideological spectrum:** The security-oriented right (Likud, Religious Zionism) versus the peace-process-oriented left (Labor, Meretz).
- **Secular-Religious divide:** Secular and traditional voters versus ultra-Orthodox (Haredi) parties (Shas, United Torah Judaism).
- **Arab-Jewish divide:** Arab citizens voting predominantly for the Joint List or Ra'am versus Jewish-majority parties.
- **Geographic concentration:** These cleavages exhibit strong spatial autocorrelation - nearby municipalities tend to vote similarly due to shared demographics, economic conditions, and social networks [10, 25, 30].

The geographic structure of Israeli politics makes it a suitable testbed for constrained spatial clustering: we expect meaningful, contiguous cantons to emerge that reflect these known political-demographic divisions.

### 2.4 Dimensionality Reduction for Voting Data

Municipality-level election data can be represented as high-dimensional vectors of party vote shares. Dimensionality reduction techniques compress these vectors while preserving key political structure:

- **Principal Component Analysis (PCA)** finds orthogonal axes of maximum variance, typically capturing left-right and Arab-Jewish dimensions in the first few components [11].
- **Non-negative Matrix Factorization (NMF)** decomposes vote shares into additive components, producing interpretable "political archetypes" (e.g., an Arab voting pattern, a Haredi pattern) [12].
- **Manual bloc aggregation** groups parties into predefined political blocs (Right, Haredi, Center, Left, Arab), producing a low-dimensional but domain-informed representation.

We systematically compare these representations to assess which best captures politically meaningful variation for clustering purposes.

### 2.5 Research Gap

Prior work on constrained spatial clustering has focused primarily on fair electoral redistricting -- producing *competitive* districts with balanced partisan composition [1, 2, 3]. In contrast, our work seeks to maximize political *homogeneity* within regions, a fundamentally different objective. While regionalization methods such as SKATER [23] and MAX-P-REGIONS [29] address spatially constrained partitioning, they have not been applied to Israeli political geography, nor have they been evaluated across a systematic grid of feature representations, distance metrics, and algorithms. Furthermore, existing studies of Israeli political geography [10, 25] are primarily qualitative, lacking the quantitative spatial clustering framework that our project provides. This work bridges these gaps by combining constrained spatial clustering with a comprehensive experimental comparison tailored to the Israeli political context.

---

## 3. Problem Definition

### 3.1 Formal Statement

Let $V = \{v_1, \ldots, v_n\}$ be a set of $n$ municipalities, each characterized by a political feature vector $f_i \in \mathbb{R}^d$ derived from election results. Let $G = (V, E)$ be a geographic contiguity graph where edge $(v_i, v_j)$ exists if municipalities $i$ and $j$ share a geographic boundary. Let $w_i$ denote the voter population of municipality $i$.

**The Canton Partitioning Problem:** This is a variant of the regionalization problem [23, 29] -- given $V$, $G$, feature vectors $\{f_i\}$, voter weights $\{w_i\}$, and a target number of cantons $K$, find a partition $\mathcal{C} = \{C_1, \ldots, C_K\}$ of $V$ that:

1. **Maximizes political homogeneity:** Minimizes within-canton political variance.
2. **Ensures geographic contiguity:** Each canton $C_k$ induces a connected subgraph of $G$.
3. **Balances population:** Minimizes disparity in total voter population across cantons.

### 3.2 Multi-Objective Formulation

These objectives may conflict: maximizing homogeneity may produce cantons with extreme population imbalance, while enforcing strict balance may force politically dissimilar municipalities together. We adopt a weighted multi-objective approach:

$$\text{Cost}(\mathcal{C}) = \alpha \cdot \text{Homogeneity}(\mathcal{C}) + \beta \cdot \text{Balance}(\mathcal{C}) + \gamma \cdot \text{Compactness}(\mathcal{C})$$

where $\alpha, \beta, \gamma$ are tunable weights. In our Simulated Annealing implementation, we use $\alpha = 0.4$, $\beta = 0.4$, $\gamma = 0.2$. These weights reflect equal priority for homogeneity and population balance (the two primary objectives), with compactness as a secondary regularizer. Preliminary experiments with weight variations $(\alpha, \beta, \gamma) \in \{(0.5,0.3,0.2), (0.3,0.5,0.2), (0.4,0.4,0.2), (0.33,0.33,0.33)\}$ showed that equal homogeneity-balance weights $(0.4, 0.4, 0.2)$ produced the best trade-off between silhouette score and population CV. Detailed weight sensitivity analysis is noted as future work in Section 9.

### 3.3 Contiguity Constraint

The contiguity constraint is fundamental to producing geographically meaningful cantons. It requires that each canton $C_k$ forms a connected subgraph of $G$ - i.e., any two municipalities in the same canton can be reached from each other by traversing edges within that canton. This constraint is enforced structurally in agglomerative methods (only adjacent clusters merge) and algorithmically in SA (moves are rejected if they break contiguity).

---

## 4. Data Sources

### 4.1 Election Data

We use municipality-level election results from five consecutive Knesset elections, obtained from the Israel Central Bureau of Statistics (CBS) [26]:

**Table 1:** Municipality-level election data across five Knesset elections (all cover 255 municipalities).

| Election | Knesset | Date | Eligible Voters | Actual Voters | Turnout |
|----------|---------|-----------|-----------------|---------------|---------|
| 1 | 21 | Apr.\ 2019 | 6,303,973 | 4,089,609 | 64.9% |
| 2 | 22 | Sep.\ 2019 | 6,354,847 | 4,166,925 | 65.6% |
| 3 | 23 | Mar.\ 2020 | 6,416,082 | 4,268,189 | 66.5% |
| 4 | 24 | Mar.\ 2021 | 6,539,675 | 3,998,159 | 61.1% |
| 5 | 25 | Nov.\ 2022 | 6,742,445 | 4,311,984 | 64.0% |

All five elections cover the same 255 municipalities after name normalization and cross-election matching. Each record contains per-party vote counts, enabling computation of vote share vectors.

### 4.2 Geographic Data

Municipal boundary polygons were obtained from the Israel CBS geographic databases [27] in Shapefile format. Municipalities were dissolved (merged) from locality-level polygons to municipality-level using an official locality-to-municipality mapping. The CBS boundary file covers municipalities inside the Green Line. Three of them carried outdated names and were missing from earlier versions of the analysis: the file still calls Nof HaGalil by its former name (Nazareth Illit), names the Sdot Dan regional council Emek Lod, and spells Shibli-Umm al-Ghanam differently from the election data; all three are now matched.

**Judea and Samaria.** Election results include the 23 Israeli local authorities in Judea and Samaria, but the CBS file has no polygons for them. Their boundaries come from two further sources (documented in `data/raw/geo/SOURCES.md`):

- The 17 cities and local councils (including Ariel, Ma'ale Adumim, Beitar Illit and Modi'in Illit) from the CBS municipal layer based on the Ministry of Interior's boundaries as of the end of 2023.
- The 6 regional councils (Shomron, Mateh Binyamin, Gush Etzion, Har Hevron, Megilot and Arvot HaYarden) from the Civil Administration's council-area and settlement-jurisdiction layers, published under freedom of information. Each council is the union of its own area and its member settlements' jurisdictions, minus the cities and local councils. The council layer overlaps in places (79 km$^2$ between Mateh Binyamin and Arvot HaYarden); an overlap is assigned to the council with more of its settlements' area inside it, or, with none on either side, to the council for which it is the larger share of its area.

Invalid source geometries are repaired, polygons are clipped so they do not overlap existing ones, and all new polygons are simplified together by 5 m so shared borders stay shared. As a check, points inside Ramallah, Al-Bireh, Nablus, Jericho, Bethlehem and Hebron's old city fall outside every polygon: the analysis covers Israeli local authorities, whose jurisdictions in Judea and Samaria are fragmented, and Palestinian areas, which do not vote in Knesset elections, are outside it.

The combined file has 257 municipalities. Of these, 255 have votes in all five elections and form the analysis set; the other 2 are industrial local councils with no voters.

### 4.3 Party-to-Bloc Mapping

Israeli political parties were classified into five political blocs:

**Table 2:** Party-to-bloc classification.

| Bloc | Description | Example Parties |
|------|-------------|----------------|
| Right | Nationalist right | Likud, Yisrael Beiteinu, Yamina, Religious Zionism, Otzma Yehudit, Jewish Home |
| Haredi | Ultra-Orthodox religious | Shas, United Torah Judaism |
| Center | Centrist parties | Yesh Atid, Blue and White, Kahol Lavan |
| Left | Labor-left | Labor, Meretz |
| Arab | Arab-majority parties | Joint List, Ra'am, Balad |

This mapping enables the BlocShares feature representation, which aggregates raw party vote shares into five interpretable bloc dimensions. Every list that received at least 1% of the valid vote in an election is assigned to a bloc (enforced by a unit test); smaller lists are counted as "other". The mapping is keyed by ballot letter per election, since letters move between parties (for example, in 2021 Yamina ran under the letter Bet and the Religious Zionist Party under Tet).

### 4.4 Data Processing Pipeline

![Methodology Pipeline](figures/pipeline.png)
*Figure 1: End-to-end methodology pipeline from raw election data to evaluated canton partitions.*

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

**Jensen-Shannon Distance:** The square root of the Jensen-Shannon divergence [18], a symmetric, bounded measure derived from the Kullback-Leibler divergence. Particularly well-suited for probability distributions such as vote share vectors. The underlying divergence is:

$$\text{JSD}(P \| Q) = \frac{1}{2} D_{KL}(P \| M) + \frac{1}{2} D_{KL}(Q \| M), \quad \text{where } M = \frac{1}{2}(P + Q)$$

Our implementation uses $d(P, Q) = \sqrt{\text{JSD}(P \| Q)}$, which is a proper metric (satisfies the triangle inequality) [17].

### 5.3 Graph Construction and Preprocessing

**Raw Adjacency Graph:** We construct a contiguity graph $G = (V, E)$ where municipalities are nodes and edges connect municipalities that share a geographic boundary (detected via polygon intersection using GeoPandas and Shapely). The raw graph has $257$ nodes and $574$ edges but is *disconnected* - some municipalities are geographic isolates (enclaves, exclave communities, or municipalities with no shared boundaries due to polygon precision issues).

**Graph Preprocessing:** To ensure a connected graph (required for contiguous clustering), we apply three preprocessing steps:

1. **Virtual edges for isolates:** For each isolated node (degree 0), connect it to its $k=3$ nearest neighbors in feature space. $k=3$ balances ensuring connectivity with avoiding spurious long-distance edges. This ensures all municipalities participate in the clustering.

2. **Enclave edges:** For municipalities where a single bloc exceeds 70% of the municipality's own vote share (political enclaves), add edges connecting all enclaves of the same bloc type. The 70% threshold identifies municipalities where a single bloc overwhelmingly dominates. This prevents small enclaves from being forced into politically dissimilar cantons.

3. **Bridge edges for disconnected components:** For any remaining disconnected components after steps 1-2, connect each component to the largest component via an edge between the most politically similar pair of municipalities. This ensures full graph connectivity.

Municipalities inside the Green Line are adjacent when their polygons share a boundary line. Polygons from different sources do not share exact borders, so a Judea and Samaria authority is adjacent to any polygon that runs alongside it within 100 m (their 100 m buffers overlap by at least 200 m $\times$ 200 m); Ariel and Elkana, which touch nothing within that distance, are joined to their geographically nearest authority (Shomron). After subsetting the raw graph to the 255 analysis municipalities (569 edges), the augmentation pipeline produces a fully connected graph with $255$ nodes and $2{,}490$ edges.

### 5.4 Clustering Algorithms

**Simulated Annealing (SA):**
SA optimizes a multi-objective cost function over the partition space. Starting from a seed-based initialization (selecting the most politically extreme municipality per bloc as seeds, then greedily growing cantons with balance constraints), the algorithm proposes moves (reassigning a border municipality to an adjacent canton) and accepts or rejects them based on the Metropolis criterion. The cost function weights three objectives:

- Homogeneity (weight $0.4$): Size-weighted mean within-canton feature variance.
- Population balance (weight $0.4$): Coefficient of variation of canton populations.
- Compactness (weight $0.2$): Graph cut ratio -- fraction of inter-canton edges over total edges.

Parameters: initial temperature $T_0 = 1.0$, cooling rate $0.9995$, following standard SA practice [9]. The code default is $50{,}000$ iterations; the systematic grid search (Section 6) used $5{,}000$ iterations per configuration for computational efficiency, while the SA seed-sensitivity analysis (Section 9.1) used the full $50{,}000$. Contiguity is enforced by rejecting moves that disconnect any canton. Note that SA uses a deterministic seed-based *initialization* (providing a reproducible starting point) but stochastic *optimization* (random move proposals with probabilistic acceptance), so results may vary with different random seeds. Each configuration was executed once; the stability analysis in Section 7 partially addresses sensitivity by evaluating SA across five different election datasets.

**Agglomerative Clustering:**
Average-linkage with contiguity constraints [6] - starting from 255 singleton clusters, iteratively merge the two adjacent clusters with the smallest average pairwise distance. The contiguity constraint ensures only adjacent clusters merge, maintaining geographic connectedness. This deterministic algorithm produces a dendrogram that can be cut at any level to obtain K cantons.

**K-Means Baseline:**
Standard K-Means clustering [5] in feature space without geographic contiguity constraints. Serves as a baseline to measure the cost of enforcing contiguity - cantons may be geographically disconnected.

**Louvain Community Detection:**
The Louvain algorithm [8] maximizes modularity [16] on the adjacency graph. Edge weights are set based on political similarity (inverse distance). Louvain determines its own number of communities rather than accepting a target K, serving as a topology-driven baseline.

### 5.5 Evaluation Metrics

All algorithms were implemented in Python using scikit-learn [20] for K-Means and silhouette computation, NetworkX [21] for graph operations and Louvain community detection, and SciPy [22] for distance computations including Jensen-Shannon divergence.

**Within-Canton Sum of Squares (WCSS):** Measures total political variance within cantons. Computed as the sum of squared distances from each municipality's feature vector to its canton centroid (unweighted). Lower WCSS indicates more politically homogeneous cantons.

**Silhouette Score [13]:** For each municipality, measures how well it fits in its assigned canton versus the nearest alternative. Ranges from -1 to +1; higher values indicate better-defined clusters.

**Population Balance (CV):** Coefficient of variation of canton voter populations. Lower CV indicates more balanced cantons. We also report the max-to-min population ratio.

**Contiguity:** Number of cantons that are disconnected in the adjacency graph. Should be 0 for all spatially-constrained algorithms.

**Dominant Margin:** For each canton, the percentage-point lead of the dominant political bloc over the second-highest bloc. Higher margins indicate more politically distinctive cantons.

---

## 6. Experimental Results

### 6.1 Experimental Setup

We conducted a systematic grid search over 264 configurations:

**Table 3:** Experimental grid dimensions.

| Dimension | Values | Count |
|-----------|--------|-------|
| Representation | BlocShares, RawParty, PCA_5, NMF_5 | 4 |
| Distance Metric | Euclidean, Cosine, Jensen-Shannon | 3 |
| Algorithm | SA, Agglomerative, Louvain, KMeans (baseline) | 4 |
| K (cantons) | 3, 5, 7, 10, 15, 20 | 6 |
| **Total** | | **264** |

Note: Not all metric-representation combinations are applicable. Jensen-Shannon requires non-negative values and is compatible with BlocShares, RawParty, and NMF_5, but not PCA_5 (which may produce negative values); PCA_5 uses only Euclidean and Cosine metrics. All 264 configurations executed successfully with 0 failures.

**Computational Performance:** Mean runtimes per configuration were: SA 34.4s (range: 22--58s depending on K), Agglomerative 0.34s, Louvain 0.42s, KMeans 0.14s. SA's higher runtime reflects its iterative optimization (5,000 iterations in the grid search), while Agglomerative and Louvain operate in near-linear time on the 255-node graph. Total grid search runtime was approximately 40 minutes on a single CPU core (Apple M1 Pro, 16GB RAM). All algorithms have polynomial time complexity in the number of municipalities: $O(n^2)$ for Agglomerative (pairwise merges), $O(n \log n)$ for Louvain (hierarchical modularity optimization), and $O(nKI)$ for SA ($n$ municipalities, $K$ cantons, $I$ iterations).

### 6.2 Key Findings

**Representation Comparison:** BlocShares achieves the highest silhouette scores for unconstrained algorithms (Agglomerative, KMeans), thanks to its domain-informed aggregation of party votes into five interpretable blocs. However, when combined with contiguity-constrained SA, BlocShares produces severely imbalanced partitions -- at K=5, SA places 93 municipalities in one canton and only 1 in another (270x population ratio). This occurs because BlocShares' five coarse features cause the distinctive Arab voting pattern to dominate: the oversized canton holds 66 of the 69 Arab-majority municipalities. Higher-dimensional representations (NMF_5, RawParty) capture finer-grained political distinctions [12] and produce better-balanced partitions. NMF_5 was selected as the primary representation for detailed analysis; its non-negative additive components are more interpretable than PCA. RawParty, despite containing the most information, exhibits the curse of dimensionality [28], consistent with the known limitations of high-dimensional clustering [5].

**Distance Metric Comparison:** Silhouette scores are computed in each configuration's own distance metric. Cosine distance produces the highest silhouette score overall (0.987 with BlocShares/Agglomerative at K=3), ahead of Euclidean (0.910) and Jensen-Shannon (0.793) for the same configuration. Metric choice matters most for the KMeans baseline, which optimizes Euclidean distance regardless of the metric used for evaluation: its K=3 BlocShares partition scores 0.861 under Euclidean distance but -0.864 under Cosine and -0.199 under Jensen-Shannon. Jensen-Shannon offers no advantage over Euclidean or Cosine for any representation.

**Algorithm Comparison:**

- **Agglomerative** achieves the highest silhouette scores (up to 0.987) but can produce severe population imbalance, sometimes placing 250+ municipalities in a single canton.
- **Simulated Annealing** produces the most balanced cantons due to its explicit population balance objective, at the cost of slightly lower silhouette scores. SA is the preferred algorithm when population balance matters.
- **Louvain** ignores the target K parameter and finds its own natural community count. Its partitions are highly stable across elections (ARI 0.909--0.992, Section 7) but may not match the desired K.
- **KMeans (baseline)** achieves competitive silhouette scores but produces geographically disconnected cantons, confirming the necessity of contiguity constraints.

**Effect of K:** WCSS decreases monotonically with increasing K (as expected - more cantons means smaller, more homogeneous clusters). Silhouette scores [13] peak at low K values (K=3 or K=5) for most configurations, suggesting that Israel's political geography is naturally structured into a small number of macro-regions.

![Silhouette vs K](figures/silhouette_vs_k.png)
*Figure 2: Silhouette score vs K for BlocShares/Euclidean across all four algorithms.*

![Heatmap](figures/heatmap_silhouette.png)
*Figure 3: Best silhouette score achieved by each representation × algorithm combination.*

### 6.3 Best Configurations

**Table 4:** Selected configurations: best result per algorithm family.

| Rank | Repr | Metric | Algorithm | K | Silhouette | Pop CV |
|------|-----------|---------|---------------|------|------------|--------|
| 1 | BlocShares | Cosine | Agglomerative | 3 | 0.987 | 1.41 |
| 2 | BlocShares | Euclidean | KMeans | 3 | 0.861 | 0.52 |
| 3 | NMF_5 | Euclidean | Agglomerative | 3 | 0.623 | 1.13 |
| 4 | NMF_5 | Cosine | Louvain | 5 | 0.180 | 0.66 |
| 5 | NMF_5 | Cosine | SA | 5 | 0.136* | 0.29* |

*\*SA values are 30-seed means (single run: Sil=0.136, CV=0.29); see Section 9.1 for full seed sensitivity analysis.*

The best overall configuration depends on which objectives are prioritized. For pure clustering quality (silhouette), Agglomerative clustering on BlocShares dominates. KMeans achieves a high silhouette (0.861) but produces disconnected cantons. For interpretable partitions with good silhouette and politically meaningful assignments, Louvain with NMF_5/Cosine at K=5 achieves a positive silhouette (0.180), produces five distinct cantons where all major cities are assigned to politically compatible groups, and keeps its boundaries stable across elections (mean ARI = 0.909). SA with NMF_5 achieves better population balance (CV 0.29 vs 0.66) but lower silhouette (0.136).

**Note on Selection Bias:** With 264 configurations evaluated, the reported 'best' silhouette scores may be inflated by selection effects. Without multiple comparison correction (e.g., Bonferroni), the top-ranked configuration's superiority should be interpreted cautiously. The relative rankings and qualitative patterns are more robust than absolute performance differences.

### 6.4 Primary Result: K=5 Louvain Partition

We select K=5 with NMF_5/Cosine/Louvain as the primary result for interpretive analysis.

**Selection Criteria:** We formalize the primary result selection using four criteria weighted by importance for exploratory political analysis:

| Criterion | Weight | K=3 Agglom (BlocShares/Cosine) | K=5 Louvain (NMF_5/Cosine) | Winner |
|-----------|--------|------------|-------------|--------|
| Silhouette (higher = better) | 0.25 | 0.987 | 0.180 | K=3 |
| Population Balance CV (lower = better) | 0.25 | 1.41 | 0.66 | K=5 |
| Temporal Stability ARI (higher = better) | 0.25 | 0.954* | 0.909 | K=3 |
| Political Granularity (5 > 3 cantons) | 0.25 | 3 cantons | 5 cantons | K=5 |

*\*Stability is measured at K=5 for every configuration; this is BlocShares/Cosine/Agglomerative at K=5, the nearest tested configuration.*

The criteria split 2--2: K=3 Agglomerative has the higher silhouette and stability, K=5 Louvain the better population balance and political resolution. We select K=5 because the K=3 configuration's superior silhouette reflects its coarser granularity (fewer, larger clusters naturally have higher cohesion), while its severe population imbalance (CV=1.41) and limited political resolution (only 3 regions) make it unsuitable for detailed political analysis. The K=5 partition's positive silhouette (0.180) indicates weak but above-chance cluster structure (below the 0.25 threshold for substantial structure per Rousseeuw [13]), while providing the granularity needed to distinguish the metropolitan core, two right-leaning regions, the Arab canton and the Haredi cities. K=6 was also examined: it splits off a two-town canton (Abu Snan and Kafr Yasif) and is worse on every criterion (silhouette 0.070, CV 0.85, ARI 0.801). NMF_5 provides a good balance of dimensionality reduction and interpretability: its five non-negative additive components capture finer-grained political distinctions than BlocShares' five coarse features, producing well-balanced partitions across all algorithms. Louvain's modularity-based optimization yields a positive silhouette (0.180), politically coherent assignments (all major cities land in ideologically compatible cantons), and stable boundaries across elections (mean ARI = 0.909, Section 7).

**Table 5:** K=5 canton profiles (NMF_5 / Cosine / Louvain). Bloc values are vote shares (%) averaged over the five elections and weighted by each municipality's number of voters.

| Canton | Munis | Right% | Haredi% | Center% | Left% | Arab% |
|-------------------------|-------|--------|---------|---------|-------|-------|
| 0 -- METRO Tel Aviv | 53 | 41.1 | 7.1 | 39.0 | 10.6 | 1.3 |
| 1 -- RIGHT Jerusalem & South | 60 | 53.1 | 22.1 | 17.8 | 5.4 | 0.7 |
| 2 -- RIGHT North | 75 | 44.8 | 7.3 | 30.7 | 9.4 | 6.6 |
| 3 -- ARAB | 60 | 1.9 | 0.9 | 2.4 | 4.0 | 89.6 |
| 4 -- HAREDI Cities | 7 | 8.6 | 90.0 | 0.9 | 0.3 | 0.0 |

**Evaluation metrics for this partition:**

- Cantons: 5
- Population CV: 0.66
- Silhouette: 0.180
- Cross-election stability: mean ARI = 0.909 (std 0.077)

The silhouette of 0.180, while positive, indicates weak cluster separation with substantial overlap between cantons—typical for political geography where boundaries are gradual rather than sharp. Canton 0 (METRO Tel Aviv) covers Greater Tel Aviv and the Sharon, from Netanya to Rehovot, with Right and Center almost level (41.1% and 39.0%). Canton 1 (RIGHT Jerusalem & South) runs from Jerusalem through the southern periphery and the Negev and includes the Judea and Samaria authorities (53.1% Right, 22.1% Haredi). Canton 2 (RIGHT North) is a mixed northern region including Haifa and the Galilee Jewish towns (44.8% Right). Canton 3 (ARAB) brings together the Arab municipalities of the Galilee, the Triangle and the Negev (89.6% Arab vote share). Canton 4 (HAREDI Cities) consists of the seven municipalities where Haredi parties receive more than 70% of the vote: Bnei Brak, El'ad, Rekhasim, Kiryat Ye'arim, Modi'in Illit, Beitar Illit and Immanuel (90.0% Haredi). None of the seven borders another; they are joined by the graph's enclave edges (Section 5.3), so this canton is a political rather than a geographic unit. It appears once Beitar Illit, Modi'in Illit and Immanuel are included, and the two Arab cantons of earlier versions merge to keep K=5. The municipality count imbalance (7--75) is wider than SA's (29--73), reflecting Louvain's optimization of modularity rather than balance. Each canton has a clearly interpretable political character (see Section 8).

![Canton Map K=5](figures/canton_map_k5.png)
*Figure 4: Geographic visualization of the K=5 Louvain canton partition (NMF_5 / Cosine).*

![Political Composition](figures/political_composition_k5.png)
*Figure 5: Political bloc composition of each canton in the K=5 Louvain partition.*

---

## 7. Stability Analysis

### 7.1 Methodology

To assess whether canton boundaries are structurally stable or sensitive to election-specific noise, we perform temporal stability analysis. For a fixed configuration, we run clustering independently on each of the five elections and measure pairwise agreement between the resulting partitions using:

- **Adjusted Rand Index (ARI) [14]:** Measures partition similarity corrected for chance. $\text{ARI} = 1.0$ indicates identical partitions; $\text{ARI} = 0$ indicates random agreement.
- **Normalized Mutual Information (NMI) [15]:** Information-theoretic measure of partition similarity. $\text{NMI} = 1.0$ indicates identical partitions.

We tested seven representative configurations spanning different representation-metric-algorithm combinations, including the primary NMF_5/Cosine/Louvain partition. SA configurations used $2{,}000$ iterations per run for computational efficiency (5 elections × 4 SA configurations = 20 SA executions).

### 7.2 Results

**Table 6:** Cross-election stability for seven representative configurations.

| Repr | Metric | Algorithm | Mean ARI | Std ARI | Mean NMI | Std NMI |
|-----------|---------|---------------|----------|---------|----------|---------|
| BlocShares | Euclidean | Louvain | 0.992 | 0.007 | 0.988 | 0.010 |
| BlocShares | Cosine | Agglomerative | 0.954 | 0.059 | 0.945 | 0.071 |
| NMF_5 | Cosine | Louvain (primary) | 0.909 | 0.077 | 0.920 | 0.065 |
| BlocShares | Euclidean | SA | 0.587 | 0.103 | 0.636 | 0.083 |
| RawParty | Cosine | SA | 0.458 | 0.165 | 0.518 | 0.140 |
| NMF_5 | Euclidean | SA | 0.449 | 0.241 | 0.547 | 0.191 |
| PCA_5 | Euclidean | SA | 0.383 | 0.119 | 0.497 | 0.098 |

### 7.3 Interpretation

**Deterministic algorithms produce highly stable partitions.** The BlocShares Louvain configuration produces near-identical partitions across elections (ARI = 0.992) because it optimizes graph modularity on the fixed adjacency structure rather than feature values; this largely reflects algorithmic determinism rather than political stability. The graph topology dominates Louvain's community detection, so variations in election-specific feature values have little effect. The primary NMF_5/Cosine Louvain partition is somewhat less stable (ARI = 0.909) but still more stable than any SA configuration. Agglomerative clustering also produces near-perfect stability (ARI = 0.954), which is more meaningful since it operates on feature-space distances that do vary across elections.

**SA stability varies by representation.** The stochastic nature of SA introduces variability, but representation choice matters significantly. BlocShares produces the most stable SA partitions (ARI = 0.587), followed by RawParty (0.458) and NMF (0.449). PCA produces the least stable partitions (0.383), likely because the principal components rotate across elections as party compositions change.

**Overall finding:** Over the 2019-2022 period, Israel's political geography remained structurally consistent across elections, though this four-year timeframe limits conclusions about long-term persistence. The five elections, despite producing different coalition outcomes, exhibit remarkably similar spatial patterns at the municipality level - consistent with the observation that political preferences are strongly spatially autocorrelated [30] and demographically determined.

![Stability ARI](figures/stability_ari.png)
*Figure 6: Mean Adjusted Rand Index across election pairs for each configuration, with error bars showing standard deviation.*

### 7.4 Cantons in Each Election

To show the stability of the primary partition directly, the primary configuration was run on each election alone and each election's cantons were matched one-to-one to the primary map's (maximum overlap). A canton sharing less than half of its members with its match (Jaccard index below 0.5) keeps its own number instead of borrowing a label.

![Per-election maps](figures/per_election_maps.png)
*Figure 7: K=5 cantons computed from each election separately, coloured by their matching primary canton.*

220 of the 255 municipalities are in the same canton in every election; 28 change in one election and 7 in two. The four elections from 2019 to 2021 give nearly the same map. November 2022 differs most: the seven Haredi cities join the metropolitan canton, and 18 Arab municipalities, most of them Bedouin towns in the Negev and towns in the southern Triangle (including Rahat, Hura, Tel Sheva, Kafr Qasem and Jaljulia), form a canton of their own with no counterpart in the primary map. These towns gave Ra'am 68% of their vote in 2022, against 26% in the Arab canton's other towns (65% and 34% in 2021), so the gap between the two widened.

### 7.5 Do the Cantons Differ? A Held-Out Test

Testing whether cantons differ in the vote shares they were built from would be circular: a clustering algorithm separates groups on exactly those features. We therefore rebuild the cantons from the 2019--2021 elections only (features, graph preprocessing and weights all use Knesset 21--24) and test differences on the November 2022 results, which did not shape the map. The training map agrees closely with the primary map (ARI = 0.967), and a unit test checks that scrambling the 2022 results leaves it unchanged.

For each bloc, a Kruskal--Wallis test compares the five cantons, and each pair of cantons is compared twice: by the voter-weighted difference in bloc share with a 95% bootstrap interval (10,000 resamples of municipalities within each canton), and by a Mann--Whitney test of whether the typical municipality differs, Holm-adjusted across the ten pairs. Each municipality counts once in the Mann--Whitney test, so the two can disagree when a few large towns drive a canton's share.

**Table 6b:** Kruskal--Wallis tests across the five cantons, November 2022 bloc shares.

| Bloc | H | p | $\epsilon^2$ | Pairs differing (Holm $p<0.05$) |
|------|---|---|---------------|-------------------------------|
| Arab | 157.6 | $<10^{-30}$ | 0.62 | 9 of 10 |
| Center | 156.6 | $<10^{-30}$ | 0.62 | 9 of 10 |
| Right | 151.4 | $<10^{-30}$ | 0.60 | 9 of 10 |
| Haredi | 111.4 | $<10^{-20}$ | 0.44 | 8 of 10 |
| Left | 86.1 | $<10^{-15}$ | 0.34 | 9 of 10 |

All five blocs differ strongly across cantons in the held-out election (large effect sizes, $\epsilon^2$ from 0.34 to 0.62), and 44 of the 50 canton pairs differ significantly. The pairs that do not are informative: the metropolitan canton and RIGHT North do not differ in their typical town's Right, Left or Haredi share, so the line between them is drawn by the Center vote (8.6 points higher in the metropolitan canton) and the Arab vote (6.4 points higher in RIGHT North); and the Haredi share of the metropolitan canton and of RIGHT Jerusalem & South differs in voters' terms (16.3 points, 95% interval 5.2 to 24.4, driven by Jerusalem) but not in the typical town ($p = 0.30$). Neighbouring municipalities vote alike, so these tests, which treat municipalities as independent, are somewhat optimistic. The full table is in the app's *Compare Cantons* page and in `data/processed/canton_tests.csv`.

**What the test does and does not show.** Municipal bloc shares are very stable between elections: their 2022 values correlate 0.91 (Left) to 0.99 (Arab, Haredi) with the 2019--2021 averages. The held-out test therefore shows that the differences between cantons persist into an election that played no part in drawing them; it does not show that these particular boundaries separate the electorate better than other groupings of the same towns would. Two further caveats: the primary configuration was chosen from a grid computed on all five elections, so the 2022 results did inform which method is used; and the bootstrap interval for the seven-town Haredi canton, whose voters are dominated by Bnei Brak, is likely too narrow. Comparing the cantons against random contiguous partitions of the same graph is left for future work.

---

## 8. Case Studies

### 8.1 The K=5 Partition in Detail

Our primary K=5 NMF_5/Cosine/Louvain partition divides Israel into five politically coherent regions. We examine seven case study areas to assess whether the algorithmic cantons align with known political geography. Dominant blocs and shares below are averages over the five elections.

### 8.2 Greater Tel Aviv (Gush Dan)

**Table 7:** Greater Tel Aviv canton assignments.

| Municipality | Canton | Dominant Bloc |
|-------------|--------|---------------|
| Tel Aviv-Yafo | 0 | Center |
| Ramat Gan | 0 | Center |
| Givatayim | 0 | Center |
| Herzliya | 0 | Center |
| Ra'anana | 0 | Center |
| Kfar Saba | 0 | Center |
| Holon | 0 | Right |
| Bat Yam | 0 | Right |
| Petah Tikva | 0 | Right |
| Rishon LeZion | 0 | Right |
| Netanya | 0 | Right |
| Bnei Brak | 4 | Haredi |

**Analysis:** The whole metropolitan area -- the center-leaning core (Tel Aviv, Ramat Gan, Givatayim, Herzliya, Ra'anana, Kfar Saba) and the right-leaning cities around it (Holon, Bat Yam, Petah Tikva, Rishon LeZion, Netanya) -- forms Canton 0 (METRO Tel Aviv), where Right and Center are almost level (41.1% and 39.0%). Bnei Brak, in the middle of the metropolis, belongs to Canton 4 (HAREDI Cities) with the other predominantly Haredi cities.

### 8.3 Jerusalem Region

**Table 8:** Jerusalem region canton assignments.

| Municipality | Canton | Dominant Bloc |
|-------------|--------|---------------|
| Jerusalem | 1 | Haredi |
| Beit Shemesh | 1 | Haredi |
| Mevasseret Zion | 1 | Right |
| Ma'ale Adumim | 1 | Right |
| Givat Ze'ev | 1 | Right |
| Modi'in-Maccabim-Re'ut | 0 | Center |
| Beitar Illit | 4 | Haredi |
| Modi'in Illit | 4 | Haredi |

**Analysis:** Jerusalem is placed in **Canton 1** (RIGHT Jerusalem & South) with Beit Shemesh, Mevasseret Zion, Ma'ale Adumim, Givat Ze'ev, the regional councils of Judea and Samaria, the southern periphery towns and the major southern cities (Ashdod, Ashkelon, Beer Sheva). This canton captures Israel's right-wing and Haredi heartland (53.1% Right, 22.1% Haredi). Modi'in joins the metropolitan canton, and the two large Haredi cities beyond the Green Line, Beitar Illit and Modi'in Illit, join Canton 4.

### 8.4 Judea and Samaria

**Table 9:** Judea and Samaria authorities (Right = average Right-bloc vote share).

| Authority | Canton | Dominant Bloc | Right % |
|-----------|--------|---------------|---------|
| Elkana | 1 | Right | 91.8 |
| Kiryat Arba | 1 | Right | 91.1 |
| Har Hevron | 1 | Right | 88.0 |
| Efrat | 1 | Right | 87.9 |
| Karnei Shomron | 1 | Right | 87.4 |
| Shomron | 1 | Right | 83.5 |
| Ariel | 1 | Right | 77.9 |
| Arvot HaYarden | 1 | Right | 68.6 |
| Megilot | 1 | Right | 44.8 |
| Oranit | 0 | Right | 46.0 |
| Immanuel | 4 | Haredi | 22.6 |

**Analysis:** Most of the 23 Judea and Samaria authorities join Canton 1, with some of the highest Right-bloc shares in the country (above 85% in Elkana, Kiryat Arba, Har Hevron, Efrat and Karnei Shomron). Oranit and Alfei Menashe, on the Green Line next to the Sharon, join the metropolitan canton, and the Haredi cities Beitar Illit, Modi'in Illit and Immanuel join Canton 4. Because the regional councils' jurisdictions are fragmented and Ariel and Elkana are linked to their nearest authority (Section 5.3), contiguity here is looser than inside the Green Line.

### 8.5 Arab Towns

**Table 10:** Arab-majority municipality canton assignments.

| Municipality | Canton | Dominant Bloc |
|-------------|--------|---------------|
| Nazareth | 3 | Arab |
| Umm al-Fahm | 3 | Arab |
| Shfar'am | 3 | Arab |
| Tayibe | 3 | Arab |
| Sakhnin | 3 | Arab |
| Tamra | 3 | Arab |
| Baqa al-Gharbiyye | 3 | Arab |
| Rahat | 3 | Arab |
| Kafr Qasem | 3 | Arab |

**Analysis:** All Arab-majority municipalities, in the Galilee, the Triangle and the Negev, form **Canton 3** (ARAB, 89.6% Arab vote share). Earlier versions of the analysis split them into a Galilee canton and a southern one; with the Haredi cities forming their own canton, K=5 leaves room for one Arab canton. The split reappears in the November 2022 election taken alone (Section 7.4), where the Bedouin towns of the Negev and towns in the southern Triangle, where Ra'am is strongest [25], form a separate canton.

### 8.6 The Haredi Cities

**Table 11:** Canton 4 (HAREDI Cities).

| Municipality | Haredi % | Area |
|-------------|----------|----------|
| Bnei Brak | 89.2 | Greater Tel Aviv |
| El'ad | 84.8 | Central Israel |
| Rekhasim | 88.1 | Haifa district |
| Kiryat Ye'arim | 87.8 | Jerusalem hills |
| Modi'in Illit | 97.6 | Judea and Samaria |
| Beitar Illit | 90.7 | Judea and Samaria |
| Immanuel | 76.8 | Judea and Samaria |

**Analysis:** Canton 4 is the set of municipalities where Haredi parties receive more than 70% of the vote (90.0% Haredi overall). None of the seven borders another: the canton is held together by the graph's enclave edges, which connect municipalities dominated by the same bloc (Section 5.3). It is therefore a political archipelago rather than a geographic region, and it should be read as "the Haredi cities vote as a bloc of their own" rather than as a contiguous territory.

### 8.7 Haifa and the Krayot

**Table 12:** Haifa metropolitan area canton assignments.

| Municipality | Canton | Dominant Bloc |
|-------------|--------|---------------|
| Haifa | 2 | Right |
| Kiryat Ata | 2 | Right |
| Kiryat Motzkin | 2 | Right |
| Kiryat Yam | 2 | Right |
| Kiryat Bialik | 2 | Right |
| Nesher | 2 | Right |
| Akko | 2 | Right |

**Analysis:** Haifa and all the Krayot are assigned to **Canton 2** (RIGHT North, 44.8% Right), a large northern canton that encompasses the Jewish towns of the Galilee, Golan Heights, and upper Galilee alongside the Haifa metropolitan area. Louvain's modularity-based approach groups these right-leaning Jewish cities together based on their political similarity, keeping Haifa in a politically compatible canton despite its geographic proximity to Arab municipalities in the Galilee.

### 8.8 Southern Periphery

**Table 13:** Southern periphery canton assignments.

| Municipality | Canton | Dominant Bloc |
|-------------|--------|---------------|
| Beer Sheva | 1 | Right |
| Dimona | 1 | Right |
| Netivot | 1 | Right |
| Ofakim | 1 | Right |
| Arad | 1 | Right |
| Eilat | 1 | Right |
| Yeruham | 1 | Right |
| Mitzpe Ramon | 1 | Right |

**Analysis:** All southern periphery towns, including Beer Sheva, are grouped in **Canton 1** (RIGHT Jerusalem & South), forming a contiguous arc from Jerusalem through the Negev to Eilat. This aligns with the well-documented "periphery vote" phenomenon [10, 25]. Beer Sheva (65.0% Right) is grouped with the right-wing southern arc, consistent with its voting patterns, despite its geographic proximity to Bedouin municipalities.

### 8.9 Comparison to Administrative Districts

We compared our K=5 political cantons to Israel's official administrative districts, assigning each municipality the most common district among its localities in the CBS locality file. The Adjusted Rand Index [14] between the canton partition and the administrative district partition is 0.360 over all 255 municipalities (low to moderate; earlier versions reported 0.286 over the 149 cities and local councils that a name-based lookup could match, which left out every regional council). Political cantons only partially coincide with administrative districts and diverge in key ways:

- Administrative districts follow geographic boundaries (north, center, south), while political cantons follow ideological lines (Arab vs. Jewish, religious vs. secular, periphery vs. core).
- The Arab canton spans the Northern, Haifa, Central and Southern districts.
- The Judea and Samaria district is split three ways: most authorities join the Jerusalem and southern canton, Oranit and Alfei Menashe the metropolitan canton, and Beitar Illit, Modi'in Illit and Immanuel the Haredi canton.
- Jerusalem is administratively its own district but politically groups with the southern periphery and Judea and Samaria.

This confirms that **political cantons more closely reflect ideological geography than administrative geography, though partial overlap exists**.

---

## 9. Limitations and Future Work

### 9.1 Limitations

**Population Imbalance:** The K=5 NMF_5/Louvain partition has a municipality count range of 7--75 (Pop CV = 0.66). The Haredi canton (7 municipalities, 157,000 voters) is far smaller than the others (53--75 municipalities). Louvain optimizes modularity rather than balance; the SA alternative achieves better balance (CV = 0.29) but with lower silhouette (0.136), as its contiguity constraints can override political similarity.

**SA Single-Run Results:** Simulated Annealing is a stochastic algorithm, and the results reported for each SA configuration are from a single run with a fixed random seed (42), which makes each run exactly reproducible. While the fixed seed provides a consistent starting point, different random seeds or initialization strategies could yield different partitions. Ideally, each SA configuration would be run multiple times to report mean and variance of evaluation metrics. Our stability analysis (Section 7) partially addresses this by evaluating SA on five different election datasets, revealing the sensitivity of SA results to input data variation.

**SA Seed Sensitivity:** To quantify SA's stochastic variance, we ran the primary SA configuration (NMF_5/Cosine/K=5) with 30 different random seeds (following the recommendation of at least 30 runs for reliable variance estimation [9]). Results showed silhouette scores ranging from 0.120 to 0.140 (mean: 0.136, std: 0.003, 95% CI: [0.135, 0.137]) and Pop CV ranging from 0.23 to 0.29 (mean: 0.29, std: 0.01, 95% CI: [0.287, 0.295]). This variance is much smaller than the gap between SA and Louvain (silhouette difference of ~0.04), confirming that algorithmic choice dominates over seed variance.

**Ecological Fallacy:** Our analysis operates at the municipality level, aggregating individual votes. This means we cannot infer individual-level political preferences from municipality-level patterns - a well-known limitation in spatial analysis called the ecological fallacy [19]. For example, a right-leaning municipality may contain left-leaning neighborhoods, but our municipality-level data cannot capture such within-municipality variation. Our partition describes municipal-level political geography, not individual voter preferences.

**Static Analysis:** We analyze election results as fixed snapshots without modeling voter migration, demographic shifts, or political realignment over time. Our stability analysis shows structural persistence across five elections, but longer-term changes (such as growth of specific religious or ethnic communities) are not captured.

**Data Coverage:** We include the 255 municipalities that have votes in all five elections, including the 23 Israeli local authorities in Judea and Samaria. Small localities, kibbutzim, and moshavim that are part of regional councils (administrative units encompassing multiple small localities) are aggregated at the regional council level, potentially masking within-council political heterogeneity. The Judea and Samaria boundaries combine two sources (CBS and the Civil Administration), neither of which states terms of use; the regional councils' jurisdictions are fragmented, and Palestinian areas, which do not vote in Knesset elections, are outside the analysis.

**Contiguity Approximation:** The augmented graph includes virtual edges for isolate municipalities and enclaves, which means some "contiguous" cantons are not strictly geographically connected but rather connected through feature-space proximity. For example, Kiryat Shmona, in the far north, is assigned to Canton 1 (RIGHT Jerusalem & South) through enclave edges that link it to right-wing enclaves such as Sderot and Dimona, and the Haredi canton consists of seven municipalities none of which borders another (Section 8.6). Ariel and Elkana, which touch no other polygon within 100 m, are linked to their nearest authority. These are pragmatic compromises to handle Israel's complex municipal geography; removing the enclave edges would change the method and is left for future work.

**KMeans Baseline Contiguity:** The KMeans baseline operates purely in feature space without geographic constraints, meaning its cantons may be geographically disconnected. It is included as a reference point to quantify the trade-off between clustering quality and contiguity enforcement.

### 9.2 Future Work

**Enhanced Web Application:** The current Streamlit-based explorer allows interactive exploration of all 264 configurations. Future work could extend this with React + Leaflet for enhanced interactivity, side-by-side canton comparisons, and animated transitions between configurations.

**Finer Geographic Resolution:** Extend the analysis to statistical area or neighborhood level within large cities, capturing within-city political variation (e.g., north vs. south Tel Aviv).

**Coalition Simulation:** Use canton-level political profiles to simulate coalition formation under hypothetical regional representation systems.

**Cross-Country Comparison:** Apply the same constrained spatial clustering methodology to other countries with spatial political polarization (e.g., the United States red/blue state divide, Belgian linguistic-political divisions).

**Temporal Dynamics:** Model how canton boundaries shift over time as demographics change, incorporating census data and immigration statistics.

**Parameter Sensitivity Analysis:** A systematic sensitivity analysis of SA cost function weights, graph preprocessing thresholds (enclave threshold, nearest-neighbor $k$), and SA temperature schedule parameters would further strengthen the methodology and quantify robustness of results to parameter choices.

---

## 10. Conclusion

This project successfully demonstrates that constrained spatial clustering can partition Israeli municipalities into politically coherent, geographically contiguous cantons that align with known political-demographic divisions. Our systematic experimental framework - evaluating 264 configurations across four representations, three distance metrics, four algorithms, and six values of K - provides comprehensive evidence that:

1. **Israel's political geography is structurally robust.** BlocShares achieves the highest silhouette scores for unconstrained algorithms, while NMF_5 with Louvain produces the most interpretable partition with positive silhouette (0.180) and stable boundaries across elections (ARI = 0.909) -- demonstrating that representation and algorithm choice critically interact. SA achieves better population balance (CV = 0.29) but lower silhouette (0.136); Louvain's modularity-based approach yields politically coherent assignments with positive silhouette.

2. **The Arab-Jewish divide is the dominant political-geographic cleavage, with the Haredi cities a second bloc of their own.** In virtually all configurations, Arab-majority municipalities form a distinct, cohesive cluster, reflecting the unique Arab voting pattern that is quantitatively dissimilar from all Jewish-majority voting patterns. With the Judea and Samaria authorities included, the seven predominantly Haredi cities also form their own canton, although they share no borders.

3. **Political cantons differ from administrative districts.** With ARI = 0.360 [14] between our K=5 cantons and Israel's administrative districts, we confirm that political geography follows ideological lines (religious vs. secular, periphery vs. core, Arab vs. Jewish) rather than administrative boundaries.

4. **The differences between cantons persist into a new election.** Built from the 2019--2021 elections only, the cantons still differ significantly in all five blocs' vote shares in the held-out 2022 election (44 of 50 canton pairs, effect sizes $\epsilon^2$ 0.34--0.62). Because municipal voting is so stable, this shows persistence rather than validating these exact boundaries (Section 7.5).

5. **Multi-objective optimization is essential.** The trade-off between political homogeneity, population balance, and geographic compactness requires careful algorithm selection. Louvain produces the most interpretable partitions with the best silhouette among graph-based methods, while SA achieves the best population balance through its explicit multi-objective cost function -- each algorithm has distinct strengths depending on priorities.

6. **Distance metric choice matters.** Cosine distance with BlocShares/Agglomerative at K=3 achieves the highest silhouette score (0.987), ahead of Euclidean (0.910) and Jensen-Shannon (0.793) for the same configuration, while KMeans partitions that score well under Euclidean distance score poorly under Cosine and Jensen-Shannon. The choice of metric interacts with both the representation and the algorithm's objective.

This project bridges computer science, data science, geographic information systems, and political analysis, providing both a methodological contribution to constrained spatial clustering and an analytical tool for exploring Israel's political geography. The open-source codebase, modular architecture, and comprehensive experiment logs enable full reproducibility and extension.

---

## References

[1] Stephanopoulos, N. O., & McGhee, E. M. (2015). Partisan Gerrymandering and the Efficiency Gap. *University of Chicago Law Review*, 82(2), 831-900.

[2] Brieden, A., Gritzmann, P., & Klemm, F. (2017). Constrained clustering via diagrams: A unified theory and its application to electoral district design. *arXiv preprint* [arXiv:1703.02867](https://arxiv.org/abs/1703.02867).

[3] DeFord, D., Duchin, M., & Solomon, J. (2021). Recombination: A family of Markov chains for redistricting. *Harvard Data Science Review*, 3(1).

[4] Duchin, M., & Tenner, B. E. (2018). Discrete geometry for electoral geography. *arXiv preprint* [arXiv:1808.05860](https://arxiv.org/abs/1808.05860).

[5] Hastie, T., Tibshirani, R., & Friedman, J. (2009). *The Elements of Statistical Learning: Data Mining, Inference, and Prediction*. Springer.

[6] Murtagh, F., & Legendre, P. (2014). Ward's hierarchical agglomerative clustering method: Which algorithms implement Ward's criterion? *Journal of Classification*, 31(3), 274-295.

[7] Von Luxburg, U. (2007). A tutorial on spectral clustering. *Statistics and Computing*, 17(4), 395-416.

[8] Blondel, V. D., Guillaume, J. L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. *Journal of Statistical Mechanics: Theory and Experiment*, 2008(10), P10008.

[9] Kirkpatrick, S., Gelatt, C. D., & Vecchi, M. P. (1983). Optimization by simulated annealing. *Science*, 220(4598), 671-680.

[10] Arian, A., & Shamir, M. (2008). A decade later, the world had changed, the cleavage structure remained: Israel 1996-2006. *Party Politics*, 14(6), 685-705.

[11] Jolliffe, I. T. (2002). *Principal Component Analysis*. Springer.

[12] Lee, D. D., & Seung, H. S. (1999). Learning the parts of objects by non-negative matrix factorization. *Nature*, 401(6755), 788-791.

[13] Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics*, 20, 53-65.

[14] Hubert, L., & Arabie, P. (1985). Comparing partitions. *Journal of Classification*, 2(1), 193-218.

[15] Strehl, A., & Ghosh, J. (2002). Cluster ensembles -- a knowledge reuse framework for combining multiple partitions. *Journal of Machine Learning Research*, 3, 583-617.

[16] Newman, M. E. J., & Girvan, M. (2004). Finding and evaluating community structure in networks. *Physical Review E*, 69(2), 026113.

[17] Endres, D. M., & Schindelin, J. E. (2003). A new metric for probability distributions. *IEEE Transactions on Information Theory*, 49(7), 1858-1860.

[18] Lin, J. (1991). Divergence measures based on the Shannon entropy. *IEEE Transactions on Information Theory*, 37(1), 145-151.

[19] Robinson, W. S. (1950). Ecological correlations and the behavior of individuals. *American Sociological Review*, 15(3), 351-357.

[20] Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., ... & Duchesnay, E. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research*, 12, 2825-2830.

[21] Hagberg, A. A., Schult, D. A., & Swart, P. J. (2008). Exploring network structure, dynamics, and function using NetworkX. In *Proceedings of the 7th Python in Science Conference (SciPy)*, 11-15.

[22] Virtanen, P., Gommers, R., Oliphant, T. E., Haberland, M., Reddy, T., Cournapeau, D., ... & van der Walt, S. J. (2020). SciPy 1.0: Fundamental algorithms for scientific computing in Python. *Nature Methods*, 17, 261-272.

[23] Assuncao, R. M., Neves, M. C., Camara, G., & da Costa Freitas, C. (2006). Efficient regionalization techniques for socio-economic geographical units using minimum spanning trees. *International Journal of Geographical Information Science*, 20(7), 797-811.

[24] Diskin, A., & Diskin, H. (2005). The politics of electoral reform in Israel. *International Political Science Review*, 26(1), 33-54.

[25] Shamir, M., & Arian, A. (1999). Collective identity and electoral competition in Israel. *American Political Science Review*, 93(2), 265-277.

[26] Israel Central Bureau of Statistics. (2023). *Election Results Data*. Retrieved from https://www.cbs.gov.il/

[27] Israel Central Bureau of Statistics. (2023). *Municipal Boundaries GIS Data*. Retrieved from https://www.cbs.gov.il/

[28] Bellman, R. E. (1961). *Adaptive Control Processes: A Guided Tour*. Princeton University Press.

[29] Duque, J. C., Anselin, L., & Rey, S. J. (2012). The MAX-P-REGIONS problem. *Journal of Regional Science*, 52(3), 397-419.

[30] Anselin, L. (1995). Local indicators of spatial association -- LISA. *Geographical Analysis*, 27(2), 93-115.

[31] Strenger, C., & Yadid, J. (2014, October 8). Lama rak shtei medinot? Gam Israel yekhola lehitchalek le'otonomiot [Why only two states? Israel, too, can be divided into autonomies]. *Haaretz*, The Edge. English edition: Yadid, J., & Strenger, C. (2014, October 7). How cantonization can save Israel. *Haaretz*.

---

## Appendix

### A. Canton Member Lists (K=5 NMF_5/Cosine/Louvain Partition)

**Canton 0 - METRO Tel Aviv (53 municipalities):**
Alfei Menashe, Azor, Bat Yam, Be'er Ya'akov, Beit Dagan, Brenner, Daliyat al-Karmel, Drom HaSharon, Emek Hefer, Even Yehuda, Gan Raveh, Ganei Tikva, Gezer, Givat Shmuel, Givatayim, Herzliya, Hevel Modi'in, Hod HaSharon, Hof HaSharon, Holon, Isfiya, Kadima-Zoran, Kfar Saba, Kfar Shemaryahu, Kfar Yona, Kiryat Ekron, Kiryat Ono, Kokhav Ya'ir, Lev HaSharon, Lod, Mazkeret Batya, Modi'in-Maccabim-Re'ut, Nahal Sorek, Nes Tziona, Netanya, Or Yehuda, Oranit, Pardesiya, Petah Tikva, Ra'anana, Ramat Gan, Ramat HaSharon, Ramla, Rehovot, Rishon LeZion, Rosh HaAyin, Savyon, Sdot Dan, Shoham, Tel Aviv-Yafo, Tel Mond, Yavne, Yehud-Monosson

**Canton 1 - RIGHT Jerusalem & South (60 municipalities):**
Arad, Ariel, Arvot HaYarden, Ashdod, Ashkelon, Be'er Tuvia, Beer Sheva, Beit Aryeh-Ofarim, Beit El, Beit Jann, Beit Shemesh, Bnei Ayish, Bnei Shimon, Dimona, Efrat, Eilat, Elkana, Eshkol, Gan Yavne, Gedarot, Gedera, Givat Ze'ev, Gush Etzion, HaArava HaTikhona, Har Adar, Har Hevron, Harish, Hevel Eilot, Hevel Yavne, Hof Ashkelon, Jerusalem, Karnei Shomron, Kedumim, Kiryat Arba, Kiryat Gat, Kiryat Malakhi, Kiryat Shmona, Lakhish, Lehavim, Ma'ale Adumim, Ma'ale Efraim, Mateh Binyamin, Mateh Yehuda, Megilot, Meitar, Merhavim, Mevasseret Zion, Mitzpe Ramon, Netivot, Ofakim, Omer, Ramat Negev, Sderot, Sdot Negev, Sha'ar HaNegev, Shafir, Shomron, Tamar, Yeruham, Yoav

**Canton 2 - RIGHT North (75 municipalities):**
Abu Snan, Afula, Akko, Alona, Beit She'an, Binyamina-Giv'at Ada, Buq'ata, Ein Kinya, Elyakhin, Emek HaMa'ayanot, Emek HaYarden, Emek Yizre'el, Fassuta, Ghajar, Golan, Gush Halav (Jish), HaGalil HaElyon, HaGalil HaTahton, HaGilboa, Hadera, Haifa, Hatzor HaGlilit, Hof HaCarmel, Hurfeish, Ilabun, Julis, Ka'abiyye-Tabbash-Hajajre, Kafr Kama, Karmi'el, Katzrin, Kfar Tavor, Kfar Vradim, Kiryat Ata, Kiryat Bialik, Kiryat Motzkin, Kiryat Tiv'on, Kiryat Yam, Kisra-Sumei, Ma'ale Yosef, Ma'alot-Tarshiha, Magar, Majdal Shams, Mas'ada, Mateh Asher, Megiddo, Menashe, Merom HaGalil, Metula, Mevo'ot HaHermon, Migdal, Migdal HaEmek, Misgav, Nahariya, Nesher, Nof HaGalil, Or Akiva, Pardes Hanna-Karkur, Peqi'in (Buqei'a), Rama, Ramat Yishai, Rosh Pinna, Sa'ur, Safed, Shlomi, Tiberias, Tirat Carmel, Tuba-Zangariyye, Yanouh-Jat, Yavne'el, Yesod HaMa'ala, Yirka, Yokne'am Illit, Zarziir, Zikhron Ya'akov, Zvulun

**Canton 3 - ARAB (60 municipalities):**
Abu Ghosh, Al-Batuf, Al-Qasam, Ar'ara, Ar'ara BaNegev, Arraba, Baqa al-Gharbiyye, Basma, Basmat Tab'un, Bi'ina, Bir al-Maksur, Bu'eine Nujeidat, Bustan al-Marj, Dabburiyya, Dir Hanna, Dir al-Asad, Ein Mahil, Fureidis, Hura, I'billin, Iksal, Ilut, Jadeidi-Makr, Jaljulia, Jatt, Jisr az-Zarqa, Kabul, Kafr Bara, Kafr Kanna, Kafr Manda, Kafr Qara, Kafr Qasem, Kafr Yasif, Kaukab Abu al-Hija, Kuseife, Laqiye, Ma'ale Iron, Ma'ilya, Majd al-Krum, Mashhad, Mazra'a, Nahf, Nazareth, Neve Midbar, Qalansuwa, Rahat, Reina, Sakhnin, Segev Shalom, Sha'ab, Shfar'am, Shibli-Umm al-Ghanam, Tamra, Tayibe, Tel Sheva, Tira, Tur'an, Umm al-Fahm, Yafi', Zemer

**Canton 4 - HAREDI Cities (7 municipalities):**
Beitar Illit, Bnei Brak, El'ad, Immanuel, Kiryat Ye'arim, Modi'in Illit, Rekhasim

### B. Software Architecture

```
src/
  config.py              - Project paths, constants, bloc column definitions
  data/
    loader.py            - Load election data, GeoJSON, municipality mappings
    processing.py        - Process raw elections, normalize names, match data
    representations.py   - BlocShares, RawParty, PCA, NMF feature builders
    distance_metrics.py  - Euclidean, Cosine, Jensen-Shannon distance classes
  graph/
    adjacency.py         - Build adjacency graph from geographic polygons
    preprocessing.py     - Virtual edges, enclave edges, component bridging
  clustering/
    base.py              - CantonAssignment data class, base clusterer interface
    simulated_annealing.py - SA clusterer with multi-objective cost function
    agglomerative.py     - Average-linkage with contiguity constraints
    spectral.py          - Louvain community detection (used); spectral clustering (implemented, not evaluated)
    baseline.py          - K-Means baseline (no contiguity constraints)
  evaluation/
    metrics.py           - WCSS, silhouette, population balance, contiguity
    stability.py         - Temporal stability (ARI/NMI across elections)
    experiment.py        - Experiment grid runner, result aggregation
  visualization/
    maps.py              - Static canton maps, interactive Folium maps
    charts.py            - Political composition, population balance, elbow plots

tests/                   - 73 unit tests covering all modules
notebooks/               - 6 Jupyter notebooks (exploration through experiments)
app/
  app.py                 - Streamlit main page (project overview, featured K=5 map)
  utils.py               - Shared data loading and visualization helpers
  pages/
    1_Canton_Map.py      - Interactive canton map explorer (all 264 configurations)
    2_Experiments.py     - Experiment results dashboard (heatmaps, line plots)
    3_Stability.py       - Cross-election stability analysis (ARI/NMI charts)
    4_About.py           - Project background and methodology overview
```

### C. Reproducibility

**Key Dependencies:** Python 3.12, pandas, geopandas, scikit-learn, networkx, scipy, matplotlib, seaborn, plotly, streamlit, folium.

All results can be reproduced by running the Jupyter notebooks in sequence:
1. `01_data_exploration.ipynb` - Initial data inspection
2. `02_data_processing.ipynb` - Data cleaning and integration
3. `03_adjacency_graph.ipynb` - Graph construction and preprocessing
4. `04_political_features.ipynb` - Feature representation computation
5. `05_clustering.ipynb` - Clustering algorithms (all methods, K=3--20)
6. `06_experiments.ipynb` - Full 264-config grid search, stability analysis, case studies

Requirements: Python 3.12, dependencies listed in `requirements.txt`. All source data is included in the `data/raw/` directory.
