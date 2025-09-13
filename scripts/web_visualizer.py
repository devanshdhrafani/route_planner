import json
from typing import Dict, List, Tuple, Optional
import folium
from pathlib import Path
import time
import argparse
import webbrowser
import os

def is_within_bbox(lat: float, lon: float, bbox: List[float]) -> bool:
    """
    Check if a point is within the bounding box.
    
    Args:
        lat: Latitude
        lon: Longitude
        bbox: [min_lon, min_lat, max_lon, max_lat]
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat

def create_web_visualization(nodes_file: str, 
                           edges_file: str,
                           output_file: str = "visuals/road_network.html") -> None:
    """
    Creates an interactive web-based visualization of the road network using Folium.
    
    Args:
        nodes_file: Path to the nodes JSON file
        edges_file: Path to the edges JSON file
        output_file: Path where the HTML file will be saved
    """
    print("Loading network data...")
    start_time = time.time()
    
    try:
        with open(nodes_file, 'r') as f:
            nodes = json.load(f)
        with open(edges_file, 'r') as f:
            edges = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
        
    print(f"Loaded {len(nodes):,} nodes and {len(edges):,} edges in {time.time() - start_time:.2f}s")
    
    # Calculate center point from first node
    first_node = next(iter(nodes.values()))
    center_lat, center_lon = first_node['lat'], first_node['lon']
    
    # Create map centered on the first node
    m = folium.Map(location=[center_lat, center_lon], 
                   zoom_start=13,
                   tiles='cartodbpositron')  # Light map style
    
    # Extract bounding box from filename
    bbox = None
    if 'bbox_' in nodes_file:
        try:
            bbox_str = nodes_file.split('bbox_')[1].split('.')[0]
            coords = list(map(float, bbox_str.split('_')))
            if len(coords) == 4:
                bbox = coords  # [min_lon, min_lat, max_lon, max_lat]
                print(f"Using bounding box: {bbox}")
        except:
            print("Warning: Could not extract bounding box from filename")
    
    if bbox:
        print(f"Using bounding box: {bbox}")
    
    # Process edges
    print("\nPlotting edges...")
    
    # Track statistics
    highways_count = 0
    city_roads_count = 0
    
    # Create feature groups for different road types
    highways = folium.FeatureGroup(name='Highways and Major Roads')
    city_roads = folium.FeatureGroup(name='City Roads')
    
    for edge in edges:
        u_id, v_id = str(edge['u']), str(edge['v'])
        
        if u_id in nodes and v_id in nodes:
            u_node = nodes[u_id]
            v_node = nodes[v_id]
            
            # Get edge properties
            highway = edge.get('highway', 'other')
            name = edge.get('name', 'Unnamed')
            maxspeed = edge.get('maxspeed', 'Unknown')
            oneway = 'Yes' if edge.get('oneway', False) else 'No'
            
            # Create popup content
            popup_content = f"""
                <b>Road Details:</b><br>
                Name: {name}<br>
                Type: {highway}<br>
                Speed Limit: {maxspeed}<br>
                One-way: {oneway}<br>
            """
            
            # Filter edges outside bounding box if bbox is available
            if bbox:
                u_lat, u_lon = u_node['lat'], u_node['lon']
                v_lat, v_lon = v_node['lat'], v_node['lon']
                
                # Skip if both endpoints are outside the bbox
                if not (is_within_bbox(u_lat, u_lon, bbox) or 
                       is_within_bbox(v_lat, v_lon, bbox)):
                    continue
            
            # Create line coordinates
            line = [[u_node['lat'], u_node['lon']], 
                   [v_node['lat'], v_node['lon']]]
            
            # Style based on road type
            if highway in ['motorway', 'trunk', 'primary', 'motorway_link', 'trunk_link']:
                folium.PolyLine(
                    locations=line,
                    weight=3,
                    color='orange',
                    opacity=0.8,
                    popup=folium.Popup(popup_content, max_width=300)
                ).add_to(highways)
                highways_count += 1
            else:
                folium.PolyLine(
                    locations=line,
                    weight=1.5,
                    color='blue',
                    opacity=0.6,
                    popup=folium.Popup(popup_content, max_width=300)
                ).add_to(city_roads)
                city_roads_count += 1
    
    # Add road layers to map in correct order
    city_roads.add_to(m)  # Add city roads first (background)
    highways.add_to(m)    # Add highways on top
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save the map
    m.save(output_file)
    
    print("\nStatistics:")
    print(f"Highways and major roads: {highways_count:,}")
    print(f"City roads: {city_roads_count:,}")
    print(f"Total roads plotted: {highways_count + city_roads_count:,}")
    
    # Get absolute path for the HTML file
    abs_path = os.path.abspath(output_file)
    print(f"\nMap saved to: {abs_path}")
    
    # Open in default browser
    print("Opening map in your default web browser...")
    webbrowser.open(f'file://{abs_path}')

def main():
    parser = argparse.ArgumentParser(description='Interactive Web Road Network Visualizer')
    parser.add_argument('--nodes', 
                       default='data/nodes.json',
                       help='Path to the nodes JSON file')
    parser.add_argument('--edges', 
                       default='data/edges.json',
                       help='Path to the edges JSON file')
    parser.add_argument('--output',
                       default='visuals/road_network.html',
                       help='Path where the HTML file will be saved (default: visuals/road_network.html)')
    args = parser.parse_args()
    
    print("Interactive Web Road Network Visualizer")
    print("=" * 40)
    print("Features:")
    print("- Zoomable and pannable map")
    print("- Toggle road layers on/off")
    print("- Click roads to see detailed properties")
    print("- Highways in orange, city roads in blue")
    print("- Base map with street names and landmarks")
    print("\nCreating visualization...")
    
    create_web_visualization(
        nodes_file=args.nodes,
        edges_file=args.edges,
        output_file=args.output
    )
    
if __name__ == "__main__":
    main()