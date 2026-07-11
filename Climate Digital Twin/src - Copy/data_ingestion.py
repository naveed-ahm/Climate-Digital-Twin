# src/data_ingestion.py

import numpy as np
from src.config import GRID_SIZE, LAT_MAX, LAT_MIN, LON_MAX, LON_MIN, get_grid_coords, latlon_to_grid

class ClimateDataIngestor:
    def __init__(self):
        self.lats, self.lons = get_grid_coords()
        self.ocean_mask = self._generate_ocean_mask()
        self.elevation_map = self._generate_elevation_map()
        self.time_step = 0
        
        # Current active disaster triggers
        self.active_trigger = None  # 'cyclone', 'heatwave', 'monsoon', 'drought'
        self.trigger_center = None   # (lat, lon)
        self.trigger_intensity = 1.0

    def _generate_ocean_mask(self):
        """
        Generates a Boolean grid where True represents ocean (Arabian Sea, Bay of Bengal, Indian Ocean)
        and False represents land.
        """
        mask = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                lat = self.lats[r]
                lon = self.lons[c]
                
                # Broad approximation of India's coastlines
                # South of 23.5N is ocean, except for the Indian peninsula (which is roughly between 72E and 85E)
                if lat < 23.5:
                    if lat < 8.0:
                        mask[r, c] = True
                    elif lon < 68.5:
                        mask[r, c] = True
                    elif lon > 89.0:
                        mask[r, c] = True
                    else:
                        # Triangular peninsula shape: land narrows as we go south
                        # At lat 20, land is roughly 72.5E to 86E
                        # At lat 13, land is roughly 74E to 80.5E
                        # At lat 8, land is narrow (77E to 78.5E)
                        west_bound = 68.0 + (23.5 - lat) * 0.65
                        east_bound = 90.0 - (23.5 - lat) * 0.75
                        
                        if lon < west_bound or lon > east_bound:
                            mask[r, c] = True
                else:
                    # Northern areas are all land
                    mask[r, c] = False
        return mask

    def _generate_elevation_map(self):
        """
        Generates dummy elevation map of India (Himalayas in north, Western Ghats, Deccan Plateau).
        Elevation is scaled from 0 (sea level) to 1.0 (highest peaks).
        """
        elevation = np.zeros((GRID_SIZE, GRID_SIZE))
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                lat = self.lats[r]
                lon = self.lons[c]
                
                if self.ocean_mask[r, c]:
                    elevation[r, c] = 0.0
                    continue
                
                # Himalayas: Lat > 30N
                if lat > 30.0:
                    elevation[r, c] = 0.6 + 0.4 * np.sin((lat - 30.0) / 6.0 * np.pi)
                # Western Ghats: narrow strip on west coast (around 73.5E to 75E, below 20N)
                elif lon > 73.0 and lon < 75.5 and lat < 20.0:
                    elevation[r, c] = 0.4
                # Deccan Plateau: central India
                elif lat < 22.0 and lon > 75.0 and lon < 82.0:
                    elevation[r, c] = 0.2
                else:
                    elevation[r, c] = 0.05
                    
        return elevation

    def set_disaster_trigger(self, disaster_type, center_lat=None, intensity=1.0):
        """
        Force-inject a climate anomaly event.
        Types: 'cyclone', 'heatwave', 'monsoon', 'drought'
        """
        self.active_trigger = disaster_type
        self.trigger_center = center_lat
        self.trigger_intensity = intensity

    def clear_trigger(self):
        self.active_trigger = None
        self.trigger_center = None

    def ingest_current_state(self, base_state=None):
        """
        Simulates one time step of multi-source data ingestion.
        Returns:
            grid_data: (GRID_SIZE, GRID_SIZE, 7) tensor
        """
        self.time_step += 1
        t = self.time_step
        
        # Initialize features: Prep, Temp, SST, Cloud, Soil, Wind, Humidity
        grid = np.zeros((GRID_SIZE, GRID_SIZE, 7))
        
        # Compute baseline seasonal trends
        # Simulating monsoon season shifting
        monsoon_factor = 0.4 + 0.6 * np.sin(t * 0.05)  # cyclic variation
        
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                lat = self.lats[r]
                lon = self.lons[c]
                is_ocean = self.ocean_mask[r, c]
                elev = self.elevation_map[r, c]
                
                # 1. Temperature (°C)
                # Base temperature decreases with latitude (North is cooler) and elevation
                base_temp = 32.0 - (lat - 8.0) * 0.4 - elev * 15.0
                # Seasonal diurnal fluctuation + noise
                temp = base_temp + 4.0 * np.sin(t * 0.2) + np.random.normal(0, 0.5)
                
                # 2. SST (°C) - only valid on ocean
                sst = 0.0
                if is_ocean:
                    # Ocean is warm, warmer in the south
                    sst = 27.5 - (lat - 8.0) * 0.12 + 1.0 * np.sin(t * 0.1) + np.random.normal(0, 0.2)
                    temp = sst - 1.0 # Air temperature over ocean tracks SST
                
                # 3. Cloud Cover (0 to 1)
                # Ocean tends to have more clouds, especially in monsoon
                base_cloud = 0.6 * monsoon_factor if is_ocean else 0.2
                # Spatial wave pattern drifting east-to-west
                cloud = base_cloud + 0.3 * np.cos(lon * 0.3 - t * 0.1) + np.random.normal(0, 0.05)
                cloud = np.clip(cloud, 0.0, 1.0)
                
                # 4. Precipitation (mm/hr)
                # Proportional to cloud cover, humidity, and random convective cells
                prep = 0.0
                if cloud > 0.65:
                    prep = (cloud - 0.65) * 8.0 * (1.0 + elevation_boost(elev)) + np.random.exponential(0.5)
                    if not is_ocean and elev > 0.3: # Orographic rainfall over mountains
                        prep *= 1.8
                
                # 5. Wind Speed (km/h)
                # Higher over ocean, base wind
                wind = 12.0 + (30.0 if is_ocean else 5.0) * (cloud) + np.random.normal(0, 2.0)
                wind = max(0.0, wind)
                
                # 6. Humidity (%)
                # Higher near ocean and cloud cover
                humidity = 40.0 + 45.0 * cloud + (10.0 if is_ocean else 0.0) - (temp - 30.0) * 1.5
                humidity = np.clip(humidity, 10.0, 100.0)
                
                # 7. Soil Moisture (0 to 1)
                # Decreases over time due to heat, increases with precipitation
                if is_ocean:
                    soil_m = 1.0
                else:
                    # Let's pull previous soil moisture from base_state if available
                    if base_state is not None:
                        prev_soil = base_state[r, c, 4]
                        # evaporation rate proportional to temp and low humidity
                        evap = 0.008 * (temp / 30.0) * (1.0 - humidity / 100.0)
                        # absorption
                        rain_absorbed = prep * 0.08
                        soil_m = prev_soil - evap + rain_absorbed
                    else:
                        # Initial guess
                        soil_m = 0.5 - 0.2 * (lat - 8.0)/28.0 + 0.3 * cloud
                    soil_m = np.clip(soil_m, 0.05, 1.0)
                
                grid[r, c, 0] = prep
                grid[r, c, 1] = temp
                grid[r, c, 2] = sst
                grid[r, c, 3] = cloud
                grid[r, c, 4] = soil_m
                grid[r, c, 5] = wind
                grid[r, c, 6] = humidity

        # Apply disaster triggers (inject anomalies)
        if self.active_trigger:
            grid = self._apply_trigger(grid)

        return grid

    def _apply_trigger(self, grid):
        """Modifies grid to simulate severe active weather events."""
        trigger_type = self.active_trigger
        intensity = self.trigger_intensity
        
        # Default center of disaster if none provided
        if self.trigger_center is None:
            if trigger_type == 'cyclone':
                # Build cyclone on Bay of Bengal or Odisha Coast
                self.trigger_center = (18.0, 86.5)
            elif trigger_type == 'heatwave':
                # Northern Plains / Rajasthan
                self.trigger_center = (27.5, 74.0)
            elif trigger_type == 'monsoon':
                # Mumbai/Western coast downpour
                self.trigger_center = (19.0, 72.8)
            elif trigger_type == 'drought':
                # Central / Southern India
                self.trigger_center = (15.0, 76.0)

        tr_r, tr_c = latlon_to_grid(self.trigger_center[0], self.trigger_center[1])

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                lat = self.lats[r]
                lon = self.lons[c]
                
                # Distance in grid cells
                dist = np.sqrt((r - tr_r)**2 + (c - tr_c)**2)
                # Exponential spatial decay of the effect
                influence = np.exp(-dist / 3.0)
                
                if trigger_type == 'cyclone':
                    # Warm ocean temperature, huge wind speed, high clouds and rainfall
                    if self.ocean_mask[r, c] or dist < 2.5:
                        grid[r, c, 5] += 90.0 * influence * intensity  # wind speed spikes
                        grid[r, c, 0] += 30.0 * influence * intensity  # rainfall spikes
                        grid[r, c, 3] = max(grid[r, c, 3], 0.95 * influence) # Cloud cover
                        grid[r, c, 6] = max(grid[r, c, 6], 95.0 * influence) # Humidity
                        if self.ocean_mask[r, c]:
                            grid[r, c, 2] = max(grid[r, c, 2], 28.5)   # Warmer sea surface
                            
                elif trigger_type == 'heatwave':
                    # Sky-rocketing temperature, low humidity, dry soil
                    if not self.ocean_mask[r, c]:
                        grid[r, c, 1] += 12.0 * influence * intensity  # Temperature increase
                        grid[r, c, 6] = max(10.0, grid[r, c, 6] - 30.0 * influence * intensity) # Dry air
                        grid[r, c, 4] = max(0.05, grid[r, c, 4] - 0.25 * influence * intensity) # Dry soil
                        grid[r, c, 3] = max(0.0, grid[r, c, 3] - 0.5 * influence) # Clear skies
                        
                elif trigger_type == 'monsoon':
                    # Intense localized rainfall, saturated soil, high cloud cover
                    grid[r, c, 0] += 38.0 * influence * intensity  # Heavy rain
                    grid[r, c, 3] = max(grid[r, c, 3], 0.98 * influence)
                    grid[r, c, 4] = max(grid[r, c, 4], 0.95 * influence) # Saturated soil
                    grid[r, c, 6] = max(grid[r, c, 6], 90.0 * influence)
                    
                elif trigger_type == 'drought':
                    # Dry soil, zero rain, moderately high temperature over large area
                    decay = np.exp(-dist / 6.0) # Larger footprint
                    if not self.ocean_mask[r, c]:
                        grid[r, c, 4] = max(0.03, grid[r, c, 4] - 0.4 * decay * intensity) # Complete soil dryout
                        grid[r, c, 0] = max(0.0, grid[r, c, 0] - 5.0 * decay) # No rain
                        grid[r, c, 1] += 5.0 * decay * intensity # Warmer temp
                        grid[r, c, 6] = max(12.0, grid[r, c, 6] - 20.0 * decay * intensity) # Dry air

        return grid

def elevation_boost(elev):
    return elev * 1.5
