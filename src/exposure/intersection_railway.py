"""Exposure analysis

Calculate the intersection of hazards and infrastructure networks.
"""
import csv
import glob
import json
import os

import geopandas
from shapely.wkt import dumps
from tqdm import tqdm


def main():
    """Read files and do intersections
    """
    config = load_config()
    base_path = config['base_path']
    epsg_code = 32630 # 32630 is UTM Zone 30N, suitable for Ghana

    # Setting up the paths
    hazard_paths = glob.glob(
        os.path.join(base_path, 'data', 'hazard_fl_pres', '*.shp'))

    network_path = os.path.join(
        base_path, 'data', 'infrastructure', 'GHA_railway_new.shp')

    # Reading infrastructure network, convert to projected CRS
    network_df = geopandas.read_file(network_path).to_crs(epsg=epsg_code)

    for hazard_path in hazard_paths:
        hazard_id = os.path.basename(hazard_path).replace(".shp", "")
        # if "medium" in hazard_id: # DEBUG
        #     continue

        print("Processing", hazard_id)

        # Reading hazard outlines
        hazard_df = geopandas.read_file(hazard_path)

        # Convert to projected CRS
        hazard_df = hazard_df.to_crs(epsg=epsg_code)

        # Do intersection
        intersections = []
        csv_fname = os.path.join(
            base_path, 'results', 'exposure', f"railwaysnew__{hazard_id}.csv")

        with open(csv_fname, 'w') as fh:
            w = csv.DictWriter(fh, fieldnames=('railway_id', 'hazard_id', 'name', 'length', 'geom'))
            w.writeheader()

            for hazard_n, hazard in enumerate(hazard_df.itertuples()):
                # if hazard_n != 133485: # DEBUG
                #     continue

                print("considering", hazard_n)
                if hazard.geometry.geom_type == 'MultiPolygon':
                    geoms = [p for p in hazard.geometry]
                else:
                    geoms = [hazard.geometry]

                for hazard_geom in geoms:
                    # Try fixing invalid geometry
                    if not hazard_geom.is_valid:
                        print("fixing", hazard_n)
                        hazard_geom = hazard_geom.buffer(0)
                        print("fixed", hazard_n)

                    # Use spatial index to find candidate road segments
                    potential_railways = network_df.iloc[
                        list(network_df.sindex.intersection(hazard_geom.bounds))]
                    print("found", len(potential_railways), "railways")

                    if len(potential_railways):
                        for railway in potential_railways.itertuples():
                            print(railway.ID, hazard_n)
                            if railway.geometry.intersects(hazard_geom):
                                print("intersects")
                                intersection_geom = railway.geometry.intersection(hazard_geom)
                                print("done intersection")
                                w.writerow({
                                    'railway_id': railway.ID,
                                    'hazard_id': hazard_n,
                                    'name': railway.NAME,
                                    'length': intersection_geom.length
                                })
                                intersections.append({
                                    'railway_id': railway.ID,
                                    'hazard_id': hazard_n,
                                    'name': railway.NAME,
                                    'length': intersection_geom.length,
                                    'geometry': intersection_geom
                                })

                        fh.flush()

        # Write intersection data
        fname = os.path.join(
            base_path, 'results', 'exposure', f"railwaysnew__{hazard_id}.gpkg")
        intersections_df = geopandas.GeoDataFrame(intersections).set_crs(epsg=epsg_code)
        intersections_df.to_file(fname, driver="GPKG")


def load_config():
    config_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'config.json')
    with open(config_path) as fh:
        config = json.load(fh)
    return config


if __name__ == '__main__':
    main()
