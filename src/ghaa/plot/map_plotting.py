"""Road network risks and adaptation maps
"""
import os
import sys
from collections import namedtuple, OrderedDict
import ast
import numpy as np
import geopandas
import pandas as pd
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from shapely.geometry import LineString
from matplotlib.lines import Line2D

Style = namedtuple('Style', ['color', 'zindex', 'label'])
Style.__doc__ += """: class to hold an element's styles
Used to generate legend entries, apply uniform style to groups of map elements
(See network_map.py for example.)
"""
def within_extent(x, y, extent):
    """Test x, y coordinates against (xmin, xmax, ymin, ymax) extent
    """
    xmin, xmax, ymin, ymax = extent
    return (xmin < x) and (x < xmax) and (ymin < y) and (y < ymax)

def set_ax_bg(ax, color='#ffffff'):
    """Set axis background color
        white=#ffffff
        blue=#c6e0ff
    """
    ax.background_patch.set_facecolor(color)

def get_projection(extent=(-74.04, -52.90, -20.29, -57.38), epsg=None):
    """Get map axes

    Default to Argentina extent // Lambert Conformal projection
    """
    if epsg is not None:
        ax_proj = ccrs.epsg(epsg)
    else:
        x0, x1, y0, y1 = extent
        cx = x0 + ((x1 - x0) / 2)
        cy = y0 + ((y1 - y0) / 2)
        ax_proj = ccrs.TransverseMercator(central_longitude=cx, central_latitude=cy)

    return ax_proj

def get_axes(ax,extent=(-74.04, -52.90, -20.29, -57.38), epsg=None):
    """Get map axes

    Default to Lambert Conformal projection
    """

    print(" * Setup axes")
    proj = ccrs.PlateCarree()
    ax.set_extent(extent, crs=proj)
    set_ax_bg(ax)
    return ax

def plot_basemap_labels(ax, data_path, include_regions=False, include_zorder=2):
    """Plot countries and regions background
    """
    proj = ccrs.PlateCarree()
    labels = [
        # ("Ghana", -1.1755, 6.9591),
        ("Togo", 1.0546, 8.7439),
        ("Burkina Faso", -1.2084, 11.2046),
        ("Ivory Coast", -3.1080, 8.2767),
    ]

    if include_regions:
        regions = geopandas.read_file(
            os.path.join(data_path, 'admin', 'GHA_admin1.gpkg')).to_crs(epsg=4326)
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
            size=20,
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
            horizontalalignment='center', verticalalignment='bottom', size=16)

def save_fig(output_filename):
    print(" * Save", os.path.basename(output_filename))
    plt.savefig(output_filename)

def plot_basemap(ax, data_path, ax_crs=3857, plot_regions=False):
    """Plot countries and regions background
    """
    states = geopandas.read_file(
        os.path.join(data_path, 'admin', 'GHA_admin0.gpkg')).to_crs(epsg=ax_crs)

    lakes = geopandas.read_file(
        os.path.join(data_path, 'nature', 'GHA_lakes.gpkg')).to_crs(epsg=ax_crs)

    states.plot(ax=ax, edgecolor='#ffffff', facecolor='#e4e4e3', zorder=1)

    if plot_regions:
        regions = geopandas.read_file(
            os.path.join(data_path, 'admin', 'GHA_admin1.gpkg')).to_crs(epsg=ax_crs)
        regions.plot(ax=ax, edgecolor='#00000000', facecolor='#dededc')
        regions.plot(ax=ax, edgecolor='#ffffff', facecolor='#00000000', zorder=2)

    lakes.plot(ax=ax, edgecolor='none', facecolor='#87cefa', zorder=1)

def plot_point_assets(ax,nodes,colors,size,marker,zorder,proj_lat_lon = ccrs.PlateCarree()):
    ax.scatter(
        list(nodes.geometry.x),
        list(nodes.geometry.y),
        transform=proj_lat_lon,
        facecolor=colors,
        s=size,
        marker=marker,
        zorder=zorder
    )
    return ax

def plot_line_assets(ax,edges,colors,size,zorder,proj_lat_lon = ccrs.PlateCarree()):
    ax.add_geometries(
        list(edges.geometry),
        crs=proj_lat_lon,
        linewidth=size,
        edgecolor=colors,
        facecolor='none',
        zorder=zorder
    )
    return ax

def plot_polygons(ax,df,df_column,color_map,divisor,legend_label,vmin=0,vmax=1,ax_crs=3857):
    # print (df)
    df = df.to_crs(epsg=ax_crs)
    df[df_column] = 1.0*df[df_column]/divisor
    return df.plot(ax=ax,
            column = df[df_column],
            cmap=color_map,
            vmin=0,
            vmax=200,
            legend=False,
            legend_kwds={'label':legend_label,'orientation':'horizontal'},
            zorder=5)

def add_colorbar(fig,ax,min_value,max_value,color_map,legend_label):
    # plt.title(plot_title, fontsize=9)
    # colorbar will be created by ...
    # fig = ax.get_figure()
    # add colorbar axes to the figure
    # here, need trial-and-error to get [l,b,w,h] right
    # l:left, b:bottom, w:width, h:height; in normalized unit (0-1)
    cbax = fig.add_axes([0.92, 0.02, 0.05, 0.90])   #[0.025, 0.025, 0.95, 0.95]
    cbax.set_title(legend_label,fontsize=20,fontweight='bold')

    sm = plt.cm.ScalarMappable(cmap=color_map, \
                    norm=plt.Normalize(vmin=min_value, vmax=max_value))
    # at this stage, 
    # 'cbax' is just a blank axes, with un needed labels on x and y axes

    # blank-out the array of the scalar mappable 'sm'
    sm._A = []
    # draw colorbar into 'cbax'
    cbar = fig.colorbar(sm, cax=cbax,orientation='vertical',ax=ax)
    cbar.ax.tick_params(labelsize=20)

    # plt.title(plot_title, fontsize=8)
    # save_fig(figure_path)

def legend_from_style_spec(ax, styles, fontsize = 10, loc='lower left'):
    """Plot legend
    """
    handles = [
        mpatches.Patch(color=style.color, label=style.label)
        for style in styles.values() if style.label is not None
    ]
    ax.legend(
        handles=handles,
        fontsize = fontsize,
        loc=loc
    )

def generate_weight_bins(weights, n_steps=9, width_step=0.01, interpolation='linear'):
    """Given a list of weight values, generate <n_steps> bins with a width
    value to use for plotting e.g. weighted network flow maps.
    """
    min_weight = min(weights)
    max_weight = max(weights)

    width_by_range = OrderedDict()

    if interpolation == 'linear':
        mins = np.linspace(min_weight, max_weight, n_steps)
    elif interpolation == 'log':
        mins = np.geomspace(min_weight, max_weight, n_steps)
    else:
        raise ValueError('Interpolation must be log or linear')
    maxs = list(mins)
    maxs.append(max_weight*10)
    maxs = maxs[1:]

    assert len(maxs) == len(mins)

    if interpolation == 'log':
        scale = np.geomspace(1, len(mins),len(mins))
    else:
        scale = np.linspace(1,len(mins),len(mins))


    for i, (min_, max_) in enumerate(zip(mins, maxs)):
        width_by_range[(min_, max_)] = scale[i] * width_step

    return width_by_range

def find_significant_digits(divisor,significance,width_by_range):
    divisor = divisor
    significance_ndigits = significance
    max_sig = []
    for (i, ((nmin, nmax), line_style)) in enumerate(width_by_range.items()):
        if round(nmin/divisor, significance_ndigits) < round(nmax/divisor, significance_ndigits):
            max_sig.append(significance_ndigits)
        elif round(nmin/divisor, significance_ndigits+1) < round(nmax/divisor, significance_ndigits+1):
            max_sig.append(significance_ndigits+1)
        elif round(nmin/divisor, significance_ndigits+2) < round(nmax/divisor, significance_ndigits+2):
            max_sig.append(significance_ndigits+2)
        else:
            max_sig.append(significance_ndigits+3)

    significance_ndigits = max(max_sig)
    return significance_ndigits

def create_figure_legend(divisor,significance,width_by_range,max_weight,legend_type,legend_colors,legend_weight,marker='o'):
    legend_handles = []
    significance_ndigits = find_significant_digits(divisor,significance,width_by_range)
    for (i, ((nmin, nmax), width)) in enumerate(width_by_range.items()):
        if abs(nmin - max_weight) < 1e-5:
            value_template = '>{:.' + str(significance_ndigits) + 'f}'
            label = value_template.format(
                round(max_weight/divisor, significance_ndigits))
        else:
            value_template = '{:.' + str(significance_ndigits) + \
                'f}-{:.' + str(significance_ndigits) + 'f}'
            label = value_template.format(
                round(nmin/divisor, significance_ndigits), round(nmax/divisor, significance_ndigits))
        if legend_type == 'marker':
            legend_handles.append(plt.plot([],[],
                                marker=marker, 
                                ms=width/legend_weight, 
                                ls="",
                                color=legend_colors[i],
                                label=label)[0])
        else:
            legend_handles.append(Line2D([0], [0], 
                            color=legend_colors[i], lw=width/legend_weight, label=label))

    return legend_handles

def line_map_plotting(ax,df,df_column,line_color,divisor,legend_label,value_label,plot_title=False,figure_path=False,significance=0):
    column = df_column

    weights = [
        getattr(record,column)
        for record in df.itertuples()
    ]
    max_weight = max(weights)
    width_by_range = generate_weight_bins(weights, width_step=0.02, n_steps=4)
    # print (width_by_range)
    line_geoms_by_category = {
        '1': [],
        '2': []
    }
    for record in df.itertuples():
        geom = record.geometry
        val = getattr(record,column)
        if val == 0:
            cat = '2'
        else:
            cat = '1'

        buffered_geom = None
        for (nmin, nmax), width in width_by_range.items():
            if nmin <= val and val < nmax:
                buffered_geom = geom.buffer(width)

        if buffered_geom is not None:
            line_geoms_by_category[cat].append(buffered_geom)
        else:
            print("Feature was outside range to plot", record.Index)

    styles = OrderedDict([
        ('1',  Style(color=line_color, zindex=9, label=value_label)),
        ('2', Style(color='#969696', zindex=7, label='No {}'.format(value_label)))
    ])

    for cat, geoms in line_geoms_by_category.items():
        cat_style = styles[cat]
        ax.add_geometries(
            geoms,
            crs=ccrs.PlateCarree(),
            linewidth=0,
            facecolor=cat_style.color,
            edgecolor='none',
            zorder=cat_style.zindex
        )

    legend_handles = create_figure_legend(divisor,
                        significance,
                        width_by_range,
                        max_weight,
                        'line',[line_color]*len(width_by_range),0.02)

    if plot_title:
        ax.set_title(plot_title, fontsize=9)
    print ('* Plotting ',plot_title)
    first_legend = ax.legend(handles=legend_handles,fontsize=9,title=legend_label,loc='lower left')
    ax.add_artist(first_legend)
    legend_from_style_spec(ax, styles,fontsize=8,loc='lower right')
    return ax

def point_map_plotting(ax,df,df_column,
                point_color,marker,divisor,
                legend_label,value_label,
                plot_title=False,figure_path=False,significance=0):
    column = df_column

    weights = [
        getattr(record,column)
        for record in df.itertuples()
    ]
    max_weight = max(weights)
    width_by_range = generate_weight_bins(weights, width_step=20, n_steps=4)
    line_geoms_by_category = {
        '1': [],
        '2': []
    }
    for record in df.itertuples():
        geom = record.geometry
        val = getattr(record,column)
        if val == 0:
            cat = '2'
        else:
            cat = '1'
        for (nmin, nmax), width in width_by_range.items():
            if val == 0:
                line_geoms_by_category[cat].append((geom,width/2))
                break
            elif nmin <= val and val < nmax:
                line_geoms_by_category[cat].append((geom,width))

    styles = OrderedDict([
        ('1',  Style(color=point_color, zindex=9, label=value_label)),
        ('2', Style(color='#969696', zindex=7, label='No {}'.format(value_label)))
    ])

    for cat, geoms in line_geoms_by_category.items():
        cat_style = styles[cat]
        for g in geoms:
            ax.scatter(
                g[0].x,
                g[0].y,
                transform=ccrs.PlateCarree(),
                facecolor=cat_style.color,
                s=g[1],
                marker=marker,
                zorder=cat_style.zindex
            )

    legend_handles = create_figure_legend(divisor,
                        significance,
                        width_by_range,
                        max_weight,
                        'marker',[point_color]*len(width_by_range),10,marker=marker)
    if plot_title:
        plt.title(plot_title, fontsize=9)
    first_legend = ax.legend(handles=legend_handles,fontsize=9,title=legend_label,loc='lower left')
    ax.add_artist(first_legend)
    print ('* Plotting ',plot_title)
    legend_from_style_spec(ax, styles,fontsize=8,loc='lower right')
    return ax

def line_map_plotting_colors_width(ax,df,df_column,
                        divisor,legend_label,value_label,
                        line_colors = ['#c6dbef','#6baed6','#2171b5','#08306b'],
                        no_value_color = '#969696',
                        line_steps = 4,
                        width_step = 0.02,
                        plot_title=False,
                        figure_path=False,
                        significance=0):
    column = df_column
    all_colors = [no_value_color] + line_colors
    line_geoms_by_category = {'{}'.format(j):[] for j in range(len(all_colors))}
    weights = [
        getattr(record,column)
        for record in df.itertuples()
    ]
    max_weight = max(weights)
    width_by_range = generate_weight_bins(weights, 
                                width_step=width_step, 
                                n_steps=line_steps)
    # print (width_by_range)
    min_width = 0.8
    for record in df.itertuples():
        geom = record.geometry
        val = getattr(record,column)
        buffered_geom = None
        for (i, ((nmin, nmax), width)) in enumerate(width_by_range.items()):
            if val == 0:
                buffered_geom = geom.buffer(width/2)
                cat = str(i)
                min_width = width/2
                break
            elif nmin <= val and val < nmax:
                buffered_geom = geom.buffer(width)
                cat = str(i+1)

        if buffered_geom is not None:
            line_geoms_by_category[cat].append(buffered_geom)
        else:
            print("Feature was outside range to plot", record.Index)

    style_noflood = [(str(0),  Style(color=no_value_color, zindex=7,label='No {}'.format(value_label)))]
    styles = OrderedDict(style_noflood + [
        (str(j+1),  Style(color=line_colors[j], zindex=8+j,label=None)) for j in range(len(line_colors))
    ])
    # print ()
    for cat, geoms in line_geoms_by_category.items():
        # print (cat,geoms)
        cat_style = styles[cat]
        ax.add_geometries(
            geoms,
            crs=ccrs.epsg(3857),
            linewidth=0,
            facecolor=cat_style.color,
            edgecolor='none',
            zorder=cat_style.zindex
        )

    legend_handles = create_figure_legend(divisor,
                        significance,
                        width_by_range,
                        max_weight,
                        'line',line_colors,width_step)
    if plot_title:
        ax.set_title(plot_title, fontsize=9)
    print ('* Plotting ',plot_title)
    first_legend = ax.legend(handles=legend_handles,fontsize=6,title=legend_label,loc='upper right')
    # print (styles)
    ax.add_artist(first_legend)
    legend_from_style_spec(ax, styles,fontsize=6,loc='lower right')
    return ax

def point_map_plotting_color_width(ax,df,df_column,
                marker,divisor,
                legend_label,value_label,
                point_colors = ['#c6dbef','#6baed6','#2171b5','#08306b'],
                no_value_color = '#969696',
                point_steps = 4,
                width_step = 20,
                plot_title=False,
                figure_path=False,
                significance=0):
    column = df_column

    all_colors = [no_value_color] + point_colors
    point_geoms_by_category = {'{}'.format(j):[] for j in range(len(all_colors))}
    weights = [
        getattr(record,column)
        for record in df.itertuples()
    ]
    max_weight = max(weights)
    width_by_range = generate_weight_bins(weights, width_step=width_step, n_steps=point_steps)

    for record in df.itertuples():
        geom = record.geometry
        val = getattr(record,column)
        for (i, ((nmin, nmax), width)) in enumerate(width_by_range.items()):
            if val == 0:
                point_geoms_by_category[str(i)].append((geom,width/2))
                min_width = width/2
                break
            elif nmin <= val and val < nmax:
                point_geoms_by_category[str(i+1)].append((geom,width))

    style_noflood = [(str(0),  Style(color=no_value_color, zindex=7,label='No {}'.format(value_label)))]
    styles = OrderedDict(style_noflood + [
        (str(j+1),  Style(color=point_colors[j], zindex=8+j,label=None)) for j in range(len(point_colors))
    ])

    for cat, geoms in point_geoms_by_category.items():
        cat_style = styles[cat]
        for g in geoms:
            ax.scatter(
                g[0].x,
                g[0].y,
                transform=ccrs.PlateCarree(),
                facecolor=cat_style.color,
                s=g[1],
                marker=marker,
                zorder=cat_style.zindex
            )

    legend_handles = create_figure_legend(divisor,
                        significance,
                        width_by_range,
                        max_weight,
                        'marker',point_colors,10,marker=marker)
    if plot_title:
        plt.title(plot_title, fontsize=9)
    first_legend = ax.legend(handles=legend_handles,fontsize=9,title=legend_label,loc='lower left')
    ax.add_artist(first_legend)
    print ('* Plotting ',plot_title)
    legend_from_style_spec(ax, styles,fontsize=8,loc='lower right')
    return ax