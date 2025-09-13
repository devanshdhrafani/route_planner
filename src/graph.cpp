#include "route_planner/graph.hpp"
#include "route_planner/utils.hpp"
#include <cmath>

namespace route_planner {

void Graph::init(std::unordered_map<int64_t, Node> nodes, std::vector<Edge> edges) {
    nodes_ = std::move(nodes);
    edges_ = std::move(edges);
    build_adjacency_list();
}

const Node* Graph::get_node(int64_t id) const {
    auto it = nodes_.find(id);
    return it != nodes_.end() ? &it->second : nullptr;
}

std::vector<const Edge*> Graph::get_outgoing_edges(int64_t node_id) const {
    std::vector<const Edge*> result;
    
    // Special case: node_id == -1 means return all edges
    if (node_id == -1) {
        result.reserve(edges_.size());
        for (const auto& edge : edges_) {
            result.push_back(&edge);
        }
        return result;
    }
    
    auto it = adjacency_list_.find(node_id);
    if (it != adjacency_list_.end()) {
        result.reserve(it->second.size());
        for (size_t edge_idx : it->second) {
            result.push_back(&edges_[edge_idx]);
        }
    }
    
    return result;
}

const Edge* Graph::get_edge_between_nodes(int64_t from_node_id, int64_t to_node_id) const {
    auto it = adjacency_list_.find(from_node_id);
    if (it != adjacency_list_.end()) {
        for (size_t edge_idx : it->second) {
            const Edge& edge = edges_[edge_idx];
            if (edge.target == to_node_id) {
                return &edge;
            }
        }
    }
    
    // If not found in forward direction, check reverse direction for non-oneway roads
    auto reverse_it = adjacency_list_.find(to_node_id);
    if (reverse_it != adjacency_list_.end()) {
        for (size_t edge_idx : reverse_it->second) {
            const Edge& edge = edges_[edge_idx];
            if (edge.target == from_node_id && !edge.oneway) {
                return &edge;
            }
        }
    }
    
    return nullptr;
}

double Graph::straight_line_distance(int64_t from, int64_t to) const {
    const Node* from_node = get_node(from);
    const Node* to_node = get_node(to);
    
    if (!from_node || !to_node) {
        return -1.0;
    }
    
    return utils::haversine_distance(
        from_node->latitude, from_node->longitude,
        to_node->latitude, to_node->longitude
    );
}

void Graph::build_adjacency_list() {
    adjacency_list_.clear();
    
    // Pre-allocate space for efficiency
    adjacency_list_.reserve(nodes_.size());
    
    // Build adjacency list
    for (size_t i = 0; i < edges_.size(); ++i) {
        const auto& edge = edges_[i];
        adjacency_list_[edge.source].push_back(i);
        
        // If the road is not one-way, add the reverse direction
        if (!edge.oneway) {
            adjacency_list_[edge.target].push_back(i);
        }
    }
}

} // namespace route_planner