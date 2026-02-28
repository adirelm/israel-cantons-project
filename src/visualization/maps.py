"""Canton map visualisations (matplotlib + folium).

Extracts plotting logic from notebook 05 cells 21-22.
"""

from __future__ import annotations

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import numpy as np

from src.clustering.base import CantonAssignment


# Default canton colour palette
_CANTON_COLORS = [
    "#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
    "#ffff33", "#a65628", "#f781bf", "#999999", "#66c2a5",
    "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f",
    "#e5c494", "#b3b3b3", "#8dd3c7", "#fb8072", "#80b1d3",
]

_BLOC_COLORS = {
    "right": "blue", "haredi": "black", "center": "purple",
    "left": "red", "arab": "green",
}


def plot_cantons(
    assignment: CantonAssignment,
    geo: gpd.GeoDataFrame,
    profiles: pd.DataFrame | None = None,
    title: str = "Cantons",
    name_col: str = "MUN_HEB",
    ax: plt.Axes | None = None,
    figsize: tuple[int, int] = (14, 16),
) -> plt.Figure:
    """Plot canton map coloured by canton ID with legend."""
    geo_c = geo.copy()
    geo_c["canton"] = geo_c[name_col].map(assignment.assignments)
    geo_c = geo_c.dropna(subset=["canton"])
    geo_c["canton"] = geo_c["canton"].astype(int)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    legend_patches = []
    for cid in sorted(geo_c["canton"].unique()):
        color = _CANTON_COLORS[int(cid) % len(_CANTON_COLORS)]
        canton_geo = geo_c[geo_c["canton"] == cid]
        canton_geo.plot(ax=ax, color=color, edgecolor="black", linewidth=0.5)

        label = f"Canton {cid}"
        if profiles is not None and cid in profiles["canton"].values:
            row = profiles[profiles["canton"] == cid].iloc[0]
            bloc = row.get("dominant_bloc", "")
            voters = row.get("total_voters", 0)
            label = f"Canton {cid}: {str(bloc).upper()} ({int(voters):,})"
        legend_patches.append(mpatches.Patch(color=color, label=label))

    ax.legend(handles=legend_patches, loc="lower right", fontsize=10,
              title="Cantons", title_fontsize=11, framealpha=0.9)
    ax.set_title(title, fontsize=14)
    ax.set_axis_off()
    fig.tight_layout()
    return fig


def plot_canton_comparison(
    assignments: list[CantonAssignment],
    geo: gpd.GeoDataFrame,
    titles: list[str],
    name_col: str = "MUN_HEB",
    ncols: int = 3,
    figsize_per: tuple[int, int] = (6, 8),
) -> plt.Figure:
    """Side-by-side canton maps for comparing configurations."""
    n = len(assignments)
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(figsize_per[0] * ncols, figsize_per[1] * nrows))
    axes_flat = np.array(axes).flatten() if n > 1 else [axes]

    for i, (asgn, title) in enumerate(zip(assignments, titles)):
        plot_cantons(asgn, geo, title=title, name_col=name_col, ax=axes_flat[i])

    for j in range(i + 1, len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.tight_layout()
    return fig


def create_folium_map(
    assignment: CantonAssignment,
    geo: gpd.GeoDataFrame,
    profiles: pd.DataFrame | None = None,
    name_col: str = "MUN_HEB",
):
    """Interactive Folium map with canton tooltips.

    Returns a ``folium.Map`` object.
    """
    import folium

    geo_c = geo.copy()
    geo_c["canton"] = geo_c[name_col].map(assignment.assignments)
    geo_c = geo_c.dropna(subset=["canton"])
    geo_c["canton"] = geo_c["canton"].astype(int)

    center = [31.5, 35.0]  # Roughly center of Israel
    m = folium.Map(location=center, zoom_start=8)

    for _, row in geo_c.iterrows():
        cid = int(row["canton"])
        color = _CANTON_COLORS[cid % len(_CANTON_COLORS)]
        tooltip = f"{row[name_col]} — Canton {cid}"
        folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda _x, c=color: {
                "fillColor": c, "color": "black",
                "weight": 0.5, "fillOpacity": 0.6,
            },
            tooltip=tooltip,
        ).add_to(m)

    return m
