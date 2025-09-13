#!/usr/bin/env python3
"""
Highway and Speed Analysis Script

This script analyzes the highway types and max speeds in an edges JSON file.
It provides insights into the road network composition and speed limit distribution.
"""

import json
import argparse
import sys
from collections import defaultdict, Counter
from pathlib import Path

def analyze_highway_data(edges_file):
    """
    Analyze highway types and max speeds from edges JSON file
    
    Args:
        edges_file (str): Path to the edges JSON file
        
    Returns:
        dict: Analysis results containing highway types, speeds, and statistics
    """
    print(f"Loading edges data from: {edges_file}")
    
    try:
        with open(edges_file, 'r') as f:
            edges = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {edges_file} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        return None
    
    print(f"Loaded {len(edges):,} edges")
    
    # Collect data
    highway_types = set()
    maxspeeds = set()
    highway_to_speeds = defaultdict(set)
    speed_to_highways = defaultdict(set)
    
    # Counters for statistics
    highway_counts = Counter()
    speed_counts = Counter()
    edges_with_highway = 0
    edges_with_maxspeed = 0
    edges_with_both = 0
    
    # Process each edge
    for edge in edges:
        highway = edge.get('highway')
        maxspeed = edge.get('maxspeed')
        
        # Track highway types
        if highway:
            highway_types.add(highway)
            highway_counts[highway] += 1
            edges_with_highway += 1
            
        # Track max speeds
        if maxspeed:
            maxspeeds.add(maxspeed)
            speed_counts[maxspeed] += 1
            edges_with_maxspeed += 1
            
        # Track combinations
        if highway and maxspeed:
            highway_to_speeds[highway].add(maxspeed)
            speed_to_highways[maxspeed].add(highway)
            edges_with_both += 1
    
    # Compile results
    results = {
        'total_edges': len(edges),
        'edges_with_highway': edges_with_highway,
        'edges_with_maxspeed': edges_with_maxspeed,
        'edges_with_both': edges_with_both,
        'highway_types': sorted(highway_types),
        'maxspeeds': sorted(maxspeeds),
        'highway_counts': dict(highway_counts),
        'speed_counts': dict(speed_counts),
        'highway_to_speeds': {k: sorted(v) for k, v in highway_to_speeds.items()},
        'speed_to_highways': {k: sorted(v) for k, v in speed_to_highways.items()}
    }
    
    return results

def print_analysis_report(results):
    """Print a comprehensive analysis report"""
    if not results:
        return
    
    total = results['total_edges']
    with_highway = results['edges_with_highway']
    with_speed = results['edges_with_maxspeed']
    with_both = results['edges_with_both']
    
    print("\n" + "="*80)
    print("HIGHWAY AND SPEED ANALYSIS REPORT")
    print("="*80)
    
    # Overall Statistics
    print(f"\n📊 OVERALL STATISTICS")
    print(f"{'Total edges:':<25} {total:,}")
    print(f"{'Edges with highway:':<25} {with_highway:,} ({100*with_highway/total:.1f}%)")
    print(f"{'Edges with maxspeed:':<25} {with_speed:,} ({100*with_speed/total:.1f}%)")
    print(f"{'Edges with both:':<25} {with_both:,} ({100*with_both/total:.1f}%)")
    
    # Highway Types
    print(f"\n🛣️  HIGHWAY TYPES ({len(results['highway_types'])} unique types)")
    print("-" * 60)
    highway_counts = results['highway_counts']
    for highway in results['highway_types']:
        count = highway_counts.get(highway, 0)
        percentage = 100 * count / total if total > 0 else 0
        print(f"{highway:<20} {count:>8,} edges ({percentage:>5.1f}%)")
    
    # Max Speeds
    print(f"\n🚗 MAX SPEEDS ({len(results['maxspeeds'])} unique values)")
    print("-" * 60)
    speed_counts = results['speed_counts']
    for speed in results['maxspeeds']:
        count = speed_counts.get(speed, 0)
        percentage = 100 * count / total if total > 0 else 0
        print(f"{speed:<20} {count:>8,} edges ({percentage:>5.1f}%)")
    
    # Highway to Speed Mapping
    print(f"\n🗺️  HIGHWAY TYPE → SPEED LIMITS")
    print("-" * 60)
    for highway in sorted(results['highway_to_speeds'].keys()):
        speeds = results['highway_to_speeds'][highway]
        print(f"{highway:<20} → {', '.join(speeds)}")
    
    # Speed to Highway Mapping
    print(f"\n🚦 SPEED LIMIT → HIGHWAY TYPES")
    print("-" * 60)
    for speed in sorted(results['speed_to_highways'].keys()):
        highways = results['speed_to_highways'][speed]
        print(f"{speed:<20} → {', '.join(highways)}")
    
    # Data Quality Insights
    print(f"\n🔍 DATA QUALITY INSIGHTS")
    print("-" * 60)
    missing_highway = total - with_highway
    missing_speed = total - with_speed
    missing_both = total - with_both
    
    if missing_highway > 0:
        print(f"⚠️  {missing_highway:,} edges ({100*missing_highway/total:.1f}%) missing highway type")
    
    if missing_speed > 0:
        print(f"⚠️  {missing_speed:,} edges ({100*missing_speed/total:.1f}%) missing max speed")
    
    if missing_both > 0:
        print(f"⚠️  {missing_both:,} edges ({100*missing_both/total:.1f}%) missing both highway and speed")
       
    # Most common combinations
    common_highways = sorted(highway_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    common_speeds = sorted(speed_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    print(f"\n📈 TOP 5 MOST COMMON")
    print("-" * 60)
    print("Highway Types:")
    for highway, count in common_highways:
        print(f"  {highway:<15} {count:,} edges")
    
    print("\nSpeed Limits:")
    for speed, count in common_speeds:
        print(f"  {speed:<15} {count:,} edges")

def main():
    parser = argparse.ArgumentParser(
        description='Analyze highway types and max speeds in edges JSON file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 analyze_highways.py --edges data/edges_bbox_-80.031_40.410_-79.896_40.494.json
  python3 analyze_highways.py --edges data/edges.json --output analysis_report.txt
        """
    )
    
    parser.add_argument('--edges', type=str, required=True,
                       help='Path to edges JSON file')
    parser.add_argument('--output', type=str,
                       help='Output file for the report (optional, defaults to stdout)')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.edges).exists():
        print(f"Error: Edges file '{args.edges}' does not exist")
        sys.exit(1)
    
    # Analyze the data
    results = analyze_highway_data(args.edges)
    
    if results is None:
        sys.exit(1)
    
    # Output the report
    if args.output:
        # Redirect output to file
        original_stdout = sys.stdout
        with open(args.output, 'w') as f:
            sys.stdout = f
            print_analysis_report(results)
        sys.stdout = original_stdout
        print(f"Analysis report saved to: {args.output}")
    else:
        print_analysis_report(results)

if __name__ == '__main__':
    main()