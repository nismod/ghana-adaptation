"""Exposure analysis for presentation in Nov

Calculate the intersection of hazards and infrastructure networks.
"""
import glob
import json
import os

import geopandas


def main():
    """Read files and do intersections
    """
    config = load_config()
    base_path = config['base_path']

    # Setting up the paths
    hazard_paths = glob.glob(
        os.path.join(base_path, 'data', 'hazard_fl_pres', '*.shp'))

    network_path = os.path.join(
        base_path, 'data', 'infrastructure_pres','GHA_highway.shp')

    # Reading infrastructure network
    network_df = geopandas.read_file(network_path)

    for hazard_path in hazard_paths:
        hazard_id = os.path.basename(hazard_path).replace(".shp", "")
        print("Processing", hazard_id)

        # Reading hazard outlines
        hazard_df = geopandas.read_file(hazard_path)

        # convert to 32630
        # hazard_df = hazard_df.to_crs(epsg=4326)

        # Do intersection
        intersection_df = geopandas.overlay(network_df, hazard_df, how='intersection')

        # Write intersection data
        intersection_df.to_file(
            os.path.join(base_path, 'results', 'exposure', f"highways__{hazard_id}.gpkg"),
            driver="GPKG")


def load_config():
    config_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'config.json')
    with open(config_path) as fh:
        config = json.load(fh)
        print(config)
    return config


if __name__ == '__main__':
    main()
