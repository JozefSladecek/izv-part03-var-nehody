#!/usr/bin/python3.13
# coding=utf-8
# %%%
import pandas as pd
import geopandas
import matplotlib.pyplot as plt
import contextily
import sklearn.cluster
import numpy as np

def make_geo(df_accidents: pd.DataFrame, df_locations: pd.DataFrame) -> geopandas.GeoDataFrame:
    
    #Konvertovani dataframe do geopandas.GeoDataFrame se spravnym kodovani Pozor na mozne prohozeni d a e!
    pass

def plot_geo(gdf: geopandas.GeoDataFrame, fig_location: str = None,
             show_figure: bool = False):
    # Vykresleni grafu s nehodami se zvěří pro roky 2023-2024 
    pass


def plot_cluster(gdf: geopandas.GeoDataFrame, fig_location: str = None,
                 show_figure: bool = False):
    # Vykresleni grafu s lokalitou vsech nehod v kraji shlukovanych do clusteru
    pass

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