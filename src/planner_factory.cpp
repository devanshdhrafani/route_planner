#include "route_planner/planner_factory.hpp"
#include "route_planner/astar_planner.hpp"
#include <stdexcept>

namespace route_planner {

PlannerPtr PlannerFactory::create(const std::string& planner_type) {
    if (planner_type == "astar") {
        return std::make_unique<AStarPlanner>();
    }
    // Add more planner types here as they are implemented
    // else if (planner_type == "dijkstra") {
    //     return std::make_unique<DijkstraPlanner>();
    // }
    
    throw std::invalid_argument("Unknown planner type: " + planner_type);
}

PlannerPtr PlannerFactory::create(const Config& config) {
    // Get planner type from config
    std::string planner_type = config.get<std::string>("planner.type", "astar");
    auto planner = create(planner_type);
    
    // Configure A* specific settings
    if (planner_type == "astar") {
        auto astar = dynamic_cast<AStarPlanner*>(planner.get());
        if (astar) {
            double default_speed = config.get<double>("planner.default_speed_mph", 25.0);
            astar->set_cost_function(CostFunction::DISTANCE, default_speed);  // Default to distance
        }
    }
    
    return planner;
}

} // namespace route_planner