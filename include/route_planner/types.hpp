#pragma once

#include <string>
#include <optional>
#include <unordered_map>
#include <vector>

namespace route_planner {

/**
 * Represents a geographical coordinate pair.
 */
struct Coordinates {
    double latitude;     // Latitude in degrees
    double longitude;    // Longitude in degrees
    
    Coordinates(double lat = 0.0, double lon = 0.0)
        : latitude(lat), longitude(lon) {}
};

/**
 * Traffic modification for a specific edge.
 */
struct TrafficModification {
    enum Type {
        SPEED_OVERRIDE,  // Set absolute speed
        MULTIPLIER      // Multiply existing speed
    };
    
    Type type;
    double value;  // New speed (mph) or multiplier factor
    
    TrafficModification(Type t, double v) : type(t), value(v) {}
};

/**
 * Complete traffic configuration.
 */
struct TrafficConfig {
    std::unordered_map<std::string, TrafficModification> edge_modifications;  // Key: "source_id-target_id"
};

/**
 * Represents a node (intersection) in the road network.
 */
struct Node {
    int64_t id;          // Unique identifier for the node
    double latitude;     // Latitude in degrees
    double longitude;    // Longitude in degrees
    
    // Constructor for easy initialization
    Node(int64_t id_, double lat_, double lon_)
        : id(id_), latitude(lat_), longitude(lon_) {}
};

/**
 * Represents an edge (road segment) in the road network.
 */
struct Edge {
    int64_t source;      // Source node ID
    int64_t target;      // Target node ID
    double distance;     // Distance in meters
    
    // Optional properties from OSM
    std::optional<double> max_speed;          // Speed limit in km/h
    std::optional<std::string> highway_type;  // Type of road (motorway, residential, etc.)
    std::optional<std::string> name;          // Road name
    bool oneway{false};                       // Whether the road is one-way
    
    // Constructor for required fields
    Edge(int64_t src, int64_t tgt, double dist)
        : source(src), target(tgt), distance(dist) {}
};

} // namespace route_planner