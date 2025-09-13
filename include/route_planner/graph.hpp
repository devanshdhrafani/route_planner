#pragma once

#include "types.hpp"
#include "utils.hpp"
#include <unordered_map>
#include <vector>
#include <memory>

namespace route_planner {

/**
 * Represents the road network as a graph structure.
 * Designed to support A* pathfinding algorithm.
 */
class Graph {
public:
    /**
     * Initialize the graph with nodes and edges.
     * 
     * @param nodes Map of node IDs to Node objects
     * @param edges Vector of Edge objects
     */
    void init(std::unordered_map<int64_t, Node> nodes, std::vector<Edge> edges);
    
    /**
     * Get a node by its ID.
     * 
     * @param id The node ID to look up
     * @return Pointer to the node if found, nullptr otherwise
     */
    const Node* get_node(int64_t id) const;
    
    /**
     * Get all outgoing edges from a node.
     * 
     * @param node_id The ID of the node to get edges for
     * @return Vector of pointers to edges starting at the given node
     */
    std::vector<const Edge*> get_outgoing_edges(int64_t node_id) const;
    
    /**
     * Calculate the straight-line distance between two nodes.
     * This will be used as the heuristic function for A*.
     * 
     * @param from Source node ID
     * @param to Target node ID
     * @return Distance in meters, or -1 if either node doesn't exist
     */
    double straight_line_distance(int64_t from, int64_t to) const;

private:
    std::unordered_map<int64_t, Node> nodes_;
    std::vector<Edge> edges_;
    
    // Adjacency list: node ID -> indices of outgoing edges in edges_ vector
    std::unordered_map<int64_t, std::vector<size_t>> adjacency_list_;
    
    /**
     * Build the adjacency list from the edges.
     * Called by init() after loading nodes and edges.
     */
    void build_adjacency_list();
};

} // namespace route_planner