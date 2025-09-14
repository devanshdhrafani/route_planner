# Route Planner

A C++ route planning system with A* algorithm implementation for OpenStreetMap road networks.

## Features

- **A* Path Planning**: Distance and time-based route optimization
- **Traffic Modeling**: Edge-specific speed modifications and traffic conditions
- **Highway Type Support**: Intelligent speed defaults based on road classification
- **Interactive Visualization**: Web-based route and traffic overlay maps
- **OSM Data Processing**: Download and parse OpenStreetMap data

## Environment Setup

### C++ Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install build-essential cmake git
sudo apt install nlohmann-json3-dev libyaml-cpp-dev
```

### Python Environment

Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Dependencies

### C++
- CMake 3.10+
- C++17 compatible compiler
- nlohmann_json 3.9.1+
- yaml-cpp

### Python
See `requirements.txt` for complete list. Main dependencies:
- folium (interactive maps)
- pandas (data processing)
- geopandas (geospatial data)
- pyrosm (OSM parsing)
- PyYAML (configuration)

## Build

```bash
mkdir build && cd build
cmake ..
make
```

## Usage

### Basic Route Planning

```bash
./bin/route_planner --start-lat 40.4499 --start-lon -79.9862 --end-lat 40.4334 --end-lon -79.9583
```

### Configuration

Edit `config/default.yaml` to set:
- Data file paths
- Highway speed defaults
- Traffic conditions
- Default start/end coordinates

### Visualization

```bash
python scripts/visualizer.py --csv results/route_time_*.csv --show-traffic
```

### Data Processing

Download OSM data:
```bash
python scripts/osm_downloader.py --bbox -80.031 40.410 -79.896 40.494
```

Parse to JSON format:
```bash
python scripts/osm_parser.py --input data/bbox_*.pbf --output-dir data/
```

## Output

- Route results: `results/*.csv`
- Interactive maps: `results/*.html`
- Performance metrics and statistics

## License

MIT License - see LICENSE file for details.