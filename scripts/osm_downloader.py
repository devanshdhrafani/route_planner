#!/usr/bin/env python3
"""
OpenStreetMap Data Downloader - C++ Compatible
Downloads OSM data and converts it to formats suitable for C++ route planning applications
"""

import pyrosm
import geopandas as gpd
import pandas as pd
import json
import os
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import sys
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

class OSMDownloader:
    def __init__(self, city: str, country: str, output_dir: Optional[str] = None, 
                 bbox: Optional[Tuple[float, float, float, float]] = None):
        """
        Initialize OSM Downloader.
        
        Args:
            city: Name of the city
            country: Name of the country
            output_dir: Custom output directory (default: ./city_osm_data)
            bbox: Custom bounding box (west, south, east, north)
        """
        self.city = city.strip()
        self.country = country.strip()
        if not self.city or not self.country:
            raise ValueError("City and country names cannot be empty")
            
        self.output_dir = Path(output_dir) if output_dir else Path(f"./{self.city.lower()}_osm_data")
        self.output_dir.mkdir(exist_ok=True)
        self.bbox = bbox if bbox else self._get_city_bbox()
        
    def _get_city_bbox(self) -> Tuple[float, float, float, float]:
        """Get bounding box for the specified city using Nominatim"""
        print(f"Fetching bounding box for {self.city}, {self.country}...")
        
        geolocator = Nominatim(user_agent="osm_downloader")
        try:
            location = geolocator.geocode(f"{self.city}, {self.country}", exactly_one=True)
            if not location:
                raise ValueError(f"Could not find location: {self.city}, {self.country}")
                
            # Add a small buffer around the city (approximately 10km)
            buffer = 0.1  # degrees
            bbox = (
                location.longitude - buffer,  # west
                location.latitude - buffer,   # south
                location.longitude + buffer,  # east
                location.latitude + buffer    # north
            )
            print(f"Found bbox: {bbox}")
            return bbox
            
        except GeocoderTimedOut:
            raise TimeoutError("Geocoding service timed out. Please try again.")
    
    def _parse_maxspeed(self, maxspeed: Union[str, float, None]) -> float:
        """Parse maxspeed values into km/h"""
        if not maxspeed:
            return 50.0
            
        try:
            if isinstance(maxspeed, (int, float)):
                return float(maxspeed)
                
            maxspeed = maxspeed.lower().strip()
            if 'mph' in maxspeed:
                return float(maxspeed.replace('mph', '').strip()) * 1.609
            elif maxspeed.isdigit():
                return float(maxspeed)
            else:
                # Handle cases like "30 km/h" or other formats
                numeric_part = ''.join(c for c in maxspeed if c.isdigit())
                return float(numeric_part) if numeric_part else 50.0
        except:
            return 50.0

    def download_pbf_data(self) -> str:
        """Download PBF data for the region"""
        print(f"Downloading OSM data for {self.country}...")
        
        # Try to get data from pyrosm
        try:
            pbf_path = pyrosm.get_data(f"{self.city}, {self.country}", directory=str(self.output_dir))
            print(f"Downloaded PBF data to: {pbf_path}")
            return pbf_path
        except Exception as e:
            print(f"Pyrosm download failed: {e}")
            # Fallback: download directly from Geofabrik
            print("Downloading from Geofabrik...")
            # Handle USA/United States specifically
            if self.country.lower() in ['usa', 'united states', 'us']:
                url = "https://download.geofabrik.de/north-america/us-latest.osm.pbf"
            else:
                url = f"https://download.geofabrik.de/{self.country.lower()}/latest.osm.pbf"
            pbf_path = self.output_dir / f"{self.city.lower()}-latest.osm.pbf"
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(pbf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded PBF data to: {pbf_path}")
            return str(pbf_path)
    
    def extract_road_network(self, pbf_path: str) -> gpd.GeoDataFrame:
        """Extract road network from PBF file"""
        print("Extracting road network...")
        
        osm = pyrosm.OSM(pbf_path, bounding_box=self.bbox)
        drive_net = osm.get_network(network_type="driving")
        print(f"Extracted {len(drive_net)} road segments")
        
        return drive_net
    
    def extract_nodes_and_ways(self, pbf_path: str) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """Extract nodes and ways separately for graph construction"""
        print("Extracting nodes and ways...")
        
        osm = pyrosm.OSM(pbf_path, bounding_box=self.bbox)
        drive_net = osm.get_network(network_type="driving")
        
        nodes_list = []
        ways_list = []
        
        for idx, way in drive_net.iterrows():
            way_id = way.get('id', idx)
            geometry = way.geometry
            
            if hasattr(geometry, 'coords'):
                coords = list(geometry.coords)
                
                way_info = {
                    'way_id': way_id,
                    'highway': way.get('highway', 'unknown'),
                    'maxspeed': way.get('maxspeed'),
                    'oneway': way.get('oneway', 'no'),
                    'name': way.get('name'),
                    'length_m': way.get('length', 0),
                    'start_node': f"{coords[0][1]:.6f},{coords[0][0]:.6f}",
                    'end_node': f"{coords[-1][1]:.6f},{coords[-1][0]:.6f}",
                    'node_count': len(coords),
                    'geometry': geometry
                }
                ways_list.append(way_info)
                
                # Add nodes
                for i, (lon, lat) in enumerate(coords):
                    node_id = f"{lat:.6f},{lon:.6f}"
                    node_info = {
                        'node_id': node_id,
                        'lat': lat,
                        'lon': lon,
                        'way_id': way_id,
                        'position_in_way': i
                    }
                    nodes_list.append(node_info)
        
        nodes_df = pd.DataFrame(nodes_list)
        ways_df = gpd.GeoDataFrame(ways_list)
        
        # Remove duplicate nodes
        unique_nodes = nodes_df.groupby('node_id').agg({
            'lat': 'first',
            'lon': 'first',
            'way_id': lambda x: list(set(x)),
            'position_in_way': 'count'
        }).rename(columns={'position_in_way': 'way_count'}).reset_index()
        
        from shapely.geometry import Point
        unique_nodes['geometry'] = unique_nodes.apply(
            lambda row: Point(row['lon'], row['lat']), axis=1
        )
        nodes_gdf = gpd.GeoDataFrame(unique_nodes)
        
        print(f"Extracted {len(unique_nodes)} unique nodes and {len(ways_df)} ways")
        return nodes_gdf, ways_df
    
    def save_as_json(self, gdf: gpd.GeoDataFrame, filename: str):
        """Save GeoDataFrame as JSON (C++ friendly)"""
        output_path = self.output_dir / filename
        
        df = gdf.copy()
        if 'geometry' in df.columns:
            df['geometry_wkt'] = df['geometry'].apply(lambda x: x.wkt if x else None)
            df = df.drop('geometry', axis=1)
        
        json_data = df.to_dict('records')
        
        with open(output_path, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        print(f"Saved JSON data to: {output_path}")
    
    def save_as_csv(self, gdf: gpd.GeoDataFrame, filename: str):
        """Save GeoDataFrame as CSV (C++ friendly)"""
        output_path = self.output_dir / filename
        
        df = gdf.copy()
        if 'geometry' in df.columns:
            if hasattr(df.geometry.iloc[0], 'x'):
                df['lon'] = df.geometry.x
                df['lat'] = df.geometry.y
            df['geometry_wkt'] = df['geometry'].apply(lambda x: x.wkt if x else None)
            df = df.drop('geometry', axis=1)
        
        df.to_csv(output_path, index=False)
        print(f"Saved CSV data to: {output_path}")
    
    def create_adjacency_list(self, nodes_gdf: gpd.GeoDataFrame, ways_gdf: gpd.GeoDataFrame) -> Dict:
        """Create adjacency list representation for C++ graph algorithms"""
        print("Creating adjacency list...")
        
        adjacency_list = {}
        
        for _, way in ways_gdf.iterrows():
            way_id = way['way_id']
            start_node = way['start_node']
            end_node = way['end_node']
            length = way.get('length_m', 0)
            maxspeed = way.get('maxspeed', '50')
            
            # Parse maxspeed
            try:
                if isinstance(maxspeed, str) and 'mph' in maxspeed:
                    speed = float(maxspeed.replace('mph', '').strip()) * 1.609
                elif isinstance(maxspeed, str) and maxspeed.isdigit():
                    speed = float(maxspeed)
                else:
                    speed = 50.0
            except:
                speed = 50.0
            
            # Calculate travel time (weight) in seconds
            weight = (length / 1000.0) / speed * 3600 if speed > 0 else length
            
            # Add to adjacency list
            if start_node not in adjacency_list:
                adjacency_list[start_node] = []
            
            adjacency_list[start_node].append({
                'target': end_node,
                'weight': weight,
                'distance': length,
                'way_id': way_id,
                'speed_kmh': speed
            })
            
            # Add reverse direction if not oneway
            oneway = way.get('oneway', 'no')
            if oneway.lower() not in ['yes', 'true', '1']:
                if end_node not in adjacency_list:
                    adjacency_list[end_node] = []
                
                adjacency_list[end_node].append({
                    'target': start_node,
                    'weight': weight,
                    'distance': length,
                    'way_id': way_id,
                    'speed_kmh': speed
                })
        
        print(f"Created adjacency list with {len(adjacency_list)} nodes")
        return adjacency_list
    
    def download_and_process(self):
        """Main method to download and process all data"""
        print(f"Starting {self.city} OSM data download and processing...")
        
        try:
            pbf_path = self.download_pbf_data()
            road_network = self.extract_road_network(pbf_path)
            nodes_gdf, ways_gdf = self.extract_nodes_and_ways(pbf_path)
            
            print("Saving data in multiple formats...")
            for fmt in ['json', 'csv']:
                for data, name in [
                    (road_network, 'road_network'),
                    (nodes_gdf, 'nodes'),
                    (ways_gdf, 'ways')
                ]:
                    if fmt == 'json':
                        self.save_as_json(data, f"{name}.json")
                    else:
                        self.save_as_csv(data, f"{name}.csv")
            
            adjacency_list = self.create_adjacency_list(nodes_gdf, ways_gdf)
            adj_list_path = self.output_dir / "adjacency_list.json"
            with open(adj_list_path, 'w') as f:
                json.dump(adjacency_list, f, indent=2, default=str)
            print(f"Saved adjacency list to: {adj_list_path}")
            
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            raise

def main():
    if len(sys.argv) < 3:
        print("Usage: osm_downloader.py <city> <country> [output_dir]")
        sys.exit(1)
    
    city = sys.argv[1]
    country = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        downloader = OSMDownloader(city, country, output_dir)
        downloader.download_and_process()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
