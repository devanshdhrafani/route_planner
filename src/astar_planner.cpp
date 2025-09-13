#include "route_planner/astar_planner.hpp"
#include "route_planner/utils.hpp"
#include <queue>
#include <unordered_map>
#include <limits>
#include <algorithm>

namespace route_planner {

PlannerResult AStarPlanner::plan(const Graph& graph,
                               const Coordinates& start_coord,
                               const Coordinates& goal_coord) {
    int64_t start_id = find_nearest_node(graph, start_coord);
    int64_t goal_id = find_nearest_node(graph, goal_coord);
    
    if (start_id == -1 || goal_id == -1) {
        PlannerResult result;
        result.success = false;
        return result;
    }

    // Track visited nodes and their states
    std::unordered_map<int64_t, NodeState> node_states;
    
    // Priority queue ordered by f-value (g + h)
    std::priority_queue<QueueEntry> open_set;
    
    // Initialize start node
    node_states[start_id] = NodeState{0.0, -1};
    open_set.push(QueueEntry{start_id, 0.0, heuristic(graph, start_id, goal_id)});

    int nodes_explored = 0;
    
    while (!open_set.empty()) {
        QueueEntry current = open_set.top();
        open_set.pop();
        
        int64_t current_id = current.node_id;
        nodes_explored++;
        
        // Goal check
        if (current_id == goal_id) {
            return reconstruct_path(graph, node_states, start_id, goal_id);
        }
        
        // Skip if we've found a better path to this node
        if (current.g_value > node_states[current_id].g_score) {
            continue;
        }
        
        // Explore neighbors
        for (const auto& edge_ptr : graph.get_outgoing_edges(current_id)) {
            double tentative_g = node_states[current_id].g_score + edge_ptr->distance;
            int64_t neighbor_id = edge_ptr->target;
            
            // If we haven't visited this node or found a better path
            if (node_states.find(neighbor_id) == node_states.end() ||
                tentative_g < node_states[neighbor_id].g_score) {
                
                // Update node state
                node_states[neighbor_id] = {tentative_g, current_id};
                
                // Add to open set
                double h_value = heuristic(graph, neighbor_id, goal_id);
                open_set.push(QueueEntry{neighbor_id, tentative_g, h_value});
            }
        }
    }
    
    PlannerResult result;
    result.success = false;
    return result;
}

double AStarPlanner::heuristic(const Graph& graph, int64_t current_id, int64_t goal_id) {
    const Node* current = graph.get_node(current_id);
    const Node* goal = graph.get_node(goal_id);
    
    return utils::haversine_distance(
        current->latitude, current->longitude,
        goal->latitude, goal->longitude
    );
}

PlannerResult AStarPlanner::reconstruct_path(const Graph& graph,
                                           const std::unordered_map<int64_t, NodeState>& node_states,
                                           int64_t start_id,
                                           int64_t goal_id) {
    std::vector<int64_t> path;
    int64_t current = goal_id;
    
    // Reconstruct path from goal to start
    while (current != -1) {
        path.push_back(current);
        auto it = node_states.find(current);
        if (it == node_states.end()) {
            PlannerResult result;
            result.success = false;
            return result;
        }
        current = it->second.parent_id;
    }
    
    // Verify path starts at start_id
    if (path.back() != start_id) {
        PlannerResult result;
        result.success = false;
        return result;
    }
    
    // Reverse to get start-to-goal order
    std::reverse(path.begin(), path.end());
    
    // Calculate total distance
    double total_distance = 0.0;
    for (size_t i = 1; i < path.size(); ++i) {
        const auto* node1 = graph.get_node(path[i-1]);
        const auto* node2 = graph.get_node(path[i]);
        total_distance += utils::haversine_distance(
            node1->latitude, node1->longitude,
            node2->latitude, node2->longitude
        );
    }
    
    PlannerResult result;
    result.success = true;
    result.path = std::move(path);
    result.total_distance = total_distance;
    result.num_nodes_explored = path.size();
    return result;
}

} // namespace route_planner