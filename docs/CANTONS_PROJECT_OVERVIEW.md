# Divide Israel into Cantons Based on Election Results

**M.Sc. Computer Science Project Proposal**  
Student: Adir Elmakais (ID 316413640)  
Advisor: Dr. Oren Glickman  
Academic Year: 2025-2026

---

## Background and Motivation

Over the past four years, Israel has held five Knesset elections, reflecting deep political divisions across multiple dimensions - secular vs. religious, left vs. right, Jewish vs. Arab communities, and attitudes toward governance and judicial reform. Throughout this period, public discourse has repeatedly invoked the idea of dividing Israel into politically distinct "cantons" or regions - contrasting, for example, liberal-secular Tel Aviv with religious-conservative Jerusalem, or Arab-majority towns in the north with predominantly Jewish communities elsewhere.

While this talk is mostly rhetorical, it raises an interesting computational question: if we were to divide Israel into regions based purely on voting patterns, what would those regions look like? How stable would they be across different elections? This project explores these questions using publicly available town-level election data and geographic boundary information.

## Project Goal

I will develop a data-driven algorithmic approach to partition Israeli municipalities into geographically contiguous "cantons" that maximize internal political similarity. The system will use town-level election results from the five most recent Knesset elections (2019-2022) combined with municipal boundary data from the Israel Central Bureau of Statistics.

The project has both technical and analytical goals: (1) design and implement a spatially-constrained clustering algorithm, and (2) produce an interactive visualization tool that lets users explore how different numbers of cantons and different election cycles affect the resulting divisions.

## Planned Approach

**Data and Representation**  
Each municipality will be represented as a vector of vote shares for different political parties or political blocs (right-wing, center/left, Arab parties, etc.). I'll construct a geographic adjacency graph from municipal boundary polygons to encode which towns share borders.

**Core Algorithm**
The main challenge is that standard clustering algorithms don't respect geographic constraints - they might group Tel Aviv with a town in the Negev if they vote similarly. I'll implement a greedy agglomerative spatial clustering algorithm that starts with each town as its own cluster and iteratively merges adjacent clusters that are most similar politically, continuing until we reach the target number of cantons. This ensures every canton is geographically contiguous.

**Analysis and Comparison**
I'll run experiments with different numbers of cantons (K = 3, 5, 7, 10, etc.) and compare results across the five elections to measure stability. I'll also compare against simple baselines - standard clustering without spatial constraints, purely graph-based clustering, and existing administrative divisions - to understand how much the geographic constraint affects results.

**Visualization**  
I'll build an interactive tool (initially a Jupyter notebook with maps, potentially a web interface later) where users can select an election and number of cantons, then see the resulting map with canton boundaries and political profiles.

## Work Plan

The project will unfold over approximately 12 months in these phases:

- **Months 1-2:** Literature review on spatial clustering and electoral geography; acquire and explore election data and municipal boundary files.
- **Months 2-4:** Clean and integrate data; build the contiguity graph; design political feature vectors.
- **Months 4-7:** Implement the greedy spatial clustering algorithm and baseline methods; validate correctness on test cases.
- **Months 7-9:** Run experiments across elections and parameter values; compute quality metrics; analyze stability.
- **Months 9-11:** Build interactive visualization tools; refine based on feedback.
- **Months 11-12:** Write final report, ensure reproducibility.

## Expected Outcomes

By the end of the project, I will deliver:

- **Working code:** A clean, documented Python pipeline from raw data to canton maps, including the clustering algorithm and evaluation scripts.
- **Visualizations:** Interactive maps showing canton divisions for different elections and parameters, with canton-level political profiles.
- **Analysis:** Quantitative evaluation of clustering quality, stability across elections, and comparison to baselines.
- **Final report:** A comprehensive technical report documenting the methodology, results, and insights, formatted according to departmental guidelines.

The project connects computer science (algorithms, graph theory, spatial data structures), data science (clustering, feature engineering), and geographic information systems, while addressing a socially and politically relevant question in a purely descriptive, analytical manner.
