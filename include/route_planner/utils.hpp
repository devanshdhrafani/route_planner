#pragma once

#include <cmath>

namespace route_planner {
namespace utils {

/**
 * Calculate the great-circle distance between two points on Earth.
 * Uses the Haversine formula.
 * 
 * @param lat1 Latitude of first point in degrees
 * @param lon1 Longitude of first point in degrees
 * @param lat2 Latitude of second point in degrees
 * @param lon2 Longitude of second point in degrees
 * @return Distance in kilometers
 */
inline double haversine_distance(double lat1, double lon1, double lat2, double lon2) {
    // Convert to radians
    const double lat1_rad = lat1 * M_PI / 180.0;
    const double lon1_rad = lon1 * M_PI / 180.0;
    const double lat2_rad = lat2 * M_PI / 180.0;
    const double lon2_rad = lon2 * M_PI / 180.0;
    
    // Haversine formula
    const double dlat = lat2_rad - lat1_rad;
    const double dlon = lon2_rad - lon1_rad;
    const double a = std::sin(dlat/2) * std::sin(dlat/2) +
                    std::cos(lat1_rad) * std::cos(lat2_rad) *
                    std::sin(dlon/2) * std::sin(dlon/2);
    const double c = 2 * std::atan2(std::sqrt(a), std::sqrt(1-a));
    
    // Earth's radius in km
    const double R = 6371.0;
    return R * c;
}

} // namespace utils
} // namespace route_planner