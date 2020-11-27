"""Road damage estimations in Ghana
"""
import os
import sys
import configparser
import pandas as pd
import geopandas as gpd
import subprocess
import numpy as np
from shapely.geometry import Point
import igraph as ig
import ghaa.config as config
import ghaa.analysis.spatial_and_network_functions as spnf
from tqdm import tqdm

BASE_PATH = config.load_config()['base_path']
tqdm.pandas()

def assign_road_condition_and_lanes(x):
    if x.type:
        if x.type in ('motorway','motorway_link','trunk','trunk_link','primary','primary_link'):
            return 'paved', 2
        else:
            return 'unpaved',1
    else:
        return 'unpaved',1

def assign_road_costs(x):
    if x.condition == 'paved':
        return x.lanes*500000.0
    else:
        return x.lanes*11000.0

def kind_of_access(x):
    if x.nearest_hc_r_node == x.nearest_pop_r_node:
        return 1
    elif x.length_km > 0:
        return 2
    else:
        return 0 

def main():
    crs = {'init': 'epsg:4326'} # Set the projection system
    data_path = os.path.join(BASE_PATH,'data')
    incoming_path = os.path.join(BASE_PATH,'incoming')
    result_path = os.path.join(BASE_PATH,'results')

    clean_data_dir = os.path.join(data_path, 'proximity_datasets')
    proximity_results = os.path.join(result_path, 'proximity_results')
    
    disruption_results = os.path.join(result_path, 'disruption_results')
    if os.path.exists(disruption_results) == False:
        os.mkdir(disruption_results)

    damage_stats = os.path.join(result_path, 'damage_stats')
    if os.path.exists(damage_stats) == False:
        os.mkdir(damage_stats)

    flood_exposures = os.path.join(result_path, 'exposure')
    edge_id = 'edge_id'

    # get nearest node in network for all health centers
    edges_in = gpd.read_file(os.path.join(clean_data_dir,'road_edges.gpkg'))
    edges_in['condition_lanes'] = edges_in.progress_apply(lambda x:assign_road_condition_and_lanes(x),axis=1)
    edges_in[['condition','lanes']] = edges_in['condition_lanes'].apply(pd.Series)
    edges_in.drop('condition_lanes',axis=1,inplace=True)
    edges_in['costs_perlanekm'] = edges_in.progress_apply(lambda x:assign_road_costs(x),axis=1)
    print (edges_in)
    
    edges_in.groupby(['type',
    				'condition'])['length_km'].sum().reset_index().to_csv(os.path.join(damage_stats,
    															'road_type_condition_length.csv'),
    															index=False)
    edges_in.groupby(['condition'])['length_km'].sum().reset_index().to_csv(os.path.join(damage_stats,
    															'road_condition_length.csv'),
    															index=False)
    admin_shape = gpd.read_file(os.path.join(data_path, 'admin', 'GHA_admin2.gpkg'))
    admin_roads = pd.read_csv(os.path.join(clean_data_dir,'road_edges_GHA_admin2.csv'))
    admin_roads['length'] = 0.001*admin_roads['length']
    admin_roads = admin_roads.groupby(['ID'])['length'].sum().reset_index()
    admin_roads.rename(columns={'length':'total_length'},inplace=True)

    flood_scenarios = ['current_3-4','current_5-6','future_3-4','future_5-6']
    for froot, fdirs, ffiles in os.walk(flood_exposures):
        for ffile in ffiles:
            if ffile.startswith('road_edges') and ffile.endswith('admin2.csv'):
            	flood_sc = [f for f in flood_scenarios if f in ffile][0]
                flood_edges = pd.read_csv(os.path.join(froot,ffile))
                flood_edges['length'] = 0.001*flood_edges['length']
                flood_edges = pd.merge(flood_edges,edges_in[[edge_id,'lanes','costs_perlanekm']],how='left',on=[edge_id])
                flood_edges['damage_cost'] = flood_edges['length']*flood_edges['lanes']*flood_edges['costs_perlanekm']
                flood_edges = flood_edges.groupby(['ID'])['length','damage_cost'].sum().reset_index()
                flood_edges.rename(columns={'length':'{}_flooded_length'.format(flood_sc),
                				'damage_cost':'{}_damage_cost'.format(flood_sc)},inplace=True)
                admin_roads = pd.merge(admin_roads,flood_edges,how='left',on=['ID'])
                admin_roads['{}_flood_percent'.format(flood_sc)] = 100.0*admin_roads['{}_flooded_length'.format(flood_sc)]/admin_roads['total_length']
                print ('* Done with file',ffile)

    column_order = ['total_length']
    nopercent_column_order = ['total_length']
    for sc in flood_sc:
    	column_order += ['{}_flooded_length'.format(sc),'{}_flooded_percent'.format(sc),'{}_damage_cost'.format(sc)]
    	nopercent_column_order += ['{}_flooded_length'.format(sc),'{}_damage_cost'.format(sc)]

    admin_roads = pd.merge(admin_roads,admin_shape[['ID','ADMIN_1_NA','ADMIN_2_NA']],how='left',on=['ID'])
    admin_roads[['ADMIN_2_NA'] + column_order].to_csv(os.path.join(damage_stats,
    								'road_flood_statistics_admin2.csv'),
    								index=False)
    admin_roads = admin_roads.groupby(['ADMIN_1_NA'])[nopercent_column_order].sum().reset_index()
    for sc in flood_sc:
    	admin_roads['{}_flooded_percent'.format(sc)] = 100.0*admin_roads['{}_flooded_length'.format(flood_sc)]/admin_roads['total_length']
    admin_roads[['ADMIN_1_NA'] + column_order].to_csv(os.path.join(damage_stats,
    								'road_flood_statistics_admin1.csv'),
    								index=False)
    
if __name__ == '__main__':
    main()
