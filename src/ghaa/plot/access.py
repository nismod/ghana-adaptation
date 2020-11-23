import os

import numpy as np
import pandas
import rasterio

from ghaa.config import load_config

base_path = load_config()["base_path"]

pop_path = os.path.join(
    base_path, 'incoming', 'population',
    'Population Density& Demographics',
    'ID 23_Population_Density_Demographics - fb AI',
    'population_gha_2019-07-01_geotiff',
    'population_gha_2019-07-01.tif')

access_path = os.path.join(
    base_path, 'results', 'proximity_results',
    'population_gha_2019-07-01_proximity_distance.csv')

access_tif_path = os.path.join(
    base_path, 'results', 'proximity_results',
    'population_gha_2019-07-01_proximity_distance.tif')


def create_z(pop_path, access_path):

    with rasterio.open(pop_path) as ds:
        transform = ds.transform
        crs = ds.crs
        pass
    Z = np.full(ds.shape, -999.0)

    access = pandas.read_csv(
        access_path, usecols=['length_km', 'access', 'x', 'y'])

    for obs in access.itertuples():
        row, col = ds.index(obs.x, obs.y)
        Z[row, col] = obs.length_km
    return Z, crs, transform

Z, crs, transform = create_z(pop_path, access_path)

with rasterio.open(
        access_tif_path,
        'w',
        driver='GTiff',
        height=Z.shape[0],
        width=Z.shape[1],
        count=1,
        dtype=Z.dtype,
        crs=crs,
        transform=transform,
        nodata=-999.0
    ) as new_dataset:
    new_dataset.write(Z, 1)
