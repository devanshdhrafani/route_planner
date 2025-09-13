#include "route_planner/planner.hpp"
#include "route_planner/utils.hpp"
#include <limits>
#include <cmath>

namespace route_planner {

int64_t Planner::find_nearest_node(const Graph& graph, const Coordinates& coord) {
    int64_t nearest_id = -1;
    double min_dist = std::numeric_limits<double>::infinity();
    
    // Simple linear search through all nodes
    // TODO: Replace with k-d tree or similar spatial index for better performance
    for (const auto& edge : graph.get_outgoing_edges(-1)) {  // -1 gets all edges
        // Check both source and target nodes of each edge
        for (int64_t node_id : {edge->source, edge->target}) {
            const Node* node = graph.get_node(node_id);
            if (!node) continue;
            
            double dist = utils::haversine_distance(
                coord.latitude, coord.longitude,
                node->latitude, node->longitude
            );
        
            if (dist < min_dist) {
                min_dist = dist;
                nearest_id = node_id;
            }
        }
    }
    return nearest_id;
}

} // namespace route_planner