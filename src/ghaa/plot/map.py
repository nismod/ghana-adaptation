import os

import cartopy.crs as ccrs
import geopandas
import matplotlib.cm
import matplotlib.colors
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import rasterio
import rioxarray
import shapely.geometry


def save_fig(output_filename):
    plt.savefig(output_filename)


def get_axes(extent=(-3.82, 1.82, 4.37, 11.51)):
    """Get map axes
    """
    ax_proj = ccrs.epsg(3857)

    plt.figure(figsize=(4, 6), dpi=150)
    ax = plt.axes([0.025, 0.025, 0.95, 0.95], projection=ax_proj)
    proj = ccrs.PlateCarree()
    ax.set_extent(extent, crs=proj)
    ax.patch.set_facecolor('#bfc0bf')

    return ax


def plot_raster(ax, tif_path, cmap='viridis', levels=None, colors=None,
                clip_extent=None):
    """Plot raster with vectors/labels
    """
    # Open raster
    ds = rioxarray.open_rasterio(tif_path, mask_and_scale=True)
    if clip_extent is not None:
        left, right, bottom, top = clip_extent
        ds = ds.rio.clip_box(
            minx=left,
            miny=bottom,
            maxx=right,
            maxy=top,
        )

    # Check raster CRS
    with rasterio.open(tif_path) as da:
        crs_code = da.crs.to_epsg()

    if crs_code == 4326:
        crs = ccrs.PlateCarree()
    else:
        crs = ccrs.epsg(crs_code)

    # Plot raster
    if levels is not None and colors is not None:
        ds.plot(
            ax=ax,
            levels=levels,
            colors=colors,
            transform=crs
        )
    else:
        ds.plot(
            ax=ax,
            cmap=cmap,
            transform=crs
        )

    return ax


def plot_basemap(ax, data_path, ax_crs=3857, plot_regions=False):
    """Plot countries and regions background
    """
    states = geopandas.read_file(
        os.path.join(data_path, 'admin', 'GHA_admin0.gpkg')).to_crs(ax_crs)

    lakes = geopandas.read_file(
        os.path.join(data_path, 'nature', 'Polygons', 'GHA_lakes.gpkg')).to_crs(ax_crs)

    states.plot(ax=ax, edgecolor='#ffffff', facecolor='#e4e4e300', zorder=1)

    if plot_regions:
        regions = geopandas.read_file(
            os.path.join(data_path, 'admin', 'GHA_admin1.gpkg')).to_crs(ax_crs)
        regions.plot(ax=ax, edgecolor='#00000000', facecolor='#dededc')
        regions.plot(ax=ax, edgecolor='#ffffff', facecolor='#00000000', zorder=2)

    lakes.plot(ax=ax, edgecolor='none', facecolor='#87cefa', zorder=1)


def plot_basemap_labels(ax, data_path, include_regions=False, include_zorder=2):
    """Plot countries and regions background
    """
    proj = ccrs.PlateCarree()
    labels = [
        # ("Ghana", -1.1755, 6.9591),
        ("Togo", 1.0546, 8.7439),
        ("Burkina Faso", -1.2084, 11.2046),
        ("Ivory Coast", -3.2080, 8.2767),
    ]

    if include_regions:
        regions = geopandas.read_file(
            os.path.join(data_path, 'admin', 'GHA_admin1.gpkg')).to_crs(4326)
        regions_labels = [
            (r.ADMIN_1_NAME, r.geometry.centroid.x, r.geometry.centroid.y)
            for r in regions.itertuples()
        ]
        labels += regions_labels

    for text, x, y in labels:
        ax.text(
            x,
            y,
            text,
            size=6,
            alpha=0.7,
            horizontalalignment='center',
            zorder = include_zorder,
            transform=proj
        )


def scale_bar(ax, length=100, location=(0.8, 0.05), linewidth=3):
    """Draw a scale bar
    Adapted from https://stackoverflow.com/questions/32333870/how-can-i-show-a-km-ruler-on-a-cartopy-matplotlib-plot/35705477#35705477
    Parameters
    ----------
    ax : axes
    length : int
        length of the scalebar in km.
    location: tuple
        center of the scalebar in axis coordinates (ie. 0.5 is the middle of the plot)
    linewidth: float
        thickness of the scalebar.
    """
    # lat-lon limits
    llx0, llx1, lly0, lly1 = ax.get_extent(ccrs.PlateCarree())

    # Transverse mercator for length
    x = (llx1 + llx0) / 2
    y = lly0 + (lly1 - lly0) * location[1]
    tmc = ccrs.TransverseMercator(x, y)

    # Extent of the plotted area in coordinates in metres
    x0, x1, y0, y1 = ax.get_extent(tmc)

    # Scalebar location coordinates in metres
    sbx = x0 + (x1 - x0) * location[0]
    sby = y0 + (y1 - y0) * location[1]
    bar_xs = [sbx - length * 500, sbx + length * 500]

    # Plot the scalebar and label
    ax.plot(bar_xs, [sby, sby], transform=tmc, color='k', linewidth=linewidth)
    ax.text(sbx, sby + 50*length, str(length) + ' km', transform=tmc,
            horizontalalignment='center', verticalalignment='bottom', size=8)
