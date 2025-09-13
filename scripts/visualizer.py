#!/usr/bin/env python3

import folium
import pandas as pd
import argparse
import os
from pathlib import Path
import webbrowser

def main():
    parser = argparse.ArgumentParser(description='Visualize route on a map')
    parser.add_argument('--csv', type=str, required=True, help='Path to CSV file containing route')
    args = parser.parse_args()

    # Read CSV file
    df = pd.read_csv(args.csv)
    
    # Calculate center point for initial map view
    center_lat = df['latitude'].mean()
    center_lon = df['longitude'].mean()
    
    # Create map centered on the path
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    # Create path coordinates
    path_coords = df[['latitude', 'longitude']].values.tolist()

    # Add path
    folium.PolyLine(
        path_coords,
        weight=3,
        color='blue',
        opacity=0.8
    ).add_to(m)

    # Add markers for start and end points with informative popups
    folium.Marker(
        [df.iloc[0]['latitude'], df.iloc[0]['longitude']],
        popup=folium.Popup(f"""
            <div style="font-family: Arial; font-size: 12px;">
                <b>Start Point</b><br>
                Node ID: {df.iloc[0]['node_id']}<br>
                Coordinates: ({df.iloc[0]['latitude']:.6f}, {df.iloc[0]['longitude']:.6f})
            </div>
        """, max_width=300),
        icon=folium.Icon(color='green', icon='info-sign')
    ).add_to(m)

    folium.Marker(
        [df.iloc[-1]['latitude'], df.iloc[-1]['longitude']],
        popup=folium.Popup(f"""
            <div style="font-family: Arial; font-size: 12px;">
                <b>End Point</b><br>
                Node ID: {df.iloc[-1]['node_id']}<br>
                Coordinates: ({df.iloc[-1]['latitude']:.6f}, {df.iloc[-1]['longitude']:.6f})<br>
                Total Distance: {df.iloc[-1]['cumulative_distance_km']:.2f} km
            </div>
        """, max_width=300),
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

    # Calculate bounds
    bounds = [
        [df['latitude'].min(), df['longitude'].min()],
        [df['latitude'].max(), df['longitude'].max()]
    ]
    
    # Fit map to bounds
    m.fit_bounds(bounds)
    
    # Save map to HTML file
    output_path = Path(args.csv).parent / 'route_visualization.html'
    m.save(str(output_path))
    print(f"Visualization saved to: {output_path}")
    
    # Open the map in default browser
    webbrowser.open(str(output_path))

if __name__ == '__main__':
    main()