#!/usr/bin/env python3

import folium
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description='Visualize route on a map')
    parser.add_argument('--coords', type=str, required=True, help='Comma-separated list of coordinates (lat1,lon1,lat2,lon2,...)')
    parser.add_argument('--start', type=str, required=True, help='Start coordinates (lat,lon)')
    parser.add_argument('--end', type=str, required=True, help='End coordinates (lat,lon)')
    parser.add_argument('--output', type=str, default='route.html', help='Output HTML file')
    args = parser.parse_args()

    # Parse coordinates
    coords = [float(x) for x in args.coords.split(',')]
    path_points = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
    
    start_lat, start_lon = map(float, args.start.split(','))
    end_lat, end_lon = map(float, args.end.split(','))

    # Create map centered on the path
    center_lat = sum(p[0] for p in path_points) / len(path_points)
    center_lon = sum(p[1] for p in path_points) / len(path_points)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    # Add path
    folium.PolyLine(
        path_points,
        weight=3,
        color='blue',
        opacity=0.8
    ).add_to(m)

    # Add markers for start and end points
    folium.Marker(
        [start_lat, start_lon],
        popup='Start',
        icon=folium.Icon(color='green', icon='info-sign')
    ).add_to(m)

    folium.Marker(
        [end_lat, end_lon],
        popup='End',
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

    # Save map
    m.save(args.output)
    print(f"Map saved to {os.path.abspath(args.output)}")

if __name__ == '__main__':
    main()