#!/usr/bin/env python3

import folium
import pandas as pd
import argparse
import os
from pathlib import Path
import webbrowser

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
        'time': ['red', 'darkred', 'pink']
    }
    
    if cost_function in colors:
        return colors[cost_function][index % len(colors[cost_function])]
    else:
        # Fallback colors for unknown cost functions
        fallback_colors = ['green', 'purple', 'orange', 'gray', 'black']
        return fallback_colors[index % len(fallback_colors)]

def main():
    parser = argparse.ArgumentParser(description='Visualize one or more routes on a map')
    parser.add_argument('--csv', type=str, nargs='+', required=True, 
                       help='Path(s) to CSV file(s) containing route(s). Can specify multiple files.')
    args = parser.parse_args()

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