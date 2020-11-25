import os
import sys

import matplotlib.pyplot as plt

from ghaa.config import load_config
from ghaa.plot.map import get_axes, plot_basemap, plot_raster


if __name__ == '__main__':
    base_path = load_config()["base_path"]
    try:
        tif_path = sys.argv[1]
    except:
        # GeoTIFF to plot
        tif_path = os.path.join(
            base_path, 'results', 'proximity_results',
            'population_gha_2019-07-01_proximity_downsampled.tif')

    try:
        png_path = sys.argv[2]
    except:
        # PNG output - default to same name as TIF, but .png
        png_path = os.path.join(
            os.path.dirname(tif_path),
            os.path.basename(tif_path).replace(".tif", ".png"))

    print("Plotting", tif_path)
    print("to image", png_path)
    ax = get_axes()
    plot_raster(ax, tif_path, base_path)
    plot_basemap(ax, os.path.join(base_path, 'data'))
    plt.savefig(png_path)
