#!/usr/bin/python3.13
# coding=utf-8
# %%%
import pandas as pd
import geopandas
import matplotlib.pyplot as plt
import contextily
import sklearn.cluster
import numpy as np
from shapely.geometry import Point

def make_geo(df_accidents: pd.DataFrame, df_locations: pd.DataFrame) -> geopandas.GeoDataFrame:

    #Konvertovani dataframe do geopandas.GeoDataFrame se spravnym kodovani Pozor na mozne prohozeni d a e!

    merged = df_accidents.merge(df_locations, on='p1', how='inner')

    merged = merged[(merged['d'] != 0) & (merged['e'] != 0)].copy()

    swap_mask = merged['d'] < merged['e']
    merged.loc[swap_mask, ['d', 'e']] = merged.loc[swap_mask, ['e', 'd']].values

    geometry = [Point(x, y) for x, y in zip(merged['d'], merged['e'])]

    gdf = geopandas.GeoDataFrame(merged, geometry=geometry)

    gdf = gdf.set_crs("EPSG:5514", allow_override=True)

    return gdf


def plot_geo(gdf: geopandas.GeoDataFrame, fig_location: str = None,
             show_figure: bool = False):
    # Vykresleni grafu s nehodami se zvěří pro roky 2023-2024

    REGION = "JHM"
    gdf_region = gdf[gdf['region'] == REGION].copy()

    gdf_animal = gdf_region[gdf_region['p10'] == 4].copy()

    gdf_animal['year'] = pd.to_datetime(gdf_animal['date']).dt.year

    gdf_2023 = gdf_animal[gdf_animal['year'] == 2023]
    gdf_2024 = gdf_animal[gdf_animal['year'] == 2024]

    gdf_2023_wgs = gdf_2023.to_crs("EPSG:3857")  # Web Mercator
    gdf_2024_wgs = gdf_2024.to_crs("EPSG:3857")

    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    ax1 = axes[0]
    gdf_2023_wgs.plot(ax=ax1, markersize=5, color='red', alpha=0.6)
    contextily.add_basemap(ax1, crs=gdf_2023_wgs.crs, source=contextily.providers.OpenStreetMap.Mapnik)
    ax1.set_title(f"{REGION} kraj (2023)", fontsize=14)
    ax1.axis('off')


    ax2 = axes[1]
    gdf_2024_wgs.plot(ax=ax2, markersize=5, color='red', alpha=0.6)
    contextily.add_basemap(ax2, crs=gdf_2024_wgs.crs, source=contextily.providers.OpenStreetMap.Mapnik)
    ax2.set_title(f"{REGION} kraj (2024)", fontsize=14)
    ax2.axis('off')
    plt.tight_layout()


    if fig_location:
        plt.savefig(fig_location, dpi=150, bbox_inches='tight')

    if show_figure:
        plt.show()
    else:
        plt.close()


def plot_cluster(gdf: geopandas.GeoDataFrame, fig_location: str = None,
                 show_figure: bool = False):

    REGION = "JHM"

    gdf_region = gdf[gdf['region'] == REGION].copy()
    gdf_alcohol = gdf_region[gdf_region['p11'] >= 4].copy()
    gdf_alcohol_wgs = gdf_alcohol.to_crs("EPSG:3857")

    coords = np.array([[point.x, point.y] for point in gdf_alcohol_wgs.geometry])

    dbscan = sklearn.cluster.DBSCAN(eps=3000, min_samples=10)
    gdf_alcohol_wgs['cluster'] = dbscan.fit_predict(coords)

    from shapely.geometry import MultiPoint

    cluster_polygons = []
    cluster_counts = []

    for cluster_id in sorted(gdf_alcohol_wgs['cluster'].unique()):
        if cluster_id == -1:
            continue

        cluster_points = gdf_alcohol_wgs[gdf_alcohol_wgs['cluster'] == cluster_id]
        count = len(cluster_points)

        points = MultiPoint(list(cluster_points.geometry))
        hull = points.convex_hull

        cluster_polygons.append(hull)
        cluster_counts.append(count)

    gdf_clusters = geopandas.GeoDataFrame({
        'geometry': cluster_polygons,
        'count': cluster_counts
    }, crs="EPSG:3857")

    fig, ax = plt.subplots(figsize=(14, 12))

    bounds = gdf_clusters.total_bounds
    padding = 8000  # (8km)
    ax.set_xlim(bounds[0] - padding, bounds[2] + padding)
    ax.set_ylim(bounds[1] - padding, bounds[3] + padding)

    contextily.add_basemap(
        ax,
        crs=gdf_alcohol_wgs.crs,
        source=contextily.providers.OpenStreetMap.Mapnik,
        zoom=10
    )

    gdf_clusters.plot(
        ax=ax,
        color='gray',
        alpha=0.65,
        linewidth=1.5,
        zorder=2
    )

    cluster_to_count = {}
    for cluster_id in gdf_alcohol_wgs['cluster'].unique():
        if cluster_id == -1:
            continue
        count = len(gdf_alcohol_wgs[gdf_alcohol_wgs['cluster'] == cluster_id])
        cluster_to_count[cluster_id] = count

    # print("\n📊 Clustery a ich počty:")
    # for cluster_id, count in sorted(cluster_to_count.items(), key=lambda x: x[1], reverse=True):
    #     print(f"  Cluster {cluster_id}: {count} nehôd")
    #
    # print(f"\nRozsah počtov: {min(cluster_to_count.values())} - {max(cluster_to_count.values())}")
    # print(f"Unikátne počty: {sorted(set(cluster_to_count.values()))}")
    #

    gdf_alcohol_wgs['count'] = gdf_alcohol_wgs['cluster'].map(cluster_to_count)

    gdf_in_clusters = gdf_alcohol_wgs[gdf_alcohol_wgs['cluster'] != -1]

    gdf_in_clusters.plot(
        ax=ax,
        column='count',
        cmap='viridis',
        markersize=5,
        alpha=0.8,
        zorder=3,
        legend=True,
        legend_kwds={
            'label': 'Počet nehôd v úseku',
            'orientation': 'horizontal',
            'shrink': 0.5,
            'pad': 0.03,
            'aspect': 25
        }
    )


    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")

    ax.set_title(
        f"Nehody v {REGION} kraji s významnou měrou alkoholu",
        fontsize=14,
        pad=20
    )

    plt.tight_layout()

    if fig_location:
        plt.savefig(fig_location, dpi=150, bbox_inches='tight')

    if show_figure:
        plt.show()
    else:
        plt.close()


if __name__ == "__main__":
    # zde muzete delat libovolne modifikace
    df_accidents = pd.read_pickle("accidents.pkl.gz")
    df_locations = pd.read_pickle("locations.pkl.gz")
    gdf = make_geo(df_accidents, df_locations)

    plot_geo(gdf, "geo1.png", True)
    plot_cluster(gdf, "geo2.png", True)

    # testovani splneni zadani
    import os
    assert os.path.exists("geo1.png")
    assert os.path.exists("geo2.png")