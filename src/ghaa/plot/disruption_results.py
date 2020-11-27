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

def plot_scatter_and_hist(x,y):
    # Set up the axes with gridspec
    fig = plt.figure(figsize=(8, 8))
    grid = plt.GridSpec(5, 5, hspace=0.2, wspace=0.2)
    main_ax = fig.add_subplot(grid[:-1, 1:])
    y_hist = fig.add_subplot(grid[:-1, 0], xticklabels=[], sharey=main_ax)
    x_hist = fig.add_subplot(grid[-1, 1:], yticklabels=[], sharex=main_ax)

    # scatter points on the main axes
    main_ax.plot(x, y, 'ok', markersize=3, alpha=0.2)

    # histogram on the attached axes
    x_hist.hist(x, 40, histtype='stepfilled',
                orientation='vertical', color='gray')
    x_hist.invert_yaxis()

    y_hist.hist(y, 40, histtype='stepfilled',
                orientation='horizontal', color='gray')
    y_hist.invert_xaxis()

    plt.show()

def bar_plots(ax,pop_counts,walking_color,access_color,no_access_color,legend_handles,x_label,y_label,plot_title):
    max_dist = pop_counts[pop_counts['access'] == 2].length_km.max()
    pop_no_access = pop_counts[pop_counts['access'] == 0].population.values[0]
    pop_nearby = pop_counts[pop_counts['access'] == 1].population.values[0]

    access = pop_counts[pop_counts.access == 2]
    distance_bins = np.arange(0,max_dist,100.0)
    if int(max_dist/100.0) < 1:
        distance_bins = np.arange(0,max_dist,10.0)
    else:
        distance_bins = np.array(list([0,10,20,50]) + list(np.arange(100,max_dist,100.0)))

    pop_bins = []
    dist_labels = []
    for d in range(len(distance_bins)-1):
        pop_bins.append(access[(access.length_km > distance_bins[d]) & (access.length_km <= distance_bins[d+1])].population.sum())
        dist_labels.append('{}-{}'.format(int(distance_bins[d]),int(distance_bins[d+1])))

    pop_bins = [pop_nearby] + pop_bins + [pop_no_access]
    if int(max_dist/100.0) < 1:
        distance_bins = list(distance_bins) + [distance_bins[-1]+10]
    else:
        distance_bins = list(distance_bins) + [distance_bins[-1]+100]
    
    dist_labels = ['0'] + dist_labels + ['No access']
    colors = [walking_color] + [access_color]*(len(dist_labels)-2) + [no_access_color]

    pop_perc = 100.0*np.array(pop_bins)/sum(pop_bins)
    x = np.arange(0,len(distance_bins),1)
    ax.bar(x,pop_perc,width=1,tick_label=dist_labels,color=colors)
    for i in range(len(pop_bins)):
        ax.text(x = x[i]-0.20 , y = pop_perc[i]+4, s = "{:,}".format(int(pop_bins[i])), size = 6)
        ax.text(x = x[i]-0.15 , y = pop_perc[i]+1, s = "({:,.2f}%)".format(pop_perc[i]), size = 6)
    
    # ax.tick_params(axis='x', rotation=45)
    ax.set_ylim(0,100)
    plt.yticks(np.arange(0,110,10),np.arange(0,110,10))
    ax.legend(handles=legend_handles,loc='upper right',fontsize=8)
    plt.xlabel(x_label, fontweight='bold')
    plt.ylabel(y_label, fontweight='bold')
    plt.title(plot_title)


def main():
    crs = {'init': 'epsg:4326'} # Set the projection system
    data_path = os.path.join(BASE_PATH,'data')
    incoming_path = os.path.join(BASE_PATH,'incoming')
    result_path = os.path.join(BASE_PATH,'results')
    figures_path = os.path.join(BASE_PATH,'figures')

    population_layers = os.path.join(incoming_path,
                    'population',
                    'Population Density& Demographics',
                    'ID 23_Population_Density_Demographics - fb AI')
    
    proximity_results = os.path.join(result_path, 'proximity_results')
    disruption_results = os.path.join(result_path, 'disruption_results')
    edges = gpd.read_file(os.path.join(data_path,'proximity_datasets','road_edges.shp')).to_crs(epsg=3857)
    flood_scenarios = ['current_3-4','current_5-6','future_3-4','future_5-6']
    flood_scenarios_label = ['(a) Current Medium','(b) Current High', '(c) Future Medium', '(d) Future High']

    access_color = '#3182bd'
    walking_color = '#31a354'
    no_access_color = '#636363'
    legend_handles = []
    colors = [walking_color,access_color,no_access_color]
    color_labels = ['Walking distance','Road access','No access']
    for c in range(len(colors)):
        legend_handles.append(mpatches.Patch(color=colors[c], label=color_labels[c]))
    
    # Bar plots of accessibility
    file = 'population_gha_2019-07-01_proximity.csv'
    pop_gdf = pd.read_csv(os.path.join(proximity_results,file))
    print (pop_gdf)
    print (pop_gdf.population.sum())

    pop_counts = pop_gdf.groupby(['edge_path','length_km','time_hr','access'])['population'].sum().reset_index()
    fig, ax = plt.subplots(figsize=(8, 4))
    x_label = 'Distance (km)'
    y_label = 'Population (%)'
    plot_title = 'Total populationn - Distance to nearest health center'
    bar_plots(ax,pop_counts,walking_color,access_color,no_access_color,legend_handles,x_label,y_label,plot_title)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_path,'GHA_all_proximity_bar_percentage.png'), dpi=500)
    plt.close()
    
    pop_counts['edge_path'] = pop_counts.progress_apply(lambda x: ast.literal_eval(x.edge_path),axis=1)
    edge_path_index = defaultdict(float)
    for row in pop_counts.itertuples():
        if row.edge_path:
            for edge in row.edge_path:
                edge_path_index[edge] += row.population
    print ('Total edge population:',sum(edge_path_index.values()))
    node_counts = pop_gdf[pop_gdf['access']==1].groupby(['nearest_pop_r_node'])['population'].sum().reset_index()
    print (node_counts.sort_values(by=['population'],ascending=False))
    print ('Total node population',node_counts.population.sum())

    for nodes in node_counts.itertuples():
        select_edges = list(set(edges[(edges.from_node == nodes.nearest_pop_r_node) | (edges.to_node == nodes.nearest_pop_r_node)].edge_id.values.tolist()))
        for edge in select_edges:
            edge_path_index[edge] += 1.0*nodes.population/len(select_edges)

    edge_df = pd.DataFrame([(k,v) for k,v in edge_path_index.items()],columns=['edge_id','population'])
    print (edge_df.sort_values(by=['population'],ascending=False))
    print ('Total population:',edge_df.population.sum())
    edges = pd.merge(edges[['edge_id','geometry']],edge_df,how='left',on=['edge_id']).fillna(0)
    edges = gpd.GeoDataFrame(pd.merge(edge_df,edges[['edge_id','geometry']],how='left',on=['edge_id']).fillna(0),
                    crs={'init': 'epsg:3857'},geometry='geometry')
    print (edges.crs)
    print (edges.sort_values(by=['population'],ascending=False))
    edges.sort_values(by=['population'],
                    ascending=False).to_file(os.path.join(proximity_results,'road_flows.shp'))
    road_colors = ['#fdd0a2','#f16913','#cb181d','#a63603','#67000d']
    ax = gha_basemap.get_axes()
    gha_basemap.plot_basemap(ax, data_path, plot_regions=True)
    gha_basemap.plot_basemap_labels(ax, data_path, include_regions=True,include_zorder=12)
    gha_basemap.scale_bar(ax)
    ax = gha_map.line_map_plotting_colors_width(ax,edges,'population',
                        1.0,
                        'Population',
                        'Population',
                        line_colors = road_colors,
                        line_steps = 5,
                        width_step = 1000.0,
                        plot_title='Total population - Road usage for access to health services'
                        )
    gha_map.save_fig(os.path.join(os.path.join(figures_path,'GHA_roads_map_accessibility.png')))
    
    x_label = 'Distance (km)'
    y_label = 'Population (%)'
    for sc in range(len(flood_scenarios)):
        file = 'road_edges_flood_{}_population_gha_2019-07-01_proximity.csv'.format(flood_scenarios[sc])
        pop_gdf = pd.read_csv(os.path.join(disruption_results,file))
        pop_counts = pop_gdf.groupby(['edge_path','length_km','time_hr','access'])['population'].sum().reset_index()
        fig, ax = plt.subplots(figsize=(8, 4))
        plot_title = flood_scenarios_label[sc]
        bar_plots(ax,pop_counts,walking_color,access_color,no_access_color,legend_handles,x_label,y_label,plot_title)

        # plt.suptitle('Total populationn - Distance to nearest health center after flooding', fontsize=16,fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(figures_path,
                    'GHA_all_proximity_bar_percentage_{}_flooding.png'.format(flood_scenarios[sc])), 
                    dpi=500)
        plt.close()

if __name__ == '__main__':
    main()
