# backend/app/services/synthetic_data.py

import numpy as np
from backend.app.services.config import GRID_SIZE, get_grid_coords, latlon_to_grid

def elevation_boost(elev):
    return elev * 1.5

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
        mask = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                lat = self.lats[r]
                lon = self.lons[c]
                
                # Broad approximation of India's coastlines
                if lat < 23.5:
                    if lat < 8.0:
                        mask[r, c] = True
                    elif lon < 68.5:
                        mask[r, c] = True
                    elif lon > 89.0:
                        mask[r, c] = True
                    else:
                        west_bound = 68.0 + (23.5 - lat) * 0.65
                        east_bound = 90.0 - (23.5 - lat) * 0.75
                        
                        if lon < west_bound or lon > east_bound:
                            mask[r, c] = True
                else:
                    mask[r, c] = False
        return mask

    def _generate_elevation_map(self):
        elevation = np.zeros((GRID_SIZE, GRID_SIZE))
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                lat = self.lats[r]
                lon = self.lons[c]
                
                if self.ocean_mask[r, c]:
                    elevation[r, c] = 0.0
                    continue
                
                if lat > 30.0:
                    elevation[r, c] = 0.6 + 0.4 * np.sin((lat - 30.0) / 6.0 * np.pi)
                elif lon > 73.0 and lon < 75.5 and lat < 20.0:
                    elevation[r, c] = 0.4
                elif lat < 22.0 and lon > 75.0 and lon < 82.0:
                    elevation[r, c] = 0.2
                else:
                    elevation[r, c] = 0.05
                    
        return elevation

    def set_disaster_trigger(self, disaster_type, center_lat=None, intensity=1.0):
        self.active_trigger = disaster_type
        self.trigger_center = center_lat
        self.trigger_intensity = intensity

    def clear_trigger(self):
        self.active_trigger = None
        self.trigger_center = None

    def ingest_current_state(self, base_state=None):
        self.time_step += 1
        t = self.time_step
        
        # Initialize features: Prep, Temp, SST, Cloud, Soil, Wind, Humidity
        grid = np.zeros((GRID_SIZE, GRID_SIZE, 7))
        
        monsoon_factor = 0.4 + 0.6 * np.sin(t * 0.05)
        
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                lat = self.lats[r]
                lon = self.lons[c]
                is_ocean = self.ocean_mask[r, c]
                elev = self.elevation_map[r, c]
                
                # 1. Temperature
                base_temp = 32.0 - (lat - 8.0) * 0.4 - elev * 15.0
                temp = base_temp + 4.0 * np.sin(t * 0.2) + np.random.normal(0, 0.5)
                
                # 2. SST
                sst = 0.0
                if is_ocean:
                    sst = 27.5 - (lat - 8.0) * 0.12 + 1.0 * np.sin(t * 0.1) + np.random.normal(0, 0.2)
                    temp = sst - 1.0
                
                # 3. Cloud Cover
                base_cloud = 0.6 * monsoon_factor if is_ocean else 0.2
                cloud = base_cloud + 0.3 * np.cos(lon * 0.3 - t * 0.1) + np.random.normal(0, 0.05)
                cloud = np.clip(cloud, 0.0, 1.0)
                
                # 4. Precipitation
                prep = 0.0
                if cloud > 0.65:
                    prep = (cloud - 0.65) * 8.0 * (1.0 + elevation_boost(elev)) + np.random.exponential(0.5)
                    if not is_ocean and elev > 0.3:
                        prep *= 1.8
                
                # 5. Wind Speed
                wind = 12.0 + (30.0 if is_ocean else 5.0) * (cloud) + np.random.normal(0, 2.0)
                wind = max(0.0, wind)
                
                # 6. Humidity
                humidity = 40.0 + 45.0 * cloud + (10.0 if is_ocean else 0.0) - (temp - 30.0) * 1.5
                humidity = np.clip(humidity, 10.0, 100.0)
                
                # 7. Soil Moisture
                if is_ocean:
                    soil_m = 1.0
                else:
                    if base_state is not None:
                        prev_soil = base_state[r, c, 4]
                        evap = 0.008 * (temp / 30.0) * (1.0 - humidity / 100.0)
                        rain_absorbed = prep * 0.08
                        soil_m = prev_soil - evap + rain_absorbed
                    else:
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
        trigger_type = self.active_trigger
        intensity = self.trigger_intensity
        
        if self.trigger_center is None:
            if trigger_type == 'cyclone':
                self.trigger_center = (18.0, 86.5)
            elif trigger_type == 'heatwave':
                self.trigger_center = (27.5, 74.0)
            elif trigger_type in ('monsoon', 'flood'):
                self.trigger_center = (19.0, 72.8)
            elif trigger_type == 'drought':
                self.trigger_center = (15.0, 76.0)

        tr_r, tr_c = latlon_to_grid(self.trigger_center[0], self.trigger_center[1])

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                lat = self.lats[r]
                lon = self.lons[c]
                
                dist = np.sqrt((r - tr_r)**2 + (c - tr_c)**2)
                influence = np.exp(-dist / 3.0)
                
                if trigger_type == 'cyclone':
                    if self.ocean_mask[r, c] or dist < 2.5:
                        grid[r, c, 5] += 90.0 * influence * intensity
                        grid[r, c, 0] += 30.0 * influence * intensity
                        grid[r, c, 3] = max(grid[r, c, 3], 0.95 * influence)
                        grid[r, c, 6] = max(grid[r, c, 6], 95.0 * influence)
                        if self.ocean_mask[r, c]:
                            grid[r, c, 2] = max(grid[r, c, 2], 28.5)
                            
                elif trigger_type == 'heatwave':
                    if not self.ocean_mask[r, c]:
                        grid[r, c, 1] += 12.0 * influence * intensity
                        grid[r, c, 6] = max(10.0, grid[r, c, 6] - 30.0 * influence * intensity)
                        grid[r, c, 4] = max(0.05, grid[r, c, 4] - 0.25 * influence * intensity)
                        grid[r, c, 3] = max(0.0, grid[r, c, 3] - 0.5 * influence)
                        
                elif trigger_type in ('monsoon', 'flood'):
                    grid[r, c, 0] += 38.0 * influence * intensity
                    grid[r, c, 3] = max(grid[r, c, 3], 0.98 * influence)
                    grid[r, c, 4] = max(grid[r, c, 4], 0.95 * influence)
                    grid[r, c, 6] = max(grid[r, c, 6], 90.0 * influence)
                    
                elif trigger_type == 'drought':
                    decay = np.exp(-dist / 6.0)
                    if not self.ocean_mask[r, c]:
                        grid[r, c, 4] = max(0.03, grid[r, c, 4] - 0.4 * decay * intensity)
                        grid[r, c, 0] = max(0.0, grid[r, c, 0] - 5.0 * decay)
                        grid[r, c, 1] += 5.0 * decay * intensity
                        grid[r, c, 6] = max(12.0, grid[r, c, 6] - 20.0 * decay * intensity)

        return grid

# Global singletons
ingestor = ClimateDataIngestor()
