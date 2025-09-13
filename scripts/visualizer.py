import json
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
from pathlib import Path
import time
import argparse

def create_simple_visualization(nodes_file: str, 
                            edges_file: str,
                            max_edges: Optional[int] = None) -> None:
    """
    Creates a simple interactive matplotlib visualization of the road network.
    
    Args:
        nodes_file: Path to the nodes JSON file
        edges_file: Path to the edges JSON file
        max_edges: Optional limit on number of edges to display
    """
    # Enable interactive mode
    plt.ion()
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
    
    # Create figure
    plt.figure(figsize=(15, 15))
    
    # Process edges
    print("\nPlotting edges...")
    edges_to_process = edges[:max_edges] if max_edges else edges
    
    # Plot edges by type
    major_roads = []
    other_roads = []
    
    for edge in edges_to_process:
        u_id, v_id = str(edge['u']), str(edge['v'])
        
        if u_id in nodes and v_id in nodes:
            u_node = nodes[u_id]
            v_node = nodes[v_id]
            
            # Create line segment
            x = [u_node['lon'], v_node['lon']]
            y = [u_node['lat'], v_node['lat']]
            
            # Categorize road
            highway = edge.get('highway', 'other')
            if highway in ['motorway', 'trunk', 'primary']:
                major_roads.append((x, y))
            else:
                other_roads.append((x, y))
    
    # Plot other roads first (as background)
    for x, y in other_roads:
        plt.plot(x, y, color='lightgray', linewidth=0.5, alpha=0.5)
        
    # Plot major roads on top
    for x, y in major_roads:
        plt.plot(x, y, color='red', linewidth=1, alpha=0.8)
    
    plt.title("Road Network")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.axis('equal')  # Keep the aspect ratio equal
    
    # Add a descriptive title
    plt.title("Road Network\n(Use mouse wheel to zoom, click and drag to pan)")
    
    print("\nStatistics:")
    print(f"Major roads: {len(major_roads):,}")
    print(f"Other roads: {len(other_roads):,}")
    print(f"Total roads plotted: {len(major_roads) + len(other_roads):,}")
    
    # Show plot and keep window open
    plt.show(block=True)  # This will block until the window is closed
    
    print("\nVisualization window closed.")

def main():
    parser = argparse.ArgumentParser(description='Simple Road Network Visualizer')
    parser.add_argument('--nodes', 
                       default='data/nodes.json',
                       help='Path to the nodes JSON file')
    parser.add_argument('--edges', 
                       default='data/edges.json',
                       help='Path to the edges JSON file')
    parser.add_argument('--max-edges', 
                       type=int,
                       default=None,
                       help='Maximum number of edges to display (optional)')
    args = parser.parse_args()
    
    print("Interactive Road Network Visualizer")
    print("=" * 40)
    print("Controls:")
    print("- Mouse wheel: Zoom in/out")
    print("- Click and drag: Pan")
    print("- Close window to exit")
    print("\nLoading visualization...")
    
    create_simple_visualization(
        nodes_file=args.nodes,
        edges_file=args.edges,
        max_edges=args.max_edges
    )
    
if __name__ == "__main__":
    main()
