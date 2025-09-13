#include "route_planner/data_loader.hpp"
#include "route_planner/graph.hpp"
#include "route_planner/config.hpp"
#include <iostream>
#include <filesystem>
#include <cstdlib>
#include <iomanip>

void print_usage(const char* program_name) {
    std::cout << "Usage: " << program_name << " [options]\n"
              << "Options:\n"
              << "  --config <file>       Configuration file (default: config/default.yaml)\n"
              << "  --start-lat <value>   Start point latitude\n"
              << "  --start-lon <value>   Start point longitude\n"
              << "  --end-lat <value>     End point latitude\n"
              << "  --end-lon <value>     End point longitude\n"
              << "  --help               Show this help message\n"
              << std::endl;
}

int main(int argc, char* argv[]) {
    // Default config file path
    std::string config_file = "config/default.yaml";
    
    // Parse command line arguments
    route_planner::Coordinates start, end;
    bool start_set = false, end_set = false;
    
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        
        if (arg == "--help") {
            print_usage(argv[0]);
            return 0;
        }
        else if (arg == "--config" && i + 1 < argc) {
            config_file = argv[++i];
        }
        else if (arg == "--start-lat" && i + 1 < argc) {
            start.latitude = std::atof(argv[++i]);
            start_set = true;
        }
        else if (arg == "--start-lon" && i + 1 < argc) {
            start.longitude = std::atof(argv[++i]);
            start_set = true;
        }
        else if (arg == "--end-lat" && i + 1 < argc) {
            end.latitude = std::atof(argv[++i]);
            end_set = true;
        }
        else if (arg == "--end-lon" && i + 1 < argc) {
            end.longitude = std::atof(argv[++i]);
            end_set = true;
        }
        else {
            std::cerr << "Unknown argument: " << arg << std::endl;
            print_usage(argv[0]);
            return 1;
        }
    }
    
    // Load configuration
    route_planner::Config config;
    if (!config.load(config_file)) {
        std::cerr << "Failed to load configuration from " << config_file << std::endl;
        return 1;
    }
    
    // Use default coordinates if not provided
    if (!start_set) {
        start = config.get_default_start();
    }
    if (!end_set) {
        end = config.get_default_end();
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
    
    // Print route planning request
    std::cout << "\nRoute Planning Request:" << std::endl;
    std::cout << std::fixed << std::setprecision(6);
    std::cout << "Start: (" << start.latitude << ", " << start.longitude << ")" << std::endl;
    std::cout << "End  : (" << end.latitude << ", " << end.longitude << ")" << std::endl;
    
    return 0;
}