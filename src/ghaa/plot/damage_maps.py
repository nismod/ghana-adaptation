"""Generate darthmouth events
"""
import os
import sys
import configparser
import pandas as pd
import geopandas as gpd
import subprocess
import numpy as np
import igraph as ig
from shapely.geometry import Point
import matplotlib.pyplot as plt
from tqdm import tqdm
from collections import defaultdict
import ast
import matplotlib as mpl
import rasterio
import matplotlib.patches as mpatches
from matplotlib.ticker import (MaxNLocator,LinearLocator, MultipleLocator)
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from matplotlib import cm

import ghaa.config as config
import ghaa.plot.map as gha_basemap
import ghaa.plot.map_plotting as gha_map

mpl.style.use('ggplot')
mpl.rcParams['font.size'] = 10.
mpl.rcParams['font.family'] = 'tahoma'
mpl.rcParams['axes.labelsize'] = 10.
mpl.rcParams['xtick.labelsize'] = 9.
mpl.rcParams['ytick.labelsize'] = 9.

BASE_PATH = config.load_config()['base_path']
tqdm.pandas()

def main():
    crs = {'init': 'epsg:4326'} # Set the projection system
    data_path = os.path.join(BASE_PATH,'data')
    incoming_path = os.path.join(BASE_PATH,'incoming')
    result_path = os.path.join(BASE_PATH,'results')
    figures_path = os.path.join(BASE_PATH,'figures')

    admin_layer = os.path.join(data_path,'admin','GHA_admin2.gpkg')
    admin_stats = os.path.join(result_path,'damage_stats','road_flood_statistics_admin2.csv')
    
    admin_map = gpd.read_file(admin_layer)
    print (admin_map)
    admin_stats = pd.read_csv(admin_stats)
    print (admin_stats)
    
    flood_scenarios = ['current_3-4','current_5-6','future_3-4','future_5-6']
    flood_scenarios_label = ['(a) Current Medium','(b) Current High', '(c) Future Medium', '(d) Future High']
    colormap = 'Blues'
    result_dictionary = [
    					{
    					'variable':'damage_cost',
    					'plotlabel':'Damages (US$ million)',
    					'divisor':1e6,
    					'plotname':'damage_losses_admin2.png'
    					},
    					{
    					'variable':'flooded_length',
    					'plotlabel':'Flooded roads (kms)',
    					'divisor':1.0,
    					'plotname':'flooded_kilometers_admin2.png'
    					},
    					{
    					'variable':'flooded_percent',
    					'plotlabel':'Flooded roads (%)',
    					'divisor':1.0,
    					'plotname':'flooded_percent_admin2.png'
    					},
    					]
    for result in result_dictionary:
	    variable = result['variable']
	    plotlabel = result['plotlabel']
	    divisor = result['divisor']
	    plotname = result['plotname']
	    ax_proj = gha_map.get_projection(epsg=3857)
	    fig, ax_plots = plt.subplots(2,2,
	                    subplot_kw={'projection': ax_proj},
	                    figsize=(30,30),
	                    dpi=500)
	    ax_plots = ax_plots.flatten()
	    min_damage = 1e10
	    max_damage = 0
	    ax_vals = []
	    for sc in range(len(flood_scenarios)):
	        admin_values = gpd.GeoDataFrame(pd.merge(admin_stats[['ADMIN_2_NAME','{}_{}'.format(flood_scenarios[sc],variable)]],
	                        admin_map[['ADMIN_2_NAME','geometry']],
	                        how='left',on=['ADMIN_2_NAME']),geometry='geometry',crs=crs)

	        if min_damage > admin_values['{}_{}'.format(flood_scenarios[sc],variable)].min():
	            min_damage = admin_values['{}_{}'.format(flood_scenarios[sc],variable)].min()
	        if max_damage < admin_values['{}_{}'.format(flood_scenarios[sc],variable)].max():
	            max_damage = admin_values['{}_{}'.format(flood_scenarios[sc],variable)].max()
	        ax_vals.append(admin_values)

	    for sc in range(len(flood_scenarios)):
	        gha_map.plot_basemap(ax_plots[sc], data_path, plot_regions=True)
	        gha_map.plot_basemap_labels(ax_plots[sc], data_path, include_regions=True,include_zorder=12)
	        gha_map.scale_bar(ax_plots[sc])
	        gha_map.plot_polygons(ax_plots[sc],ax_vals[sc],
	                '{}_{}'.format(flood_scenarios[sc],variable),
	                colormap,divisor,plotlabel,vmin=1.0*min_damage/1e6,vmax=1.0*max_damage/1e6)
	        ax_plots[sc].set_title(flood_scenarios_label[sc],fontsize=24, fontweight='bold')

	    gha_map.add_colorbar(fig,ax_plots[-1],
	                1.0*min_damage/divisor,
	                1.0*max_damage/divisor,
	                colormap,plotlabel)
	    # fig.colorbar(im, ax=ax_plots.tolist())
	    plt.subplots_adjust(hspace=0)
	    plt.tight_layout()
	    gha_map.save_fig(os.path.join(figures_path,plotname))
	    plt.close()

if __name__ == '__main__':
    main()
