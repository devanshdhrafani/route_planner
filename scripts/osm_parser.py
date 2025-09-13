import json
import math
import geopandas as gpd
from pyrosm import OSM
import argparse

def calculate_distance(line_geometry):
    """
    Calculates the total length of a LineString geometry in meters using the Haversine formula
    for more accurate distance calculation over geographical coordinates.
    """
    if line_geometry is None or line_geometry.is_empty:
        return 0.0

    # Earth radius in meters
    R = 6371000  

    total_distance = 0.0
    coords = list(line_geometry.coords)

    for i in range(len(coords) - 1):
        lon1, lat1 = coords[i]
        lon2, lat2 = coords[i+1]
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        total_distance += distance
        
    return total_distance

def parse_pbf_for_routing(pbf_path, output_nodes_file='nodes.json', output_edges_file='edges.json'):
    """
    Parses an OSM PBF file to extract a drivable road network, including nodes and edges,
    and saves them to JSON files suitable for a C++ route planner.

    Args:
        pbf_path (str): The file path to the .osm.pbf file.
        output_nodes_file (str): Filename for the output nodes JSON.
        output_edges_file (str): Filename for the output edges JSON.
    """
    print(f"Initializing OSM parser for {pbf_path}...")
    osm = OSM(pbf_path)

    print("Extracting driving network (nodes and edges)...")
    # This extracts the graph with intersections (nodes) and road segments (edges)
    nodes_gdf, edges_gdf = osm.get_network(network_type="driving", nodes=True)

    if nodes_gdf.empty or edges_gdf.empty:
        print("Could not find a drivable network in the provided PBF file.")
        return

    print("Processing nodes...")
    # Convert nodes GeoDataFrame to a dictionary for easy lookup
    nodes_data = {}
    for node_id, row in nodes_gdf.set_index('id').iterrows():
        nodes_data[node_id] = {
            'lon': row['lon'],
            'lat': row['lat']
        }

    print("Processing edges...")
    # Process edges to extract required information
    edges_data = []
    for _, edge in edges_gdf.iterrows():
        # Calculate distance from geometry
        distance_meters = calculate_distance(edge['geometry'])

        edges_data.append({
            'u': edge['u'],              # Start node ID
            'v': edge['v'],              # End node ID
            'distance': distance_meters, # Road length in meters
            'maxspeed': edge.get('maxspeed', None), # Speed limit, if available
            'highway': edge.get('highway', None),   # Type of road (e.g., 'motorway', 'residential')
            'oneway': edge.get('oneway', None),     # Oneway status, if available
            'name': edge.get('name', None)          # Street name, if available
        })

    print(f"Saving nodes to {output_nodes_file}...")
    with open(output_nodes_file, 'w') as f:
        json.dump(nodes_data, f, indent=2)

    print(f"Saving edges to {output_edges_file}...")
    with open(output_edges_file, 'w') as f:
        json.dump(edges_data, f, indent=2)

    print("Processing complete.")

if __name__ == '__main__':
    # --- IMPORTANT ---
    # Replace this path with the location of your PBF file
    parser = argparse.ArgumentParser(description='Parse OSM PBF file for routing')
    parser.add_argument('pbf_file', help='Path to the OSM PBF file')
    args = parser.parse_args()
    pbf_file = args.pbf_file
    
    try:
        parse_pbf_for_routing(pbf_file)
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure the PBF file path is correct and the file is not corrupted.")

