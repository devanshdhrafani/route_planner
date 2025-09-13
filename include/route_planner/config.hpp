#pragma once

#include <string>
#include <unordered_map>
#include <yaml-cpp/yaml.h>
#include "types.hpp"

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

    /**
     * Get default start coordinates.
     */
    const Coordinates& get_default_start() const { return default_start_; }

    /**
     * Get default end coordinates.
     */
    const Coordinates& get_default_end() const { return default_end_; }

    /**
     * Get a configuration value of specified type with an optional default.
     * 
     * @param key Dot-separated path to the config value (e.g., "planner.type")
     * @param default_value Value to return if key doesn't exist
     * @return The config value of type T
     */
    template<typename T>
    T get(const std::string& key, const T& default_value) const {
        try {
            YAML::Node node = config_;
            size_t start = 0;
            size_t end = key.find('.');
            
            // Navigate through the nested keys
            while (end != std::string::npos) {
                std::string part = key.substr(start, end - start);
                if (!node[part]) {
                    return default_value;
                }
                node = node[part];
                start = end + 1;
                end = key.find('.', start);
            }
            
            // Get final key part
            std::string final_key = key.substr(start);
            if (!node[final_key]) {
                return default_value;
            }
            
            return node[final_key].as<T>();
        }
        catch (const YAML::Exception&) {
            return default_value;
        }
    }

    /**
     * Get highway speed mapping from config.
     * Returns a map of highway type to speed in mph.
     */
    std::unordered_map<std::string, double> get_highway_speeds() const;

    /**
     * Get speed for a specific highway type.
     * 
     * @param highway_type The highway type (e.g., "primary", "residential")
     * @param fallback_speed Speed to return if highway type not found
     * @return Speed in mph
     */
    double get_highway_speed(const std::string& highway_type, double fallback_speed = 25.0) const;

private:
    YAML::Node config_;
    std::string nodes_file_;
    std::string edges_file_;
    Coordinates default_start_;
    Coordinates default_end_;
};

} // namespace route_planner