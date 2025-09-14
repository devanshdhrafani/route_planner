#include "route_planner/data_loader.hpp"
#include <fstream>
#include <iostream>

namespace route_planner {

bool DataLoader::load(const std::string& nodes_file, const std::string& edges_file, const Config* config) {
    // Store config for edge filtering
    config_ = config;
    
    // Load traffic configuration if config is provided
    if (config_) {
        traffic_config_ = config_->get_traffic_config();
    }
    
    // Clear existing data
    nodes_.clear();
    edges_.clear();
    
    try {
        // Load nodes
        std::ifstream nodes_stream(nodes_file);
        if (!nodes_stream.is_open()) {
            std::cerr << "Could not open nodes file: " << nodes_file << std::endl;
            return false;
        }
        nlohmann::json nodes_json;
        nodes_stream >> nodes_json;
        
        if (!parse_nodes(nodes_json)) {
            std::cerr << "Failed to parse nodes data" << std::endl;
            return false;
        }
        
        // Load edges
        std::ifstream edges_stream(edges_file);
        if (!edges_stream.is_open()) {
            std::cerr << "Could not open edges file: " << edges_file << std::endl;
            return false;
        }
        nlohmann::json edges_json;
        edges_stream >> edges_json;
        
        if (!parse_edges(edges_json)) {
            std::cerr << "Failed to parse edges data" << std::endl;
            return false;
        }
        
        return true;
    }
    catch (const std::exception& e) {
        std::cerr << "Error loading data: " << e.what() << std::endl;
        return false;
    }
}

bool DataLoader::parse_nodes(const nlohmann::json& json) {
    try {
        for (const auto& [id_str, node_data] : json.items()) {
            // Convert string ID to integer
            int64_t id = std::stoll(id_str);
            
            // Extract required fields
            double lat = node_data["lat"].get<double>();
            double lon = node_data["lon"].get<double>();
            
            // Create and store the node
            nodes_.emplace(id, Node(id, lat, lon));
        }
        return true;
    }
    catch (const std::exception& e) {
        std::cerr << "Error parsing nodes: " << e.what() << std::endl;
        return false;
    }
}

bool DataLoader::parse_edges(const nlohmann::json& json) {
    try {
        edges_.reserve(json.size());  // Pre-allocate for efficiency (may be less after filtering)
        
        int skipped_edges = 0;
        int traffic_modified_edges = 0;
        
        for (const auto& edge_data : json) {
            // Extract required fields
            int64_t source = edge_data["u"].get<int64_t>();
            int64_t target = edge_data["v"].get<int64_t>();
            double distance = edge_data["distance"].get<double>();
            
            // Create edge with required fields
            Edge edge(source, target, distance);
            
            // Add optional fields if they exist
            if (edge_data.contains("maxspeed") && !edge_data["maxspeed"].is_null()) {
                // Store speed limit as a string since it might include units
                if (edge_data["maxspeed"].is_string()) {
                    std::string speed_str = edge_data["maxspeed"].get<std::string>();
                    try {
                        // Try to extract the numeric part
                        size_t end_pos;
                        double speed = std::stod(speed_str, &end_pos);
                        edge.max_speed = speed;
                    } catch (...) {
                        // If parsing fails, don't set the speed
                    }
                } else if (edge_data["maxspeed"].is_number()) {
                    edge.max_speed = edge_data["maxspeed"].get<double>();
                }
            }
            
            if (edge_data.contains("highway") && !edge_data["highway"].is_null()) {
                edge.highway_type = edge_data["highway"].get<std::string>();
            }
            
            // Check if this edge should be included based on highway type
            if (!should_include_edge(edge.highway_type)) {
                skipped_edges++;
                continue;  // Skip this edge
            }
            
            if (edge_data.contains("name") && !edge_data["name"].is_null()) {
                edge.name = edge_data["name"].get<std::string>();
            }
            
            if (edge_data.contains("oneway") && !edge_data["oneway"].is_null()) {
                // Handle oneway field that might be string "yes"/"no" or boolean
                if (edge_data["oneway"].is_string()) {
                    edge.oneway = (edge_data["oneway"].get<std::string>() == "yes");
                } else if (edge_data["oneway"].is_boolean()) {
                    edge.oneway = edge_data["oneway"].get<bool>();
                }
            }
            
            // Apply traffic modifications to the edge
            double original_speed = edge.max_speed.value_or(0.0);
            apply_traffic_modifications(edge);
            if (original_speed != edge.max_speed.value_or(0.0)) {
                traffic_modified_edges++;
            }
            
            edges_.push_back(std::move(edge));
        }
        
        if (skipped_edges > 0) {
            std::cout << "Filtered out " << skipped_edges << " non-car edges" << std::endl;
        }
        
        if (traffic_modified_edges > 0) {
            std::cout << "Applied traffic modifications to " << traffic_modified_edges << " edges" << std::endl;
        }
        
        return true;
    }
    catch (const std::exception& e) {
        std::cerr << "Error parsing edges: " << e.what() << std::endl;
        return false;
    }
}

bool DataLoader::should_include_edge(const std::optional<std::string>& highway_type) const {
    // If no config is provided, include all edges
    if (!config_) {
        return true;
    }
    
    // If edge has no highway type, include it (use default speed)
    if (!highway_type.has_value()) {
        return true;
    }
    
    // Check if this highway type has a speed of 0 (meaning it should be excluded)
    double speed = config_->get_highway_speed(highway_type.value(), -1.0);  // Use -1 as sentinel value
    
    // If speed is 0, exclude this edge (not for cars)
    if (speed == 0.0) {
        return false;
    }
    
    // Include all other edges
    return true;
}

void DataLoader::apply_traffic_modifications(Edge& edge) const {
    // Skip if no config
    if (!config_) {
        return;
    }
    
    // Check for specific edge modifications
    std::string edge_key = std::to_string(edge.source) + "-" + std::to_string(edge.target);
    auto edge_mod_it = traffic_config_.edge_modifications.find(edge_key);
    
    // If no edge modification found, skip processing
    if (edge_mod_it == traffic_config_.edge_modifications.end()) {
        return;
    }
    
    // Get current speed (either explicit or from highway type)
    double current_speed = 25.0;  // Default fallback
    if (edge.max_speed.has_value()) {
        current_speed = edge.max_speed.value();
        // Convert km/h to mph if needed (assume > 80 is km/h)
        if (current_speed > 80) {
            current_speed *= 0.621371;
        }
    } else if (edge.highway_type.has_value()) {
        current_speed = config_->get_highway_speed(edge.highway_type.value(), 25.0);
    }
    
    // Apply the specific edge modification
    const auto& modification = edge_mod_it->second;
    double modified_speed;
    
    if (modification.type == TrafficModification::SPEED_OVERRIDE) {
        modified_speed = modification.value;
    } else if (modification.type == TrafficModification::MULTIPLIER) {
        modified_speed = current_speed * modification.value;
    } else {
        return;  // Unknown modification type
    }
    
    // Ensure minimum speed (prevent zero or negative speeds)
    modified_speed = std::max(modified_speed, 1.0);
    
    // Update the edge's max_speed
    edge.max_speed = modified_speed;
}

} // namespace route_planner