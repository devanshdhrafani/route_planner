#include "route_planner/data_loader.hpp"
#include "route_planner/graph.hpp"
#include <iostream>

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: " << argv[0] << " <nodes_file> <edges_file>" << std::endl;
        return 1;
    }
    
    route_planner::DataLoader loader;
    if (!loader.load(argv[1], argv[2])) {
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