#!/usr/bin/env python3

import folium
import pandas as pd
import argparse
import os
from pathlib import Path
import webbrowser
import yaml
import json

def read_traffic_config(config_path):
    """Read traffic configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        traffic_edges = {}
        if 'traffic' in config and 'edges' in config['traffic']:
            for edge_key, modification in config['traffic']['edges'].items():
                traffic_edges[edge_key] = modification
        
        return traffic_edges
    except Exception as e:
        print(f"Warning: Could not read traffic config: {e}")
        return {}

def load_edge_data(edges_file):
    """Load edge data from JSON file for traffic visualization"""
    try:
        with open(edges_file, 'r') as f:
            edges = json.load(f)
        
        # Create a mapping from "source-target" to edge data
        edge_lookup = {}
        for edge in edges:
            source = edge['u']
            target = edge['v']
            edge_key = f"{source}-{target}"
            edge_lookup[edge_key] = edge
            
        return edge_lookup
    except Exception as e:
        print(f"Warning: Could not load edge data: {e}")
        return {}

def load_node_data(nodes_file):
    """Load node data from JSON file"""
    try:
        with open(nodes_file, 'r') as f:
            nodes = json.load(f)
        return nodes
    except Exception as e:
        print(f"Warning: Could not load node data: {e}")
        return {}

def read_route_csv_with_metadata(csv_path):
    """Read CSV file and extract both metadata and path data"""
    metadata = {}
    
    with open(csv_path, 'r') as f:
        # Read metadata from comment lines
        for line in f:
            if line.startswith('#'):
                key, value = line[2:].strip().split(': ', 1)
                if key != 'cost_function':
                    metadata[key] = float(value)
                else:
                    metadata[key] = value
            elif line.startswith('node_id'):
                break
    
    # Read the CSV data
    df = pd.read_csv(csv_path, comment='#')
    return metadata, df

def get_route_color(cost_function, index):
    """Get color for route based on cost function and index"""
    colors = {
        'distance': ['blue', 'darkblue', 'lightblue'],
        'time': ['green', 'darkgreen', 'lightgreen']
    }
    
    if cost_function in colors:
        return colors[cost_function][index % len(colors[cost_function])]
    else:
        # Fallback colors for unknown cost functions
        fallback_colors = ['purple', 'orange', 'gray', 'black']
        return fallback_colors[index % len(fallback_colors)]

def main():
    parser = argparse.ArgumentParser(description='Visualize one or more routes on a map with traffic conditions')
    parser.add_argument('--csv', type=str, nargs='+', required=True, 
                       help='Path(s) to CSV file(s) containing route(s). Can specify multiple files.')
    parser.add_argument('--config', type=str, default='config/default.yaml',
                       help='Path to configuration file with traffic data')
    parser.add_argument('--show-traffic', action='store_true', default=True,
                       help='Show traffic-affected edges on the map')
    parser.add_argument('--no-traffic', action='store_true', default=False,
                       help='Hide traffic conditions (show routes only)')
    args = parser.parse_args()

    # Handle traffic display logic
    if args.no_traffic:
        args.show_traffic = False

    # Load traffic configuration and edge data if showing traffic
    traffic_edges = {}
    edge_lookup = {}
    node_lookup = {}
    
    if args.show_traffic:
        # Try to find config and data files relative to CSV location
        csv_dir = Path(args.csv[0]).parent.parent  # Go up from results/ to project root
        config_path = csv_dir / args.config
        
        if config_path.exists():
            traffic_edges = read_traffic_config(config_path)
            print(f"Loaded {len(traffic_edges)} traffic conditions from config")
            
            # Load edge and node data for visualization
            edges_file = csv_dir / "data/edges_bbox_-80.031_40.410_-79.896_40.494.json"
            nodes_file = csv_dir / "data/nodes_bbox_-80.031_40.410_-79.896_40.494.json"
            
            if edges_file.exists() and nodes_file.exists():
                edge_lookup = load_edge_data(edges_file)
                node_lookup = load_node_data(nodes_file)
                print(f"Loaded {len(edge_lookup)} edges and {len(node_lookup)} nodes for traffic visualization")
            else:
                print("Warning: Could not find edge/node data files for traffic visualization")
        else:
            print(f"Warning: Config file not found at {config_path}")

    if len(args.csv) == 1:
        print(f"Visualizing single route from: {args.csv[0]}")
    else:
        print(f"Visualizing {len(args.csv)} routes for comparison")

    # Read all route data
    routes_data = []
    all_lats = []
    all_lons = []
    
    for csv_path in args.csv:
        if not os.path.exists(csv_path):
            print(f"Error: File {csv_path} does not exist")
            continue
            
        try:
            metadata, df = read_route_csv_with_metadata(csv_path)
            routes_data.append({
                'path': csv_path,
                'metadata': metadata,
                'df': df
            })
            
            # Collect all coordinates for map bounds
            all_lats.extend(df['latitude'].tolist())
            all_lons.extend(df['longitude'].tolist())
            
            print(f"Loaded route: {metadata.get('cost_function', 'unknown')} optimization")
            print(f"  Distance: {metadata.get('total_distance_km', 0) * 0.621371:.2f} miles")
            print(f"  Time: {metadata.get('total_time_minutes', 0):.1f} minutes")
            print(f"  Nodes: {metadata.get('path_nodes', len(df))}")
            
        except Exception as e:
            print(f"Error reading {csv_path}: {e}")
            continue
    
    if not routes_data:
        print("No valid routes to display")
        return

    # Calculate center point for initial map view
    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    
    # Create map centered on all paths
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    # Add each route to the map
    for i, route in enumerate(routes_data):
        metadata = route['metadata']
        df = route['df']
        cost_function = metadata.get('cost_function', 'unknown')
        
        # Get route color
        color = get_route_color(cost_function, i)
        
        # Create path coordinates
        path_coords = df[['latitude', 'longitude']].values.tolist()

        # Add path with label
        route_label = f"{cost_function.title()} Route"
        if len(routes_data) > 1:
            route_label += f" #{i+1}"
            
        folium.PolyLine(
            path_coords,
            weight=4,
            color=color,
            opacity=0.8,
            popup=folium.Popup(f"""
                <div style="font-family: Arial; font-size: 12px;">
                    <b>{route_label}</b><br>
                    Cost Function: {cost_function}<br>
                    Total Distance: {metadata.get('total_distance_km', 0) * 0.621371:.2f} miles<br>
                    Total Time: {metadata.get('total_time_minutes', 0):.1f} minutes<br>
                    Path Nodes: {metadata.get('path_nodes', len(df))}
                </div>
            """, max_width=300)
        ).add_to(m)

        # Add start marker (only for first route to avoid clutter)
        if i == 0:
            folium.Marker(
                [df.iloc[0]['latitude'], df.iloc[0]['longitude']],
                popup=folium.Popup(f"""
                    <div style="font-family: Arial; font-size: 12px;">
                        <b>Start Point</b><br>
                        Node ID: {df.iloc[0]['node_id']}<br>
                        Coordinates: ({df.iloc[0]['latitude']:.6f}, {df.iloc[0]['longitude']:.6f})
                    </div>
                """, max_width=300),
                icon=folium.Icon(color='green', icon='play')
            ).add_to(m)

        # Add end marker (only for first route to avoid clutter)
        if i == 0:
            folium.Marker(
                [df.iloc[-1]['latitude'], df.iloc[-1]['longitude']],
                popup=folium.Popup(f"""
                    <div style="font-family: Arial; font-size: 12px;">
                        <b>End Point</b><br>
                        Node ID: {df.iloc[-1]['node_id']}<br>
                        Coordinates: ({df.iloc[-1]['latitude']:.6f}, {df.iloc[-1]['longitude']:.6f})
                    </div>
                """, max_width=300),
                icon=folium.Icon(color='red', icon='stop')
            ).add_to(m)

    # Add traffic-affected edges to the map
    if args.show_traffic and traffic_edges and edge_lookup and node_lookup:
        print(f"Adding {len(traffic_edges)} traffic-affected edges to map...")
        
        for edge_key, modification in traffic_edges.items():
            if edge_key in edge_lookup:
                edge = edge_lookup[edge_key]
                source_id = str(edge['u'])
                target_id = str(edge['v'])
                
                if source_id in node_lookup and target_id in node_lookup:
                    source_node = node_lookup[source_id]
                    target_node = node_lookup[target_id]
                    
                    # Determine traffic color based on modification
                    traffic_color = '#FF4500'  # Default bright orange for traffic
                    traffic_weight = 6
                    traffic_opacity = 0.5
                    traffic_dash_array = None
                    
                    if modification['type'] == 'multiplier':
                        multiplier = modification['value']
                        if multiplier <= 0.3:
                            traffic_color = '#FF0000'  # Bright red for heavy traffic
                            traffic_weight = 8
                            traffic_dash_array = None
                            traffic_opacity = 0.5
                        elif multiplier <= 0.6:
                            traffic_color = '#FF4500'  # Bright orange for moderate traffic
                            traffic_weight = 6
                            traffic_dash_array = '8,4'
                            traffic_opacity = 0.5
                        else:
                            traffic_color = '#FFA500'  # Orange for light traffic
                            traffic_weight = 5
                            traffic_dash_array = '12,6'
                            traffic_opacity = 0.5
                    elif modification['type'] == 'speed_override':
                        traffic_color = '#8B0000'  # Dark red for speed overrides (construction)
                        traffic_weight = 10
                        traffic_dash_array = '4,4'
                        traffic_opacity = 0.7
                    
                    # Create traffic edge
                    traffic_coords = [
                        [source_node['lat'], source_node['lon']],
                        [target_node['lat'], target_node['lon']]
                    ]
                    
                    # Create popup with traffic info
                    popup_text = f"""
                        <div style="font-family: Arial; font-size: 12px;">
                            <b>🚦 Traffic Condition</b><br>
                            Edge: {edge_key}<br>
                            Type: {modification['type']}<br>
                            Value: {modification['value']}<br>
                            Road: {edge.get('name', 'Unnamed')}<br>
                            Highway: {edge.get('highway', 'Unknown')}
                        </div>
                    """
                    
                    folium.PolyLine(
                        traffic_coords,
                        weight=traffic_weight,
                        color=traffic_color,
                        opacity=traffic_opacity,
                        dash_array=traffic_dash_array,
                        popup=folium.Popup(popup_text, max_width=300)
                    ).add_to(m)

    # Add enhanced legend showing all routes
    legend_html = """
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 320px; height: auto; 
                background-color: white; border: 3px solid #333; z-index: 9999; 
                font-size: 13px; padding: 15px; border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                font-family: Arial, sans-serif;">
    <h3 style="margin-top: 0; margin-bottom: 10px; color: #333; text-align: center; 
               border-bottom: 2px solid #ddd; padding-bottom: 8px;">🗺️ Route Comparison</h3>
    """
    
    for i, route in enumerate(routes_data):
        metadata = route['metadata']
        cost_function = metadata.get('cost_function', 'unknown')
        color = get_route_color(cost_function, i)
        
        route_label = f"{cost_function.title()} Route"
        if len(routes_data) > 1:
            route_label += f" #{i+1}"
        
        # Create a visual line indicator
        legend_html += f"""
        <div style="margin: 8px 0; padding: 8px; 
                    border: 1px solid #ddd; border-radius: 4px; 
                    background-color: #f9f9f9;">
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 30px; height: 4px; background-color: {color}; 
                           margin-right: 10px; border-radius: 2px;"></div>
                <b style="color: #333;">{route_label}</b>
            </div>
            <div style="margin-left: 40px; color: #666; font-size: 11px;">
                📏 Distance: <strong>{metadata.get('total_distance_km', 0) * 0.621371:.2f} miles</strong><br>
                ⏱️ Time: <strong>{metadata.get('total_time_minutes', 0):.1f} min</strong>
            </div>
        </div>
        """
    
    # Add traffic legend if traffic is shown
    if args.show_traffic and traffic_edges:
        legend_html += """
        <div style="margin-top: 10px; padding: 8px; 
                    border-top: 2px solid #ddd; 
                    background-color: #fff3e0; border-radius: 4px;">
            <h4 style="margin: 0 0 8px 0; color: #333;">🚦 Traffic Conditions</h4>
            <div style="margin: 4px 0;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 30px; height: 4px; background-color: #FF0000; 
                               margin-right: 10px; border-radius: 2px;"></div>
                    <small><b>Heavy Traffic (≤30% speed)</b></small>
                </div>
            </div>
            <div style="margin: 4px 0;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 30px; height: 4px; background-color: #FF4500; 
                               margin-right: 10px; border-radius: 2px; 
                               background-image: repeating-linear-gradient(90deg, #FF4500, #FF4500 8px, transparent 8px, transparent 12px);"></div>
                    <small><b>Moderate Traffic (≤60% speed)</b></small>
                </div>
            </div>
            <div style="margin: 4px 0;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 30px; height: 5px; background-color: #8B0000; 
                               margin-right: 10px; border-radius: 2px; 
                               background-image: repeating-linear-gradient(90deg, #8B0000, #8B0000 4px, transparent 4px, transparent 8px);"></div>
                    <small><b>Construction/Override</b></small>
                </div>
            </div>
            <small style="color: #666; font-style: italic;">
                """ + str(len(traffic_edges)) + """ traffic condition(s) applied
            </small>
        </div>
        """
    
    # Add summary comparison if multiple routes
    if len(routes_data) > 1:
        legend_html += """
        <div style="margin-top: 10px; padding: 8px; 
                    border-top: 2px solid #ddd; 
                    background-color: #f0f8ff; border-radius: 4px;">
            <small style="color: #555; font-style: italic;">
                💡 <strong>Tip:</strong> Click on any route line for detailed information
            </small>
        </div>
        """
    
    # Add the legend using the working method
    from branca.element import MacroElement, Template
    
    legend_template = f"""
    {{% macro html(this, kwargs) %}}
    {legend_html}
    {{% endmacro %}}
    """
    
    legend_macro = MacroElement()
    legend_macro._template = Template(legend_template)
    m.add_child(legend_macro)

    # Calculate bounds and fit map
    if all_lats and all_lons:
        bounds = [
            [min(all_lats), min(all_lons)],
            [max(all_lats), max(all_lons)]
        ]
        m.fit_bounds(bounds)
    
    # Generate output filename
    if len(args.csv) == 1:
        output_path = Path(args.csv[0]).parent / 'route_visualization.html'
    else:
        output_path = Path(args.csv[0]).parent / 'route_comparison.html'
    
    # Save map to HTML file
    m.save(str(output_path))
    print(f"\nVisualization saved to: {output_path}")
    
    # Open the map in default browser
    webbrowser.open(str(output_path))

if __name__ == '__main__':
    main()