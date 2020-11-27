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

def assign_road_speeds(x):
    if x in ('motorway','motorway_link','trunk','trunk_link'):
        return 100
    elif x in ('primary','primary_link'):
        return 90
    elif x in ('secondary','secondary_link'):
        return 80
    elif x in ('tertiary','tertiary_link'):
        return 50
    elif x in ('residential','track','unclassified'):
        return 30
    else:
        return 10    

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
    population_layers = os.path.join(incoming_path,
                    'population',
                    'Population Density& Demographics',
                    'ID 23_Population_Density_Demographics - fb AI',
                    'pop_test')

    clean_data_dir = os.path.join(data_path, 'proximity_datasets')
    if os.path.exists(clean_data_dir) == False:
        os.mkdir(clean_data_dir)
    
    save_results = os.path.join(result_path, 'proximity_results')
    if os.path.exists(save_results) == False:
        os.mkdir(save_results)

    epsg_utm_20s = 32630
    network = spnf.create_network_from_edges(road_layer,'road',epsg_utm_20s,distance=20)
    # project back to WGS84 lat/lon
    network.set_crs(epsg=epsg_utm_20s)
    epsg_lat_lon = 4326
    network.to_crs(epsg=epsg_lat_lon)
    # network.to_crs(epsg=epsg_lat_lon)
    edges = network.edges
    nodes = network.nodes
    edges['length_km'] = edges.progress_apply(lambda x: spnf.line_length(x.geometry), axis=1)
    edges['speed_kph'] = edges.progress_apply(lambda x: assign_road_speeds(x.type),axis=1)
    edges['time_hr'] = 1.0*edges['length_km']/edges['speed_kph']
    print (edges)
    edge_cols = [c for c in edges.columns.values.tolist() if c not in ('from_node','to_node','edge_id')]
    edges = edges[['from_node','to_node','edge_id'] + edge_cols]
    # G = ig.Graph.TupleList(edges.itertuples(index=False), edge_attrs=list(edges.columns)[2:]).clusters().giant()
    # edge_names = G.es['edge_id']
    # node_names = np.asarray([x['name'] for x in G.vs])
    # edges = gpd.GeoDataFrame(edges[edges.edge_id.isin(edge_names)],crs=crs,geometry='geometry')
    # nodes = gpd.GeoDataFrame(nodes[nodes.node_id.isin(node_names)],crs=crs,geometry='geometry')

    G = ig.Graph.TupleList(edges.itertuples(index=False), edge_attrs=list(edges.columns)[2:])
    edges = gpd.GeoDataFrame(edges,crs=crs,geometry='geometry')
    nodes = gpd.GeoDataFrame(nodes,crs=crs,geometry='geometry')

    edges.to_file(os.path.join(clean_data_dir,'road_edges_v2.shp'))
    nodes.to_file(os.path.join(clean_data_dir,'road_nodes_v2.shp'))
    print (edges)
    del edges
    # get nearest node in network for all health centers
    edges = gpd.read_file(os.path.join(clean_data_dir,'road_edges_v2.shp'))
    print (edges)
    G = ig.Graph.TupleList(edges.itertuples(index=False), edge_attrs=list(edges.columns)[2:])
    nodes = gpd.read_file(os.path.join(clean_data_dir,'road_nodes_v2.shp'))
    health_centers = gpd.read_file(health_layer)
    health_centers = gpd.GeoDataFrame(health_centers[~(health_centers.geometry.is_empty | health_centers.geometry.isna())],
                                crs=crs,geometry='geometry')
    health_centers = health_centers.reset_index()
    health_centers.to_file(os.path.join(clean_data_dir,'health_centers.shp'))
    sindex_nodes = nodes.sindex
    sindex_health_centers = health_centers.sindex
    node_id = 'node_id'
    health_id = 'ID'
    health_centers['nearest_hc_r_node'] = health_centers.progress_apply(
            lambda x: spnf.get_nearest_node(x.geometry, sindex_nodes, nodes, node_id),axis=1)
    print (health_centers)

    tiff_file_process = False
    csv_file_process = True
    # process all the population layers
    if tiff_file_process is True:
        for root, dirs, files in os.walk(population_layers):
            for file in files:
                if file.endswith(".tif") or file.endswith(".tiff"):
                    pop_gdf = spnf.convert_tif_to_csv_gdf(root,file,'pop_id','population')
                    print (pop_gdf)
                    # get nearest node in network for all start and end points
                    pop_gdf['nearest_pop_r_node'] = pop_gdf.progress_apply(
                        lambda x: spnf.get_nearest_node(x.geometry, sindex_nodes, nodes, node_id),axis=1)

                    pop_gdf['nearest_hc'] = pop_gdf.progress_apply(
                        lambda x: spnf.get_nearest_node(x.geometry, sindex_health_centers, health_centers, health_id),axis=1)

                    pop_gdf = pd.merge(pop_gdf,health_centers[[health_id,'nearest_hc_r_node']],
                                            how='left',left_on=['nearest_hc'],right_on=[health_id])
                    pop_gdf.drop(health_id,axis=1,inplace=True)
                    pop_gdf.to_csv(os.path.join(save_results,'{}_proximity_0.csv'.format(file.split('.tif')[0])))
                    paths = spnf.network_od_paths_assembly(pop_gdf, G,'edge_id',
                                            'nearest_hc_r_node','nearest_pop_r_node',
                                            'length_km','time_hr','time_hr')
                    # print (paths)
                    print ('* Done with mappign paths')
                    pop_gdf = pd.merge(pop_gdf,paths,how='left',on=['nearest_hc_r_node','nearest_pop_r_node'])
                    del paths
                    pop_gdf.drop('geometry',axis=1,inplace=True)
                    pop_gdf = pop_gdf.drop_duplicates(subset=['pop_id'], keep='first')
                    pop_gdf = pop_gdf.sort_values(by=['length_km'],ascending=False)
                    if 'access' not in pop_gdf.columns.values.tolist():
                        pop_gdf['access'] = pop_gdf.progress_apply(lambda x:kind_of_access(x),axis=1)
                    pop_gdf.to_csv(os.path.join(save_results,'{}_proximity.csv'.format(file.split('.tif')[0])))
                    del pop_gdf
                    print ('* Done with file',file)

    # process all the population layers
    if csv_file_process is True:
        for root, dirs, files in os.walk(save_results):
            for file in files:
                if not file.startswith('._'):
                    if file.endswith("_proximity.csv"):
                        print ('* Starting file',file)
                        pop_gdf = pd.read_csv(os.path.join(save_results,file))
                        pop_gdf = pop_gdf[['pop_id','population','x','y']]
                        geometry = [Point(xy) for xy in zip(pop_gdf.x, pop_gdf.y)]
                        pop_gdf = gpd.GeoDataFrame(pop_gdf, crs=crs, geometry=geometry)
                        del geometry
                        # get nearest node in network for all start and end points
                        pop_gdf['nearest_pop_r_node'] = pop_gdf.progress_apply(
                            lambda x: spnf.get_nearest_node(x.geometry, sindex_nodes, nodes, node_id),axis=1)

                        pop_gdf['nearest_hc'] = pop_gdf.progress_apply(
                            lambda x: spnf.get_nearest_node(x.geometry, sindex_health_centers, health_centers, health_id),axis=1)

                        pop_gdf = pd.merge(pop_gdf,health_centers[[health_id,'nearest_hc_r_node']],
                                                how='left',left_on=['nearest_hc'],right_on=[health_id])
                        pop_gdf.drop(health_id,axis=1,inplace=True)
                        pop_gdf.to_csv(os.path.join(save_results,'{}_proximity_0.csv'.format(file.split('.csv')[0])))
                        paths = spnf.network_od_paths_assembly(pop_gdf, G,'edge_id',
                                                'nearest_hc_r_node','nearest_pop_r_node',
                                                'length_km','time_hr','time_hr')
                        # print (paths)
                        print ('* Done with mapping paths')
                        pop_gdf = pd.merge(pop_gdf,paths,how='left',on=['nearest_hc_r_node','nearest_pop_r_node'])
                        del paths
                        pop_gdf.drop('geometry',axis=1,inplace=True)

                        pop_gdf = pop_gdf.drop_duplicates(subset=['pop_id'], keep='first')

                        pop_gdf = pop_gdf.sort_values(by=['length_km'],ascending=False)
                        if 'access' not in pop_gdf.columns.values.tolist():
                            pop_gdf['access'] = pop_gdf.progress_apply(lambda x:kind_of_access(x),axis=1)
                            pop_gdf.to_csv(os.path.join(save_results,file),index=False)
                        print ('* Done with file',file)
                    del pop_gdf
if __name__ == '__main__':
    main()
