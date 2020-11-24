"""Convert CSV to GeoTIFF
"""
import os

import numpy as np
import pandas
import rasterio

from ghaa.config import load_config


def convert_csv_to_tiff(template_path, csv_path, tif_path, value_col='val',
                        x_col='x', y_col='y'):
    """Convert CSV to GeoTIFF
    """
    with rasterio.open(template_path) as ds:
        transform = ds.transform
        crs = ds.crs

    arr = np.full(ds.shape, -999.0)

    df = pandas.read_csv(
        csv_path, usecols=[value_col, x_col, y_col])

    for obs in df.itertuples():
        row, col = ds.index(obs[x_col], obs[y_col])
        arr[row, col] = obs[value_col]


    with rasterio.open(
            tif_path,
            'w',
            driver='GTiff',
            height=arr.shape[0],
            width=arr.shape[1],
            count=1,
            dtype=arr.dtype,
            crs=crs,
            transform=transform,
            nodata=-999.0
        ) as ds:
        ds.write(arr, 1)


if __name__ == '__main__':
    base_path = load_config()["base_path"]

    # Use population tiff transform and bounds as template
    template_path = os.path.join(
        base_path, 'incoming', 'population',
        'Population Density& Demographics',
        'ID 23_Population_Density_Demographics - fb AI',
        'population_gha_2019-07-01_geotiff',
        'population_gha_2019-07-01.tif')

    # CSV input
    csv_path = os.path.join(
        base_path, 'results', 'proximity_results',
        'population_gha_2019-07-01_proximity_distance.csv')

    # GeoTIFF output
    tif_path = os.path.join(
        base_path, 'results', 'proximity_results',
        'population_gha_2019-07-01_proximity_distance.tif')

    convert_csv_to_tiff(
        template_path, csv_path, tif_path,
        value_col='time_hr'
    )
