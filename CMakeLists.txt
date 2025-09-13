cmake_minimum_required(VERSION 3.10)
project(route_planner VERSION 1.0)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Add compile options
if(MSVC)
    add_compile_options(/W4)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find required packages
find_package(nlohmann_json 3.9.1 REQUIRED)
find_package(yaml-cpp REQUIRED)

# Library target
add_library(route_planner_lib
    src/graph.cpp
    src/data_loader.cpp
    src/config.cpp
)

target_include_directories(route_planner_lib
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(route_planner_lib
    PUBLIC
        nlohmann_json::nlohmann_json
        yaml-cpp
)

# Main executable
add_executable(route_planner 
    src/main.cpp
)

target_link_libraries(route_planner
    PRIVATE
        route_planner_lib
)