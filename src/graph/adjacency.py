"""Build spatial adjacency graph from municipality GeoJSON polygons.

Extracts logic from notebook 03.
"""

from __future__ import annotations

import geopandas as gpd
import networkx as nx


def dissolve_municipalities(
    geo: gpd.GeoDataFrame, name_col: str = "MUN_HEB"
) -> gpd.GeoDataFrame:
    """Dissolve multi-polygon features into one geometry per municipality.

    Removes the "no jurisdiction" (``ללא שיפוט``) entry if present.
    """
    geo = geo.copy()
    geo[name_col] = geo[name_col].str.strip()
    geo_dissolved = geo.dissolve(by=name_col).reset_index()

    if "ללא שיפוט" in geo_dissolved[name_col].values:
        geo_dissolved = geo_dissolved[geo_dissolved[name_col] != "ללא שיפוט"]

    return geo_dissolved


def build_adjacency_graph(
    geo_dissolved: gpd.GeoDataFrame, name_col: str = "MUN_HEB"
) -> nx.Graph:
    """Build an undirected adjacency graph from dissolved municipality polygons.

    Two municipalities are neighbours if their geometries share a boundary
    line (``intersection.length > 0``).
    """
    G = nx.Graph()

    for _, row in geo_dissolved.iterrows():
        G.add_node(row[name_col])

    for i, row1 in geo_dissolved.iterrows():
        for j, row2 in geo_dissolved.iterrows():
            if i >= j:
                continue
            if row1.geometry.touches(row2.geometry) or row1.geometry.intersects(row2.geometry):
                intersection = row1.geometry.intersection(row2.geometry)
                if intersection.length > 0:
                    G.add_edge(row1[name_col], row2[name_col])

    return G


def get_graph_stats(G: nx.Graph) -> dict:
    """Return summary statistics for the adjacency graph."""
    degrees = [d for _, d in G.degree()]
    components = list(nx.connected_components(G))
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "avg_degree": sum(degrees) / max(len(degrees), 1),
        "min_degree": min(degrees) if degrees else 0,
        "max_degree": max(degrees) if degrees else 0,
        "n_components": len(components),
        "largest_component": max(len(c) for c in components) if components else 0,
        "isolated_nodes": sum(1 for d in degrees if d == 0),
    }
