#include "route_planner/data_loader.hpp"
#include "route_planner/graph.hpp"
#include "route_planner/config.hpp"
#include "route_planner/planner_factory.hpp"
#include "route_planner/astar_planner.hpp"
#include "route_planner/utils.hpp"
#include <iostream>
#include <filesystem>
#include <cstdlib>
#include <iomanip>
#include <chrono>
#include <ctime>
#include <fstream>
#include <sstream>

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

struct ProgramArgs {
    std::string config_file;
    route_planner::Coordinates start;
    route_planner::Coordinates end;
    bool start_set = false;
    bool end_set = false;
};

bool parse_arguments(int argc, char* argv[], const std::filesystem::path& project_root, ProgramArgs& args) {
    // Default config file path
    args.config_file = (project_root / "config/default.yaml").string();
    
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        
        if (arg == "--help") {
            print_usage(argv[0]);
            return false;
        }
        else if (arg == "--config" && i + 1 < argc) {
            if (std::filesystem::path(argv[i+1]).is_absolute()) {
                args.config_file = argv[++i];
            } else {
                args.config_file = (project_root / argv[++i]).string();
            }
        }
        else if (arg == "--start-lat" && i + 1 < argc) {
            args.start.latitude = std::atof(argv[++i]);
            args.start_set = true;
        }
        else if (arg == "--start-lon" && i + 1 < argc) {
            args.start.longitude = std::atof(argv[++i]);
            args.start_set = true;
        }
        else if (arg == "--end-lat" && i + 1 < argc) {
            args.end.latitude = std::atof(argv[++i]);
            args.end_set = true;
        }
        else if (arg == "--end-lon" && i + 1 < argc) {
            args.end.longitude = std::atof(argv[++i]);
            args.end_set = true;
        }
        else {
            std::cerr << "Unknown argument: " << arg << std::endl;
            print_usage(argv[0]);
            return false;
        }
    }
    return true;
}

void save_route_to_csv(const route_planner::Graph& graph,
                       const route_planner::PlannerResult& result,
                       const route_planner::Coordinates& start,
                       const route_planner::Coordinates& end,
                       const std::filesystem::path& project_root) {
    if (result.path.size() < 2) return;
    
    // Create a unique filename based on start and end coordinates
    std::stringstream filename;
    filename << "route_" << result.cost_function << "_" << std::fixed << std::setprecision(6)
            << start.latitude << "_" << start.longitude << "_to_"
            << end.latitude << "_" << end.longitude;
    
    std::filesystem::path csv_path = project_root / "results" / (filename.str() + ".csv");
    std::ofstream csv_file(csv_path);
    
    if (csv_file.is_open()) {
        // Write metadata as comments for visualization
        csv_file << "# cost_function: " << result.cost_function << std::endl;
        csv_file << "# total_distance_km: " << (result.total_distance / 1000.0) << std::endl;
        csv_file << "# total_time_minutes: " << (result.total_time / 60.0) << std::endl;
        csv_file << "# path_nodes: " << result.path.size() << std::endl;
        
        // Write simple CSV header for path coordinates
        csv_file << "node_id,latitude,longitude" << std::endl;
        
        // Write just the path coordinates
        for (const auto& node_id : result.path) {
            const auto* node = graph.get_node(node_id);
            if (node) {
                csv_file << std::fixed << std::setprecision(6)
                        << node->id << ","
                        << node->latitude << ","
                        << node->longitude << std::endl;
            }
        }
        
        csv_file.close();
        std::cout << "Path saved to: " << csv_path << std::endl;
    } else {
        std::cerr << "Warning: Failed to save path to CSV file" << std::endl;
    }
}

void plan_and_save_route(const std::string& cost_func,
                            const route_planner::Config& config,
                            const route_planner::Graph& graph,
                            const route_planner::Coordinates& start,
                            const route_planner::Coordinates& end,
                            const std::filesystem::path& project_root,
                            double default_speed,
                            const route_planner::DataLoader& loader) {
    std::cout << "\n" << std::string(50, '=') << std::endl;
    std::cout << "Planning with cost function: " << cost_func << std::endl;
    std::cout << std::string(50, '=') << std::endl;
    
    // Create planner for this cost function
    auto planner = route_planner::PlannerFactory::create(config);
    auto astar = dynamic_cast<route_planner::AStarPlanner*>(planner.get());
    
    if (astar) {
        if (cost_func == "time") {
            astar->set_cost_function(route_planner::CostFunction::TIME, default_speed);
        } else {
            astar->set_cost_function(route_planner::CostFunction::DISTANCE, default_speed);
        }
        // Set config for highway speed mapping
        astar->set_config(&config);
    }
    
    std::cout << "Using planner: " << planner->get_name() << std::endl;

    // Plan route
    std::cout << "\nPlanning route..." << std::endl;
    auto start_time = std::chrono::high_resolution_clock::now();
    
    auto result = planner->plan(graph, start, end);

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    
    if (!result.success) {
        std::cerr << "Failed to find path!" << std::endl;
        return;
    }
    
    std::cout << "Path found! (" << duration.count() << "ms)" << std::endl;
    
    // Print detailed planner statistics
    std::cout << "\n=== Planning Statistics ===" << std::endl;
    std::cout << "Algorithm: " << planner->get_name() << std::endl;
    std::cout << "Planning time: " << duration.count() << " ms" << std::endl;
    std::cout << "Nodes explored: " << result.num_nodes_explored << " / " << loader.get_nodes().size() << std::endl;
    std::cout << "Path length: " << result.path.size() << " nodes" << std::endl;

    // Display total distance (already calculated by planner)
    double distance_km = result.total_distance / 1000.0;  // Convert from meters to km
    std::cout << "Total distance: " << std::fixed << std::setprecision(2) 
              << distance_km << " km (" << distance_km * 0.621371 << " miles)" << std::endl;
    
    // Display total travel time (already calculated by planner)
    double time_minutes = result.total_time / 60.0;  // Convert from seconds to minutes
    std::cout << "Total travel time: " << std::fixed << std::setprecision(1) 
              << time_minutes << " minutes" << std::endl;
    
    // Performance metrics
    double nodes_per_ms = static_cast<double>(result.num_nodes_explored) / duration.count();
    std::cout << "Search speed: " << std::fixed << std::setprecision(2) 
              << nodes_per_ms << " nodes/ms" << std::endl;

    // Save path to CSV file
    save_route_to_csv(graph, result, start, end, project_root);
}

int main(int argc, char* argv[]) {
    // Find project root directory (one level up from bin)
    std::filesystem::path exe_path = std::filesystem::canonical("/proc/self/exe");
    std::filesystem::path project_root = exe_path.parent_path().parent_path();
    
    // Parse command line arguments
    ProgramArgs args;
    if (!parse_arguments(argc, argv, project_root, args)) {
        return 0;  // parse_arguments handles help display and error messages
    }
    
    // Load configuration
    route_planner::Config config;
    if (!config.load(args.config_file)) {
        std::cerr << "Failed to load configuration from " << args.config_file << std::endl;
        return 1;
    }
    
    // Use default coordinates if not provided
    if (!args.start_set) {
        args.start = config.get_default_start();
    }
    if (!args.end_set) {
        args.end = config.get_default_end();
    }

    // Load data
    route_planner::DataLoader loader;
    std::string nodes_file = std::filesystem::path(config.get_nodes_file()).is_absolute() ? 
        config.get_nodes_file() : (project_root / config.get_nodes_file()).string();
    
    std::string edges_file = std::filesystem::path(config.get_edges_file()).is_absolute() ?
        config.get_edges_file() : (project_root / config.get_edges_file()).string();
    
    if (!loader.load(nodes_file, edges_file, &config)) {
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
    std::cout << "Start: (" << args.start.latitude << ", " << args.start.longitude << ")" << std::endl;
    std::cout << "End  : (" << args.end.latitude << ", " << args.end.longitude << ")" << std::endl;
    
    // Calculate straight-line distance for comparison
    double straight_line_dist = route_planner::utils::haversine_distance(
        args.start.latitude, args.start.longitude, args.end.latitude, args.end.longitude);
    std::cout << "Straight-line distance: " << std::fixed << std::setprecision(2) 
              << straight_line_dist << " km" << std::endl;

    // Get cost functions from config
    std::vector<std::string> cost_functions;
    try {
        auto cost_func_array = config.get<std::vector<std::string>>("planner.cost_functions", std::vector<std::string>{"distance"});
        cost_functions = cost_func_array;
    } catch (...) {
        std::string single_func = config.get<std::string>("planner.cost_functions", "distance");
        cost_functions = {single_func};
    }
    
    double default_speed = config.get<double>("planner.default_speed_mph", 25.0);
    
    // Plan for each cost function
    for (const auto& cost_func : cost_functions) {
        plan_and_save_route(cost_func, config, graph, args.start, args.end, 
                              project_root, default_speed, loader);
    }
    
    return 0;
}