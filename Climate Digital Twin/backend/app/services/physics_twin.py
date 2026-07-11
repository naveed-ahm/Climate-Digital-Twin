# backend/app/services/physics_twin.py

import numpy as np
from backend.app.services.config import GRID_SIZE, FEATURES, REGIONS, latlon_to_grid, grid_to_latlon

class ClimateDigitalTwin:
    def __init__(self, history_len=10):
        self.history_len = history_len
        self.state_history = []
        self.current_step = -1

    def update_state(self, new_grid):
        """
        Appends the latest unified climate tensor to the digital twin state history.
        Maintains a rolling window of length history_len.
        """
        self.current_step += 1
        self.state_history.append(new_grid.copy())
        if len(self.state_history) > self.history_len:
            self.state_history.pop(0)

    @property
    def current_state(self):
        """Returns the most recent climate grid tensor [GRID_SIZE, GRID_SIZE, 7]."""
        if not self.state_history:
            return None
        return self.state_history[-1]

    def get_history(self):
        """Returns the current list of historical climate grids."""
        return self.state_history

    def get_region_metrics(self, region_name):
        """
        Extracts meteorological values for a specific named city/region.
        """
        if region_name not in REGIONS:
            raise ValueError(f"Region {region_name} not defined in config.")
            
        if self.current_state is None:
            return None
            
        lat, lon = REGIONS[region_name]
        r, c = latlon_to_grid(lat, lon)
        
        metrics = {}
        for feat_idx, feat_name in FEATURES.items():
            metrics[feat_name] = float(self.current_state[r, c, feat_idx])
            
        metrics["lat"] = lat
        metrics["lon"] = lon
        metrics["grid_pos"] = (r, c)
        return metrics

    def get_all_regions_metrics(self):
        """Gets metrics for all regions defined in config."""
        return {name: self.get_region_metrics(name) for name in REGIONS}

    def clone_state(self):
        """
        Creates a deep copy of the current state tensor.
        Used by the simulation engine to run parallel 'what-if' scenarios.
        """
        if self.current_state is None:
            return None
        return self.current_state.copy()
        
    def advance_physics(self, state, steps=1, wind_dir=(-1, 1)):
        """
        Simulates natural physics equations (diffusion, wind drift) on the grid.
        - Temperature and humidity diffuse to neighboring grid cells.
        - Precipitation is transported slightly along the wind direction.
        - Soil moisture increases with rainfall, decreases with evaporation.
        """
        sim_state = state.copy()
        
        for _ in range(steps):
            next_state = sim_state.copy()
            
            # 1. Diffusion of Temperature (idx 1) and Humidity (idx 6)
            for r in range(1, GRID_SIZE - 1):
                for c in range(1, GRID_SIZE - 1):
                    for idx in [1, 6]:
                        center = sim_state[r, c, idx]
                        neighbors = (sim_state[r+1, c, idx] + sim_state[r-1, c, idx] + 
                                     sim_state[r, c+1, idx] + sim_state[r, c-1, idx])
                        next_state[r, c, idx] = 0.85 * center + 0.15 * (neighbors / 4.0)
            
            # 2. Wind Drift / Convection: Cloud cover (idx 3) and Precipitation (idx 0)
            row_drift, col_drift = wind_dir
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    src_r = int(np.clip(r - row_drift, 0, GRID_SIZE - 1))
                    src_c = int(np.clip(c - col_drift, 0, GRID_SIZE - 1))
                    
                    next_state[r, c, 3] = 0.9 * sim_state[r, c, 3] + 0.1 * sim_state[src_r, src_c, 3]
                    next_state[r, c, 0] = 0.95 * sim_state[r, c, 0] + 0.05 * sim_state[src_r, src_c, 0]
            
            # 3. Saturated Soil Drainage
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    prep = next_state[r, c, 0]
                    temp = next_state[r, c, 1]
                    
                    evap = 0.005 * (temp / 30.0)
                    absorption = prep * 0.05
                    
                    next_state[r, c, 4] = np.clip(sim_state[r, c, 4] - evap + absorption, 0.05, 1.0)
                    
            sim_state = next_state
            
        return sim_state

# Global singleton
digital_twin = ClimateDigitalTwin(history_len=10)
