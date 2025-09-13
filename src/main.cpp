#include "route_planner/data_loader.hpp"
#include "route_planner/graph.hpp"
#include "route_planner/config.hpp"
#include <iostream>
#include <filesystem>

int main(int argc, char* argv[]) {
    // Default config file path
    std::string config_file = "config/default.yaml";
    
    // Allow overriding config file via command line
    if (argc > 1) {
        config_file = argv[1];
    }
    
    // Load configuration
    route_planner::Config config;
    if (!config.load(config_file)) {
        std::cerr << "Failed to load configuration from " << config_file << std::endl;
        return 1;
    }
    
    route_planner::DataLoader loader;
    if (!loader.load(config.get_nodes_file(), config.get_edges_file())) {
        std::cerr << "Failed to load data" << std::endl;
        return 1;
    }
    
    // Initialize the graph
    route_planner::Graph graph;
    graph.init(
        std::unordered_map<int64_t, route_planner::Node>(loader.get_nodes()),
        std::vector<route_planner::Edge>(loader.get_edges())
    );
    
    // Print some statistics
    std::cout << "Successfully loaded road network:" << std::endl;
    std::cout << "Nodes: " << loader.get_nodes().size() << std::endl;
    std::cout << "Edges: " << loader.get_edges().size() << std::endl;
    
    return 0;
}