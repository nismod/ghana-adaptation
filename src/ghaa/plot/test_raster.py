import os
import matplotlib.pyplot as plt

from ghaa.config import load_config
from ghaa.plot.map import get_axes_for_raster, plot_raster


if __name__ == '__main__':
    base_path = load_config()["base_path"]

    # GeoTIFF to plot
    tif_path = os.path.join(
        base_path, 'results', 'proximity_results',
        'population_gha_2019-07-01_proximity_distance.tif')
    ax = get_axes_for_raster()
    plot_raster(ax, tif_path, base_path)
    plt.savefig('test_access.png')

    # Accra
    left = -0.5
    bottom = 5.4
    right = 0.1
    top = 5.8
    extent = (left, bottom, right, top)
    ax = get_axes_for_raster()
    plot_raster(ax, tif_path, base_path, extent=extent)
    plt.savefig('test_access_accra.png')
