import os

import cartopy.crs as ccrs
import geopandas
import matplotlib.cm
import matplotlib.colors
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import rasterio
import rasterio.plot
import rasterio.windows
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


def get_axes_for_raster():
    """Plain Axes object - must project anything before plotting
    (no cartopy convenience, but this lets GeoPandas)
    """
    return plt.axes([0.025, 0.025, 0.95, 0.95])


def plot_raster(ax, tif_path, base_path, extent=(-3.82, 1.82, 4.37, 11.51),
                cmap='viridis', plot_regions=False):
    """Plot raster with vectors/labels
    """
    # Unpack extent
    left, bottom, right, top = extent

    # Open raster, read window
    with rasterio.open(tif_path) as src:
        window = rasterio.windows.from_bounds(
            left, bottom, right, top, src.transform)
        rst = src.read(1, window=window)

    # Plot raster
    rasterio.plot.show(rst, cmap=cmap, ax=ax, transform=src.window_transform(window))

    # Set up colorbar
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.09)
    norm = matplotlib.colors.Normalize(vmin=0, vmax=rst.max())
    mappable = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
    fig = ax.figure
    fig.colorbar(mappable, cax=cax)

    # Read vectors
    states = geopandas.read_file(
        os.path.join(base_path, 'data', 'admin', 'GHA_admin0.gpkg')) \
        .to_crs(src.crs)

    lakes = geopandas.read_file(
        os.path.join(base_path, 'data', 'nature', 'Polygons', 'GHA_lakes.gpkg')) \
        .to_crs(src.crs)

    # Polygon for clipping
    bbpoly = shapely.geometry.box(left, bottom, right, top)

    # Clip vectors
    states = geopandas.clip(states, bbpoly)
    lakes = geopandas.clip(lakes, bbpoly)

    # Plot vectors
    states.plot(ax=ax, facecolor='#00000000', edgecolor='#ffffff')
    lakes.plot(ax=ax, edgecolor='none', facecolor='#87cefa', zorder=1)

    if plot_regions:
        regions = geopandas.read_file(
            os.path.join(base_path, 'data', 'admin', 'GHA_admin1.gpkg')) \
            .to_crs(src.crs)
        regions = geopandas.clip(regions, bbpoly)
        regions.plot(ax=ax, edgecolor='#ffffff', facecolor='#00000000', zorder=2)

    # Set axis off
    ax.axis('off')

    return ax


def plot_basemap(ax, data_path, ax_crs=3857, plot_regions=False):
    """Plot countries and regions background
    """
    states = geopandas.read_file(
        os.path.join(data_path, 'admin', 'GHA_admin0.gpkg')).to_crs(ax_crs)

    lakes = geopandas.read_file(
        os.path.join(data_path, 'nature', 'Polygons', 'GHA_lakes.gpkg')).to_crs(ax_crs)

    states.plot(ax=ax, edgecolor='#ffffff', facecolor='#e4e4e3', zorder=1)

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
