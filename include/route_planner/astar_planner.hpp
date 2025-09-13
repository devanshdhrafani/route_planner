#pragma once

#include "route_planner/planner.hpp"
#include <queue>
#include <unordered_map>
#include <limits>

namespace route_planner {

/**
 * A* path planning algorithm implementation.
 */
class AStarPlanner : public Planner {
public:
    PlannerResult plan(
        const Graph& graph,
        const Coordinates& start_coord,
        const Coordinates& end_coord) override;
    
    std::string get_name() const override { return "A*"; }

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