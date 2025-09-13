#include "route_planner/data_loader.hpp"
#include <fstream>
#include <iostream>

namespace route_planner {

bool DataLoader::load(const std::string& nodes_file, const std::string& edges_file) {
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
        edges_.reserve(json.size());  // Pre-allocate for efficiency
        
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
            
            edges_.push_back(std::move(edge));
        }
        return true;
    }
    catch (const std::exception& e) {
        std::cerr << "Error parsing edges: " << e.what() << std::endl;
        return false;
    }
}

} // namespace route_planner