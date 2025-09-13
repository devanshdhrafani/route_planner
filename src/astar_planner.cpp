#include "route_planner/astar_planner.hpp"
#include "route_planner/utils.hpp"
#include <queue>
#include <unordered_map>
#include <limits>
#include <algorithm>

namespace route_planner {

void AStarPlanner::set_cost_function(CostFunction cost_func, double default_speed_mph) {
    cost_function_ = cost_func;
    default_speed_mph_ = default_speed_mph;
}

void AStarPlanner::set_config(const Config* config) {
    config_ = config;
}

std::string AStarPlanner::get_name() const {
    switch (cost_function_) {
        case CostFunction::DISTANCE:
            return "A* (Distance)";
        case CostFunction::TIME:
            return "A* (Time)";
        default:
            return "A*";
    }
}

double AStarPlanner::calculate_edge_cost(const Edge& edge) const {
    switch (cost_function_) {
        case CostFunction::DISTANCE:
            return edge.distance / 1000.0;  // Convert meters to km
            
        case CostFunction::TIME: {
            // Convert distance from meters to miles for consistent calculation
            double distance_miles = edge.distance / 1609.34;
            
            // Determine speed in mph
            double speed_mph = default_speed_mph_;
            
            // First, try to use explicit speed limit
            if (edge.max_speed.has_value()) {
                double max_speed = edge.max_speed.value();
                // Parse speed string if needed and detect units
                if (max_speed > 80) {
                    // Assume km/h, convert to mph
                    speed_mph = max_speed * 0.621371;
                } else {
                    // Assume already in mph
                    speed_mph = max_speed;
                }
            }
            // If no explicit speed limit, try highway type-based speed from config
            else if (config_ && edge.highway_type.has_value()) {
                speed_mph = config_->get_highway_speed(edge.highway_type.value(), default_speed_mph_);
            }
            
            // Calculate time in seconds
            double time_hours = distance_miles / speed_mph;
            return time_hours * 3600.0;  // Convert to seconds
        }
        
        default:
            return edge.distance / 1000.0;
    }
}

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
            auto final_result = reconstruct_path(graph, node_states, start_id, goal_id);
            final_result.num_nodes_explored = nodes_explored;
            return final_result;
        }
        
        // Skip if we've found a better path to this node
        if (current.g_value > node_states[current_id].g_score) {
            continue;
        }
        
        // Explore neighbors
        for (const auto& edge_ptr : graph.get_outgoing_edges(current_id)) {
            // Determine the neighbor node ID based on edge direction
            int64_t neighbor_id;
            if (edge_ptr->source == current_id) {
                neighbor_id = edge_ptr->target;
            } else if (!edge_ptr->oneway && edge_ptr->target == current_id) {
                neighbor_id = edge_ptr->source;
            } else {
                continue;  // Skip if we can't traverse this edge
            }
            
            double tentative_g = node_states[current_id].g_score + calculate_edge_cost(*edge_ptr);
            
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
    
    double distance_km = utils::haversine_distance(
        current->latitude, current->longitude,
        goal->latitude, goal->longitude
    );
    
    switch (cost_function_) {
        case CostFunction::DISTANCE:
            return distance_km;
            
        case CostFunction::TIME: {
            // For time heuristic, assume we can travel at highway speed
            double highway_speed_mph = std::max(default_speed_mph_, 55.0);  // At least 55 mph for heuristic
            double distance_miles = distance_km * 0.621371;
            double time_hours = distance_miles / highway_speed_mph;
            return time_hours * 3600.0;  // Convert to seconds
        }
        
        default:
            return distance_km;
    }
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
    
    // Calculate total distance and time using actual edge data
    double total_distance = 0.0;
    double total_time = 0.0;
    for (size_t i = 1; i < path.size(); ++i) {
        int64_t from_id = path[i-1];
        int64_t to_id = path[i];
        bool found_edge = false;
        
        // Find the edge between these nodes
        for (const auto* edge : graph.get_outgoing_edges(from_id)) {
            if ((edge->source == from_id && edge->target == to_id) ||
                (!edge->oneway && edge->target == from_id && edge->source == to_id)) {
                
                total_distance += edge->distance;
                
                // Calculate time for this edge using same logic as calculate_edge_cost
                double distance_miles = edge->distance / 1609.34;
                double speed_mph = default_speed_mph_;
                
                // First, try to use explicit speed limit
                if (edge->max_speed.has_value()) {
                    double max_speed = edge->max_speed.value();
                    // Parse speed string if needed and detect units
                    if (max_speed > 80) {
                        // Assume km/h, convert to mph
                        speed_mph = max_speed * 0.621371;
                    } else {
                        // Assume already in mph
                        speed_mph = max_speed;
                    }
                }
                // If no explicit speed limit, try highway type-based speed from config
                else if (config_ && edge->highway_type.has_value()) {
                    speed_mph = config_->get_highway_speed(edge->highway_type.value(), default_speed_mph_);
                }
                
                double time_hours = distance_miles / speed_mph;
                total_time += time_hours * 3600.0;  // Convert to seconds
                
                found_edge = true;
                break;
            }
        }
        
        if (!found_edge) {
            // This should never happen if the path is valid
            PlannerResult result;
            result.success = false;
            return result;
        }
    }
    
    PlannerResult result;
    result.success = true;
    result.path = std::move(path);
    result.total_distance = total_distance;
    result.total_time = total_time;
    result.num_nodes_explored = 0;  // Will be set by the calling function
    result.cost_function = (cost_function_ == CostFunction::DISTANCE) ? "distance" : "time";
    return result;
}

} // namespace route_planner