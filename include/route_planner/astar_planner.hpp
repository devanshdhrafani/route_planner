#pragma once

#include "route_planner/planner.hpp"
#include "route_planner/config.hpp"
#include <queue>
#include <unordered_map>
#include <limits>

namespace route_planner {

/**
 * Cost function type for A* planning
 */
enum class CostFunction {
    DISTANCE,  // Cost based on distance (km)
    TIME       // Cost based on travel time (seconds)
};

/**
 * A* path planning algorithm implementation.
 */
class AStarPlanner : public Planner {
public:
    /**
     * Set the cost function and parameters for planning
     */
    void set_cost_function(CostFunction cost_func, double default_speed_mph = 25.0);
    
    /**
     * Set the config for highway speed mapping
     */
    void set_config(const Config* config);
    
    PlannerResult plan(
        const Graph& graph,
        const Coordinates& start_coord,
        const Coordinates& end_coord) override;
    
    std::string get_name() const override;

private:
    CostFunction cost_function_{CostFunction::DISTANCE};
    double default_speed_mph_{25.0};  // Default speed when no max_speed available
    const Config* config_{nullptr};  // Config for highway speed mapping

private:
    // Internal node state for A* search
    struct NodeState {
        double g_score{std::numeric_limits<double>::infinity()};  // Cost from start
        int64_t parent_id{-1};                                   // Parent node
    };
    
    // Priority queue entry
    struct QueueEntry {
        int64_t node_id;
        double g_value;
        double f_value;  // f = g + h
        
        QueueEntry(int64_t id, double g, double h) 
            : node_id(id), g_value(g), f_value(g + h) {}
            
        // For priority queue - higher f_value = lower priority
        bool operator<(const QueueEntry& other) const {
            return f_value > other.f_value;
        }
    };
    
    /**
     * Calculate edge cost based on the selected cost function
     */
    double calculate_edge_cost(const Edge& edge) const;
    
    /**
     * Calculate heuristic estimate (h-value) between nodes.
     */
    double heuristic(const Graph& graph, int64_t current_id, int64_t goal_id);
    
    /**
     * Reconstruct path from search result.
     */
    PlannerResult reconstruct_path(
        const Graph& graph,
        const std::unordered_map<int64_t, NodeState>& nodes,
        int64_t start_id,
        int64_t goal_id);
};

} // namespace route_planner