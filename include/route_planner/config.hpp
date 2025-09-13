#pragma once

#include <string>
#include <yaml-cpp/yaml.h>

namespace route_planner {

/**
 * Holds configuration settings for the route planner.
 */
class Config {
public:
    /**
     * Load configuration from a YAML file.
     * 
     * @param config_file Path to the YAML configuration file
     * @return true if loading was successful
     */
    bool load(const std::string& config_file);

    /**
     * Get the path to the nodes data file.
     */
    const std::string& get_nodes_file() const { return nodes_file_; }

    /**
     * Get the path to the edges data file.
     */
    const std::string& get_edges_file() const { return edges_file_; }

private:
    std::string nodes_file_;
    std::string edges_file_;
};

} // namespace route_planner