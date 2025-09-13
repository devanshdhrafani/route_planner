#pragma once

#include "route_planner/types.hpp"
#include "route_planner/graph.hpp"
#include <vector>
#include <memory>

namespace route_planner {

/**
 * Result of a path planning operation.
 */
struct PlannerResult {
    bool success{false};                   // Whether a path was found
    std::vector<int64_t> path;            // Sequence of node IDs in the path
    double total_distance{0.0};           // Total path length in meters
    int num_nodes_explored{0};            // Number of nodes explored during search
};

/**
 * Abstract base class for path planners.
 * This interface allows for different planning algorithms to be used
 * interchangeably (Strategy pattern).
 */
class Planner {
public:
    virtual ~Planner() = default;

    /**
     * Plan a path between start and end coordinates.
     * 
     * @param graph The road network graph
     * @param start_coord Starting coordinates
     * @param end_coord Target coordinates
     * @return PlannerResult containing the path if found
     */
    virtual PlannerResult plan(
        const Graph& graph,
        const Coordinates& start_coord,
        const Coordinates& end_coord) = 0;

    /**
     * Get the name of this planner implementation.
     */
    virtual std::string get_name() const = 0;

protected:
    /**
     * Find the nearest node in the graph to given coordinates.
     * 
     * @param graph The road network graph
     * @param coord The coordinates to find nearest node for
     * @return ID of the nearest node, or -1 if no node found
     */
    static int64_t find_nearest_node(const Graph& graph, const Coordinates& coord);
    
    // Allow Planner to access Graph's private members
    friend class Graph;
};

// Smart pointer type for planners
using PlannerPtr = std::unique_ptr<Planner>;

} // namespace route_planner