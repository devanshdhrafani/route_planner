#include "route_planner/config.hpp"
#include <filesystem>
#include <iostream>

namespace route_planner {

bool Config::load(const std::string& config_file) {
    try {
        // Load YAML file
        YAML::Node config = YAML::LoadFile(config_file);
        
        // Get data paths
        if (!config["data"]) {
            std::cerr << "Error: Missing 'data' section in config file" << std::endl;
            return false;
        }

        const auto& data = config["data"];
        
        // Get nodes file path
        if (!data["nodes_file"]) {
            std::cerr << "Error: Missing 'nodes_file' in data section" << std::endl;
            return false;
        }
        nodes_file_ = data["nodes_file"].as<std::string>();

        // Get edges file path
        if (!data["edges_file"]) {
            std::cerr << "Error: Missing 'edges_file' in data section" << std::endl;
            return false;
        }
        edges_file_ = data["edges_file"].as<std::string>();
        
        // Load default coordinates if available
        if (config["defaults"]) {
            const auto& defaults = config["defaults"];
            
            if (defaults["start"] && defaults["start"]["lat"] && defaults["start"]["lon"]) {
                default_start_.latitude = defaults["start"]["lat"].as<double>();
                default_start_.longitude = defaults["start"]["lon"].as<double>();
            }
            
            if (defaults["end"] && defaults["end"]["lat"] && defaults["end"]["lon"]) {
                default_end_.latitude = defaults["end"]["lat"].as<double>();
                default_end_.longitude = defaults["end"]["lon"].as<double>();
            }
        }
        
        // Make paths relative to the config file location
        std::filesystem::path config_dir = std::filesystem::path(config_file).parent_path();
        nodes_file_ = (config_dir / nodes_file_).lexically_normal().string();
        edges_file_ = (config_dir / edges_file_).lexically_normal().string();

        return true;
    }
    catch (const YAML::Exception& e) {
        std::cerr << "Error parsing config file: " << e.what() << std::endl;
        return false;
    }
    catch (const std::exception& e) {
        std::cerr << "Error loading config: " << e.what() << std::endl;
        return false;
    }
}

} // namespace route_planner