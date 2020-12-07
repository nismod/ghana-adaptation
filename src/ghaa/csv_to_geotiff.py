"""Convert CSV to GeoTIFF
"""
import os
import sys

import numpy as np
import pandas
import rasterio

from ghaa.config import load_config


def convert_csv_to_tiff(template_path, csv_path, tif_path, value_col='val',
                        x_col='x', y_col='y', fn=None):
    """Convert CSV to GeoTIFF
    """
    with rasterio.open(template_path) as ds:
        transform = ds.transform
        crs = ds.crs

    arr = np.full(ds.shape, -999.0)

    df = pandas.read_csv(
        csv_path, usecols=[value_col, x_col, y_col])

    if fn is not None:
        df[value_col] = df.apply(fn, axis=1)

    # Enumerate columns to use index in itertuples
    idx = {name: i for i, name in enumerate(df.columns, start=1)}
    x_idx = idx[x_col]
    y_idx = idx[y_col]
    value_idx = idx[value_col]

    for obs in df.itertuples():
        row, col = ds.index(obs[x_idx], obs[y_idx])
        arr[row, col] = obs[value_idx]


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

    try:
        csv_path = sys.argv[1]
    except:
        # CSV input
        csv_path = os.path.join(
            base_path, 'results', 'proximity_results',
            'population_gha_2019-07-01_proximity.csv')

    try:
        value_col = sys.argv[2]
    except:
        # Column
        value_col = 'length_km'

    try:
        tif_path = sys.argv[3]
    except:
        # GeoTIFF output - default to same name as CSV, but .tif
        tif_path = os.path.join(
            os.path.dirname(csv_path),
            os.path.basename(csv_path).replace(".csv", ".tif"))

    try:
        # Use tiff transform and bounds as template
        template_path = sys.argv[4]
    except:
        # Default to population raster
        template_path = os.path.join(
            base_path, 'incoming', 'population',
            'Population Density& Demographics',
            'ID 23_Population_Density_Demographics - fb AI',
            'population_gha_2019-07-01_geotiff',
            'population_gha_2019-07-01.tif')


    print("Input CSV", csv_path)
    print("Input column", value_col)
    print("Output TIF", tif_path)
    print("Template TIF", template_path)

    def fix_zero_access(row):
        if row.access == 0:
            return 100
        else:
            return row.length_km

    convert_csv_to_tiff(
        template_path, csv_path, tif_path,
        value_col=value_col,
        fn=fix_zero_access
    )
