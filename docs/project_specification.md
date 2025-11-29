You are an expert academic writing assistant.  
Please generate a **concise but professional project specification** in **Markdown format** (no code fences around the whole document).

The document is for a **year-long M.Sc. (non-thesis) project in Computer Science at Bar-Ilan University**, and is intended as a **short project proposal for advisor approval**, not as a full thesis proposal.

---

### General instructions

- **Language:** English.
- **Length:** About 2–3 pages of text (roughly 1200–1800 words, not more).
- **Style:** Clear, formal but not overly heavy. The goal is: something the advisor can read in a few minutes and say “OK, you can start”.
- **Perspective:** Third person (“the student will…”).
- **Audience:** Dr. Oren Glickman, Computer Science Department, Bar-Ilan University.
- Do **not** surround the whole document with ``` or any other code fences. Just plain Markdown headings and text.

---

### Project context (use this as factual basis)

- **Project Title:** Divide Israel into Cantons Based on Election Results  
- **Advisor:** Dr. Oren Glickman (CS, Bar-Ilan University)  
- **Degree:** M.Sc. in Computer Science, non-thesis project track  
- **Short idea:**
  - Israeli society is highly polarized politically, and there is recurring public discussion about “splitting Israel into cantons” (e.g., a more liberal “Tel Aviv canton” vs a more conservative “Jerusalem canton”).
  - In the last 4 years there have been **5 national elections**, and detailed **town-level election results** are publicly available.
  - Geographic polygon data (municipal boundaries) for Israeli towns is also available (e.g., via the Israel Central Bureau of Statistics).
  - The project aims to:
    - Represent each town by its voting pattern (vote shares per party or political bloc).
    - Build a contiguity graph of towns based on shared geographic borders.
    - Develop a **greedy spatial clustering algorithm** that merges adjacent, politically-similar towns into **contiguous cantons**.
    - Provide a **simple visual interface** (map) where a user can choose parameters (election round, number of cantons K) and see the resulting division.

---

### Required structure of the Markdown document

Please generate a document with the following sections (exact headings), but keep each section **fairly compact**.

1. `# Project Specification: Divide Israel into Cantons Based on Election Results`

2. `## 1. Project Overview`
   - 1–2 paragraphs that:
     - Briefly describe the motivation (political polarization and the idea of cantons).
     - Explain that this is a data-driven, algorithmic project in computer science.
     - Emphasize that the project is exploratory and descriptive, not a political statement.

3. `## 2. Objectives`
   - A short bullet list of clear, concrete objectives, for example:
     - Build a town-level political representation from election results.
     - Construct a geographic contiguity graph over towns in Israel.
     - Design and implement a greedy clustering algorithm that produces contiguous cantons with similar voting patterns.
     - Develop a simple visualization tool to display the resulting cantons on a map.
     - Perform basic evaluation and exploratory analysis (stability across elections, effect of the number of cantons K).
   - Keep it compact and readable, around 5–7 bullets.

4. `## 3. Data and Tools`
   - A short description (1–2 paragraphs + bullet list) of:
     - Election data: town-level results for recent Knesset elections (vote counts per party, turnout, etc.).
     - Geographic data: town polygons / municipal boundaries, used to determine adjacency.
     - The main tools/technologies the student plans to use (as a proposal, not a commitment), e.g.:
       - Python, `pandas`, `numpy` for data processing.
       - `geopandas`, `shapely` for geographic operations.
       - `networkx` for graph representation.
       - Simple mapping tools (e.g., `folium` or a basic web map) for visualization.
   - Mention expected preprocessing challenges very briefly (matching town names/codes, handling small towns, etc.), but do not go into deep detail.

5. `## 4. Proposed Method`
   - 3–5 short paragraphs that describe, at a **high level**, the planned approach:
     - How each town will be represented as a political vector (e.g., vote shares per party or per bloc).
     - How the contiguity graph will be built from geographic polygons.
     - The **idea** of a greedy spatial clustering algorithm:
       - Start with each town as its own cluster.
       - Iteratively merge neighboring clusters that are politically similar.
       - Stop when a target number of cantons K is reached, or a stopping condition is met.
     - Mention that the algorithm must respect geographic contiguity (each canton should be a connected region).
     - Mention briefly that one or two simple baselines (e.g., clustering without spatial constraints) may be used for comparison.
   - The level here should be understandable in a quick read, without formulas or heavy theory.

6. `## 5. System and Expected Deliverables`
   - Describe in 2–3 short subsections or paragraphs:
     - **Core components**:
       - Data processing and integration scripts.
       - Clustering module implementing the greedy algorithm.
       - A basic visualization component (e.g., a small web app or notebook-based map) that shows cantons on a map and allows choosing K and election round.
     - **Deliverables at the end of the project** (bulleted):
       - Source code (well organized and documented).
       - A reproducible pipeline from raw data to canton maps.
       - Example canton maps for several election rounds and values of K.
       - A short written final report summarizing the approach and main findings.

7. `## 6. Work Plan (High Level)`
   - A **brief**, realistic plan for roughly one academic year, broken into 4–5 stages. For example:
     - Months 1–2: Data collection, basic preprocessing, first exploratory analysis.
     - Months 3–4: Build political feature representation and contiguity graph.
     - Months 5–7: Design and implement the greedy clustering algorithm and simple baselines.
     - Months 8–9: Run experiments, analyze results, refine the method.
     - Months 10–12: Build visualization, finalize code, prepare the final report.
   - For each stage, give 1–2 bullet points of expected outputs.
   - Keep this section short and pragmatic, focusing on giving the advisor confidence that there is a realistic plan.

8. `## 7. Scope, Limitations, and Risks`
   - A short section (1–2 paragraphs + a few bullets) noting:
     - This is **not** a political proposal, but a methodological and exploratory project.
     - Results will depend on data quality and on modeling decisions (e.g., how parties are grouped into blocs).
     - Possible technical risks (data inconsistencies, algorithmic complexity) and a short sentence on how the student plans to handle them at a reasonable level (e.g., simplifying models if needed).
   - The tone should be modest and realistic, not overselling.

9. `## 8. Summary`
   - A short closing paragraph (4–6 sentences) that:
     - Reiterates the main idea of the project.
     - Emphasizes the combination of real political data, geographic information, and algorithmic thinking.
     - States that the project should be feasible within one year.
     - States that the document is intended as a starting specification for the advisor’s feedback and approval.

---

Please now generate the **complete Markdown document** following all the instructions above, so that it can be used directly as `project_spec.md` and sent to the advisor for initial approval.
