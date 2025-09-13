#!/usr/bin/env python3
"""
OpenStreetMap Data Downloader
Downloads OSM data in PBF format with support for custom bounding box downloads
"""

import os
import requests
from pathlib import Path
from typing import Tuple, Optional
import sys
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import argparse
import subprocess

class OSMDownloader:
    def __init__(self, bbox: Tuple[float, float, float, float], output_dir: Optional[str] = None):
        """
        Initialize OSM Downloader.
        
        Args:
            bbox: Custom bounding box (west, south, east, north)
            output_dir: Custom output directory
        """
        west, south, east, north = bbox
        area_name = f"bbox_{west:.3f}_{south:.3f}_{east:.3f}_{north:.3f}"
        self.bbox = bbox
        
        # Set output directory in data/
        self.output_dir = Path(output_dir) if output_dir else Path("data")
        self.output_dir.mkdir(exist_ok=True)
        
        print(f"Using bounding box: {bbox}")
        
    def download_osm_data(self) -> str:
        """Download OSM data using Overpass API and convert to PBF"""
        print(f"Downloading data from Overpass API...")
        west, south, east, north = self.bbox
        
        # Overpass query for all map data in the area
        overpass_query = f"""
        [out:xml];
        (
          way({south},{west},{north},{east});
          node({south},{west},{north},{east});
          relation({south},{west},{north},{east});
        );
        (._;>;);
        out meta;
        """
        
        overpass_url = "http://overpass-api.de/api/interpreter"
        
        try:
            print("Sending request to Overpass API...")
            response = requests.post(overpass_url, data={'data': overpass_query}, timeout=600)
            response.raise_for_status()
            
            # Save as OSM XML file temporarily
            area_name = f"bbox_{west:.3f}_{south:.3f}_{east:.3f}_{north:.3f}"
            osm_file = self.output_dir / f"{area_name}.osm"
            pbf_file = self.output_dir / f"{area_name}.pbf"
            
            # Save XML response
            with open(osm_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
                
            print(f"Downloaded OSM data to: {osm_file}")
            
            # Convert to PBF using osmosis
            try:
                print("Converting to PBF format...")
                subprocess.run(['osmosis', 
                             '--read-xml', str(osm_file),
                             '--write-pbf', str(pbf_file)],
                            check=True)
                print(f"Created PBF file: {pbf_file}")
                
                # Remove temporary XML file
                osm_file.unlink()
                
                return str(pbf_file)
                
            except subprocess.CalledProcessError as e:
                print(f"Error converting to PBF: {e}")
                print("XML file retained for manual conversion")
                return str(osm_file)
                
        except requests.exceptions.RequestException as e:
            print(f"Overpass API request failed: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Download OSM data in PBF format')
    parser.add_argument('--bbox', nargs=4, type=float, metavar=('WEST', 'SOUTH', 'EAST', 'NORTH'),
                       help='Bounding box coordinates: west south east north (longitude latitude)',
                       required=True)
    parser.add_argument('--output-dir', help='Output directory')
    
    args = parser.parse_args()
    
    try:
        downloader = OSMDownloader(
            bbox=tuple(args.bbox),
            output_dir=args.output_dir
        )
        downloader.download_osm_data()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
