#pragma once

#include "types.hpp"
#include <nlohmann/json.hpp>
#include <string>
#include <vector>
#include <unordered_map>

namespace route_planner {

/**
 * Loads and parses the road network data from JSON files.
 */
class DataLoader {
public:
    /**
     * Load nodes and edges from JSON files.
     * 
     * @param nodes_file Path to the nodes JSON file
     * @param edges_file Path to the edges JSON file
     * @return True if loading was successful, false otherwise
     */
    bool load(const std::string& nodes_file, const std::string& edges_file);
    
    /**
     * Get the loaded nodes.
     * @return Map of node ID to Node object
     */
    const std::unordered_map<int64_t, Node>& get_nodes() const { return nodes_; }
    
    /**
     * Get the loaded edges.
     * @return Vector of Edge objects
     */
    const std::vector<Edge>& get_edges() const { return edges_; }

private:
    std::unordered_map<int64_t, Node> nodes_;
    std::vector<Edge> edges_;
    
    /**
     * Parse nodes from JSON data.
     * @param json JSON object containing node data
     * @return True if parsing was successful
     */
    bool parse_nodes(const nlohmann::json& json);
    
    /**
     * Parse edges from JSON data.
     * @param json JSON object containing edge data
     * @return True if parsing was successful
     */
    bool parse_edges(const nlohmann::json& json);
};

} // namespace route_planner