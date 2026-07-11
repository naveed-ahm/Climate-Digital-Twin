# src/config.py

import numpy as np

# Spatial Configuration representing India
# Approx boundaries: Lat 8°N to 36°N, Lon 68°E to 98°E
LAT_MIN, LAT_MAX = 8.0, 36.0
LON_MIN, LON_MAX = 68.0, 98.0
GRID_SIZE = 15  # 15x15 grid representing India

# Regional Centers with coordinates (lat, lon) and names
REGIONS = {
    "Delhi": (28.6, 77.2),
    "Mumbai": (19.0, 72.8),
    "Chennai": (13.0, 80.2),
    "Kolkata": (22.5, 88.3),
    "Rajasthan (Desert)": (26.0, 72.0),
    "Sundarbans (Delta)": (21.9, 88.8),
    "Odisha Coast": (20.2, 86.0),
    "Western Ghats": (10.0, 76.5),
    "Assam Valley": (26.5, 92.5)
}

# Weather Features mapping in the climate state tensor
FEATURES = {
    0: "Precipitation",     # mm/hr
    1: "Temperature",       # °C
    2: "SST",              # Sea Surface Temp °C (relevant on coast/ocean pixels)
    3: "Cloud_Cover",       # 0.0 to 1.0
    4: "Soil_Moisture",     # 0.0 to 1.0 (relative saturation)
    5: "Wind_Speed",        # km/h
    6: "Humidity"           # 0.0 to 100.0 %
}
FEATURE_NAMES = list(FEATURES.values())

# Anomaly Thresholds
THRESHOLDS = {
    "cyclone": {
        "sst_min": 26.5,
        "wind_speed_min": 60.0,      # km/h
        "precipitation_min": 15.0,   # mm/hr
        "pressure_drop": 980.0       # hPa equivalent
    },
    "flood": {
        "precipitation_min": 20.0,   # mm/hr continuous
        "soil_moisture_min": 0.85
    },
    "heatwave": {
        "temperature_min": 42.0      # °C
    },
    "drought": {
        "soil_moisture_max": 0.20,
        "precipitation_max": 0.2,    # mm/hr
        "temperature_min": 35.0
    },
    "forest_fire": {
        "temperature_min": 38.0,
        "humidity_max": 25.0,
        "wind_speed_min": 25.0,
        "soil_moisture_max": 0.15
    },
    "extreme_rainfall": {
        "precipitation_min": 35.0    # mm/hr
    }
}

# Simulation/Control Speed
SIMULATION_TICK_SECONDS = 2.0  # seconds in real-world dashboard representing 1 simulation tick (e.g. 6 hours)

def get_grid_coords():
    """Generates coordinate arrays for the grid."""
    lats = np.linspace(LAT_MAX, LAT_MIN, GRID_SIZE)  # Top to bottom
    lons = np.linspace(LON_MIN, LON_MAX, GRID_SIZE)  # Left to right
    return lats, lons

def latlon_to_grid(lat, lon):
    """Converts a (lat, lon) coordinate to nearest grid indices (row, col)."""
    lats, lons = get_grid_coords()
    row = int(np.argmin(np.abs(lats - lat)))
    col = int(np.argmin(np.abs(lons - lon)))
    return row, col

def grid_to_latlon(row, col):
    """Converts grid indices (row, col) to central coordinate (lat, lon)."""
    lats, lons = get_grid_coords()
    return float(lats[row]), float(lons[col])

# Cost structure for mitigation strategies
STRATEGY_COSTS = {
    "Evacuation": 150000,           # in USD or INR equivalent scale
    "Drainage Clearing": 30000,
    "Pump Deployment": 45000,
    "Resource Pre-positioning": 60000,
    "Fire containment (Air-drop)": 120000,
    "Emergency SMS & Siren Alert": 5000,
    "Do Nothing": 0
}
