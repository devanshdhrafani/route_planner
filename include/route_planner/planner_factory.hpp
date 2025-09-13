#pragma once

#include "route_planner/planner.hpp"
#include "route_planner/config.hpp"
#include <memory>
#include <string>

namespace route_planner {

class PlannerFactory {
public:
    // Creates a planner based on the type specified in config
    static PlannerPtr create(const std::string& planner_type);
    
    // Creates a planner based on the planner configuration
    static PlannerPtr create(const Config& config);

private:
    // Prevent instantiation
    PlannerFactory() = delete;
};

} // namespace route_planner