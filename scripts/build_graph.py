#!/usr/bin/env python3
"""Rebuild the municipality adjacency graph and dissolved boundaries (notebook 03's outputs).

    python scripts/build_graph.py

Municipalities inside the Green Line keep the exact shared-border rule; Judea and
Samaria authorities (from municipalities_js.geojson) also get tolerance edges, and any
still without a neighbour is joined to its geographically nearest authority.
Fails if any edge of the previous graph is lost.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json

import geopandas as gpd
import pandas as pd

from src.config import DATA_PROCESSED, GEO_DIR, GEO_NAME_FIXES
from src.data.loader import load_municipality_geojson
from src.graph.adjacency import (
    add_tolerance_edges, build_adjacency_graph, connect_isolated_to_nearest, dissolve_municipalities, get_graph_stats,
)

TOLERANCE_M = 100.0


def main() -> None:
    graph_path = DATA_PROCESSED / "adjacency_graph.json"
    previous = json.loads(graph_path.read_text(encoding="utf-8"))
    renamed = {old: new for old, (new, _) in GEO_NAME_FIXES.items()}
    old_edges = {frozenset((renamed.get(a, a), renamed.get(b, b))) for a, nbrs in previous.items() for b in nbrs}

    geo = dissolve_municipalities(load_municipality_geojson())
    G = build_adjacency_graph(geo)
    js_path = GEO_DIR / "municipalities_js.geojson"
    js_nodes = set(gpd.read_file(js_path)["MUN_HEB"]) if js_path.exists() else set()
    G = add_tolerance_edges(G, geo, js_nodes, TOLERANCE_M)
    nearest_only = sorted(n for n in js_nodes if G.degree(n) == 0)
    G = connect_isolated_to_nearest(G, geo, js_nodes)

    new_edges = {frozenset(e) for e in G.edges()}
    lost = old_edges - new_edges
    assert not lost, f"{len(lost)} previous edges lost: {[tuple(e) for e in list(lost)[:5]]}"
    isolated = sorted(n for n in js_nodes if G.degree(n) == 0)

    adjacency = {n: sorted(G.neighbors(n)) for n in sorted(G.nodes())}
    graph_path.write_text(json.dumps(adjacency, ensure_ascii=False, indent=2), encoding="utf-8")
    edges = sorted(tuple(sorted(e)) for e in G.edges())
    pd.DataFrame(edges, columns=["municipality_1", "municipality_2"]).to_csv(
        DATA_PROCESSED / "adjacency_edges.csv", index=False, encoding="utf-8")
    geo.to_file(DATA_PROCESSED / "municipalities_dissolved.geojson", driver="GeoJSON", COORDINATE_PRECISION=6)

    print(get_graph_stats(G))
    print(f"Edges: {len(old_edges)} previous, {len(new_edges)} now; "
          f"Judea and Samaria nodes: {len(js_nodes)}; joined to nearest authority: "
          f"{[(n, next(iter(G.neighbors(n)))) for n in nearest_only]}; still isolated: {isolated}")


if __name__ == "__main__":
    main()
