#include "route_planner/config.hpp"
#include <filesystem>
#include <iostream>

namespace route_planner {

bool Config::load(const std::string& config_file) {
    try {
        // Load YAML file
        config_ = YAML::LoadFile(config_file);
        
        // Get data paths
        if (!config_["data"]) {
            std::cerr << "Error: Missing 'data' section in config file" << std::endl;
            return false;
        }

        const auto& data = config_["data"];
        
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
        if (config_["defaults"]) {
            const auto& defaults = config_["defaults"];
            
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

std::unordered_map<std::string, double> Config::get_highway_speeds() const {
    std::unordered_map<std::string, double> highway_speeds;
    
    try {
        if (config_["data"] && config_["data"]["highway_speeds"]) {
            const auto& speeds_node = config_["data"]["highway_speeds"];
            
            for (const auto& pair : speeds_node) {
                std::string highway_type = pair.first.as<std::string>();
                double speed = pair.second.as<double>();
                highway_speeds[highway_type] = speed;
            }
        }
    }
    catch (const YAML::Exception& e) {
        std::cerr << "Warning: Error loading highway speeds from config: " << e.what() << std::endl;
    }
    
    return highway_speeds;
}

double Config::get_highway_speed(const std::string& highway_type, double fallback_speed) const {
    try {
        if (config_["data"] && config_["data"]["highway_speeds"] && 
            config_["data"]["highway_speeds"][highway_type]) {
            return config_["data"]["highway_speeds"][highway_type].as<double>();
        }
    }
    catch (const YAML::Exception&) {
        // Fall through to return fallback speed
    }
    
    return fallback_speed;
}

TrafficConfig Config::get_traffic_config() const {
    TrafficConfig traffic_config;
    
    try {
        if (!config_["traffic"]) {
            // No traffic section, return default config
            return traffic_config;
        }
        
        const auto& traffic = config_["traffic"];
        
        // Edge-specific modifications
        if (traffic["edges"]) {
            const auto& edges = traffic["edges"];
            for (const auto& edge_pair : edges) {
                std::string edge_key = edge_pair.first.as<std::string>();  // "source_id-target_id"
                const auto& modification = edge_pair.second;
                
                if (modification["type"] && modification["value"]) {
                    std::string type_str = modification["type"].as<std::string>();
                    double value = modification["value"].as<double>();
                    
                    TrafficModification::Type type;
                    if (type_str == "speed_override") {
                        type = TrafficModification::SPEED_OVERRIDE;
                    } else if (type_str == "multiplier") {
                        type = TrafficModification::MULTIPLIER;
                    } else {
                        std::cerr << "Warning: Unknown traffic modification type: " << type_str << std::endl;
                        continue;
                    }
                    
                    traffic_config.edge_modifications.emplace(edge_key, TrafficModification(type, value));
                }
            }
        }
        
    }
    catch (const YAML::Exception& e) {
        std::cerr << "Warning: Error loading traffic config: " << e.what() << std::endl;
    }
    
    return traffic_config;
}

} // namespace route_planner