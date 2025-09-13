import json
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
from typing import Dict, List, Tuple, Optional
import time

def create_fast_network_visualizer(nodes_file: str = 'nodes.json', 
                                 edges_file: str = 'edges.json',
                                 max_edges: Optional[int] = None,
                                 show_nodes: bool = True,
                                 node_size: float = 0.5,
                                 edge_width: float = 0.3,
                                 figsize: Tuple[int, int] = (12, 10),
                                 title: str = "Road Network Visualization"):
    """
    Fast road network visualizer optimized for large datasets.
    
    Args:
        nodes_file: Path to nodes JSON file
        edges_file: Path to edges JSON file  
        max_edges: Maximum number of edges to plot (for performance)
        show_nodes: Whether to show nodes as points
        node_size: Size of node markers
        edge_width: Width of edge lines
        figsize: Figure size tuple
        title: Plot title
    """
    
    print("Loading network data...")
    start_time = time.time()
    
    # Load data
    try:
        with open(nodes_file, 'r') as f:
            nodes = json.load(f)
        with open(edges_file, 'r') as f:
            edges = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None, None
        
    print(f"Loaded {len(nodes)} nodes and {len(edges)} edges in {time.time() - start_time:.2f}s")
    
    # Limit edges for performance if specified
    if max_edges and len(edges) > max_edges:
        print(f"Limiting to {max_edges} edges for performance...")
        edges = edges[:max_edges]
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize, dpi=100)
    
    # Prepare edge lines for LineCollection
    print("Preparing edge visualization...")
    start_time = time.time()
    
    edge_lines = []
    edge_colors = []
    
    for edge in edges:
        u_id = str(edge['u'])
        v_id = str(edge['v'])
        
        if u_id in nodes and v_id in nodes:
            u_node = nodes[u_id]
            v_node = nodes[v_id]
            
            # Create line segment
            line = [(u_node['lon'], u_node['lat']), 
                   (v_node['lon'], v_node['lat'])]
            edge_lines.append(line)
            
            # Color by road type
            highway = edge.get('highway', 'unknown')
            if highway in ['motorway', 'trunk']:
                edge_colors.append('red')
            elif highway in ['primary', 'secondary']:
                edge_colors.append('orange') 
            elif highway in ['residential', 'tertiary']:
                edge_colors.append('gray')
            else:
                edge_colors.append('lightgray')
    
    # Plot edges using LineCollection for performance
    if edge_lines:
        lc = LineCollection(edge_lines, colors=edge_colors, linewidths=edge_width, alpha=0.7)
        ax.add_collection(lc)
    
    print(f"Prepared {len(edge_lines)} edges in {time.time() - start_time:.2f}s")
    
    # Plot nodes if requested
    if show_nodes:
        print("Preparing node visualization...")
        start_time = time.time()
        
        node_lons = [node['lon'] for node in nodes.values()]
        node_lats = [node['lat'] for node in nodes.values()]
        
        ax.scatter(node_lons, node_lats, s=node_size, c='blue', alpha=0.6, zorder=2)
        
        print(f"Plotted {len(node_lons)} nodes in {time.time() - start_time:.2f}s")
    
    # Configure plot
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.grid(True, alpha=0.3)
    
    # Add legend
    legend_elements = [
        plt.Line2D([], [], color='red', lw=2, label='Motorway/Trunk'),
        plt.Line2D([], [], color='orange', lw=2, label='Primary/Secondary'),
        plt.Line2D([], [], color='gray', lw=2, label='Residential/Tertiary'),
        plt.Line2D([], [], color='lightgray', lw=2, label='Other')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    return fig, ax

# Interactive version with zoom capabilities
def create_interactive_visualizer(nodes_file: str = 'nodes.json', 
                                edges_file: str = 'edges.json',
                                max_edges: int = 50000):
    """Interactive version with zoom and pan capabilities."""
    
    fig, ax = create_fast_network_visualizer(nodes_file, edges_file, max_edges)
    
    if fig is None:
        return None
    
    # Enable interactive navigation
    plt.ion()  # Turn on interactive mode
    
    def on_key(event):
        if event.key == 'r':  # Reset view
            ax.autoscale()
            plt.draw()
        elif event.key == 'h':  # Toggle nodes
            for collection in ax.collections:
                if hasattr(collection, '_sizes'):  # This is likely the scatter plot
                    collection.set_visible(not collection.get_visible())
            plt.draw()
    
    fig.canvas.mpl_connect('key_press_event', on_key)
    
    print("\nInteractive controls:")
    print("- Mouse: Pan and zoom")
    print("- 'r' key: Reset view")  
    print("- 'h' key: Toggle node visibility")
    
    return fig, ax

# Usage examples
def main():
    print("Fast Road Network Visualizer")
    print("=" * 40)
    
    # For large networks, limit edges
    print("\n1. Large network visualization (limited edges):")
    fig1, ax1 = create_fast_network_visualizer('nodes.json', 'edges.json', 
                                             max_edges=25000, show_nodes=False)
    
    # For smaller networks, show everything
    print("\n2. Full network visualization:")
    fig2, ax2 = create_fast_network_visualizer('nodes.json', 'edges.json', 
                                             show_nodes=True)
    
    # Interactive version
    print("\n3. Interactive visualization:")
    fig3, ax3 = create_interactive_visualizer('nodes.json', 'edges.json')
    
    # Save figures to files if they were created successfully
    if fig1:
        fig1.savefig('network_limited_edges.png')
        print("\nSaved limited edges visualization to network_limited_edges.png")
    if fig2:
        fig2.savefig('network_full.png')
        print("\nSaved full network visualization to network_full.png")
    if fig3:
        fig3.savefig('network_interactive.png')
        print("\nSaved interactive visualization to network_interactive.png")

if __name__ == "__main__":
    main()
