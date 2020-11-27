"""Generate darthmouth events
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

    road_layer = os.path.join(data_path,'infrastructure','GHA_OSM_roads.shp')
    health_layer = os.path.join(data_path,'infrastructure','GHA_healthfacility.shp')
    population_layers = os.path.join(incoming_path,
                    'population',
                    'Population Density& Demographics',
                    'ID 23_Population_Density_Demographics - fb AI')

    clean_data_dir = os.path.join(data_path, 'proximity_datasets')
    if os.path.exists(clean_data_dir) == False:
        os.mkdir(clean_data_dir)
    
    proximity_results = os.path.join(result_path, 'proximity_results')
    if os.path.exists(proximity_results) == False:
        os.mkdir(proximity_results)

    save_results = os.path.join(result_path, 'disruption_results')
    if os.path.exists(save_results) == False:
        os.mkdir(save_results)

    flood_exposures = os.path.join(result_path, 'exposure')
    # flood_file = 'road_edges_flood_current_3-4.csv'
    edge_id = 'edge_id'

    # get nearest node in network for all health centers
    edges_in = gpd.read_file(os.path.join(clean_data_dir,'road_edges.shp'))
    nodes_in = gpd.read_file(os.path.join(clean_data_dir,'road_nodes.shp'))
    print (edges_in)

    for froot, fdirs, ffiles in os.walk(flood_exposures):
        for ffile in ffiles:
            if ffile.startswith('road_edges') and ffile.endswith('csv'):
                flood_edges = pd.read_csv(os.path.join(froot,ffile))
                disrupted_edges = list(set(flood_edges[edge_id].values.tolist()))
                edges = edges_in.copy()
                edges = edges[~edges[edge_id].isin(disrupted_edges)]
                # nodes_in = [x['name'] for x in edges.vs]
                G = ig.Graph.TupleList(edges.itertuples(index=False), edge_attrs=list(edges.columns)[2:])
                nodes = [x['name'] for x in G.vs]
                # process all the population layers
                for root, dirs, files in os.walk(proximity_results):
                    for file in files:
                        if not file.startswith('._'):
                            if file.endswith("_proximity.csv"):
                                print ('* Starting file',file)
                                pop_gdf = pd.read_csv(os.path.join(proximity_results,file))
                                pop_gdf.rename(columns={'time_hr.1':'gcost'},inplace=True)
                                print ('whole population')
                                print (pop_gdf)
                                no_access = pop_gdf[pop_gdf.access == 0]
                                print ('no access')
                                print (no_access)
                                pop_gdf = pop_gdf[pop_gdf.access != 0]
                                # pop_gdf = pop_gdf[['pop_id','nearest_pop_r_node','nearest_hc_r_node']]
                                with_access = pop_gdf[pop_gdf['nearest_pop_r_node'].isin(nodes) & pop_gdf['nearest_hc_r_node'].isin(nodes)]
                                cutoff_access = pop_gdf[~pop_gdf['pop_id'].isin(with_access['pop_id'].values.tolist())]
                                # print (cutoff_access)
                                cutoff_access['edge_path'] = '[]'
                                cutoff_access['length_km'] = 0
                                cutoff_access['time_hr'] = 0
                                cutoff_access['gcost'] = 0
                                cutoff_access['access'] = 0
                                print ('cutoff access')
                                print (cutoff_access)
                                del pop_gdf
                                with_access = with_access[['pop_id','population',
                                                    'x','y','nearest_pop_r_node',
                                                    'nearest_hc_r_node','nearest_hc']]
                                paths = spnf.network_od_paths_assembly(with_access, G,'edge_id',
                                                        'nearest_hc_r_node','nearest_pop_r_node',
                                                        'length_km','time_hr','time_hr')
                                # print (paths)
                                print ('* Done with mapping paths')
                                with_access = pd.merge(with_access,paths,how='left',on=['nearest_hc_r_node','nearest_pop_r_node'])
                                del paths
                                with_access = with_access.drop_duplicates(subset=['pop_id'], keep='first')

                                if 'access' not in with_access.columns.values.tolist():
                                    with_access['access'] = with_access.progress_apply(lambda x:kind_of_access(x),axis=1)
                                
                                print ('with access')
                                print (with_access)

                                pop_gdf = pd.concat([no_access, cutoff_access, with_access],axis=0,sort='False', ignore_index=True)
                                pop_gdf = pop_gdf.sort_values(by=['length_km'],ascending=False)
                                pop_gdf.to_csv(os.path.join(save_results,file),index=False)
                                print ('* Done with file',file)
                                del pop_gdf
if __name__ == '__main__':
    main()
