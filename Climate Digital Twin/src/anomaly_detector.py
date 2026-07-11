# src/anomaly_detector.py

import numpy as np
from src.config import THRESHOLDS, GRID_SIZE, grid_to_latlon

class AnomalyDetector:
    def __init__(self, config_thresholds=None):
        self.thresholds = config_thresholds or THRESHOLDS

    def detect_anomalies(self, state, ocean_mask):
        """
        Scans the climate state grid for active anomalies.
        Args:
            state: [GRID_SIZE, GRID_SIZE, 7] tensor
            ocean_mask: [GRID_SIZE, GRID_SIZE] boolean grid
        Returns:
            list of dicts containing detected anomalies and their details.
        """
        anomalies = []
        
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                lat, lon = grid_to_latlon(r, c)
                is_ocean = ocean_mask[r, c]
                
                # Fetch variables for this grid point
                prep = state[r, c, 0]      # precipitation
                temp = state[r, c, 1]      # temperature
                sst = state[r, c, 2]       # sea surface temp
                cloud = state[r, c, 3]     # cloud cover
                soil_m = state[r, c, 4]    # soil moisture
                wind = state[r, c, 5]      # wind speed
                humidity = state[r, c, 6]  # humidity

                # 1. Cyclone (Ocean only, or coast edges)
                if is_ocean:
                    cyc_thr = self.thresholds["cyclone"]
                    if sst >= cyc_thr["sst_min"] and wind >= cyc_thr["wind_speed_min"] and prep >= cyc_thr["precipitation_min"]:
                        # Calculate severity based on wind speed
                        if wind >= 120:
                            sev = "extreme"
                        elif wind >= 90:
                            sev = "high"
                        else:
                            sev = "medium"
                            
                        anomalies.append({
                            "type": "cyclone",
                            "grid_pos": (r, c),
                            "lat": lat,
                            "lon": lon,
                            "severity": sev,
                            "confidence": min(98.0, 60.0 + (wind - cyc_thr["wind_speed_min"])*0.5),
                            "metrics": {"SST": float(sst), "Wind Speed": float(wind), "Rainfall": float(prep)}
                        })

                # Land-specific anomalies
                if not is_ocean:
                    # 2. Flood (Saturated soil moisture + high rainfall)
                    fld_thr = self.thresholds["flood"]
                    if prep >= fld_thr["precipitation_min"] and soil_m >= fld_thr["soil_moisture_min"]:
                        sev = "extreme" if prep >= 30.0 else ("high" if prep >= 22.0 else "medium")
                        anomalies.append({
                            "type": "flood",
                            "grid_pos": (r, c),
                            "lat": lat,
                            "lon": lon,
                            "severity": sev,
                            "confidence": min(95.0, 70.0 + (soil_m - fld_thr["soil_moisture_min"])*150),
                            "metrics": {"Rainfall": float(prep), "Soil Moisture": float(soil_m)}
                        })

                    # 3. Heatwave (High land surface temperature)
                    hw_thr = self.thresholds["heatwave"]
                    if temp >= hw_thr["temperature_min"]:
                        sev = "extreme" if temp >= 45.0 else "high"
                        anomalies.append({
                            "type": "heatwave",
                            "grid_pos": (r, c),
                            "lat": lat,
                            "lon": lon,
                            "severity": sev,
                            "confidence": min(99.0, 80.0 + (temp - hw_thr["temperature_min"])*3.0),
                            "metrics": {"Temperature": float(temp), "Humidity": float(humidity)}
                        })

                    # 4. Drought (Extremely dry soil, low rain, high temperatures)
                    dr_thr = self.thresholds["drought"]
                    if soil_m <= dr_thr["soil_moisture_max"] and prep <= dr_thr["precipitation_max"] and temp >= dr_thr["temperature_min"]:
                        sev = "high" if soil_m <= 0.1 else "medium"
                        anomalies.append({
                            "type": "drought",
                            "grid_pos": (r, c),
                            "lat": lat,
                            "lon": lon,
                            "severity": sev,
                            "confidence": min(90.0, 65.0 + (0.2 - soil_m)*100),
                            "metrics": {"Soil Moisture": float(soil_m), "Temperature": float(temp)}
                        })

                    # 5. Forest Fire (High temp, dry soil, low humidity, high wind)
                    ff_thr = self.thresholds["forest_fire"]
                    if (temp >= ff_thr["temperature_min"] and 
                        soil_m <= ff_thr["soil_moisture_max"] and 
                        humidity <= ff_thr["humidity_max"] and 
                        wind >= ff_thr["wind_speed_min"]):
                        
                        sev = "extreme" if wind >= 40.0 else "high"
                        anomalies.append({
                            "type": "forest_fire",
                            "grid_pos": (r, c),
                            "lat": lat,
                            "lon": lon,
                            "severity": sev,
                            "confidence": min(95.0, 75.0 + (temp - ff_thr["temperature_min"])*2.0),
                            "metrics": {"Temperature": float(temp), "Humidity": float(humidity), "Wind Speed": float(wind)}
                        })
                
                # 6. Extreme Rainfall (Applies to both land and ocean)
                er_thr = self.thresholds["extreme_rainfall"]
                if prep >= er_thr["precipitation_min"]:
                    # Prevent double alert if it's already a flood/cyclone, or make it distinct
                    # We will log it if not already captured in flood/cyclone of same grid pos
                    already_logged = any(a["grid_pos"] == (r, c) and a["type"] in ["flood", "cyclone"] for a in anomalies)
                    if not already_logged:
                        sev = "high" if prep >= 50.0 else "medium"
                        anomalies.append({
                            "type": "extreme_rainfall",
                            "grid_pos": (r, c),
                            "lat": lat,
                            "lon": lon,
                            "severity": sev,
                            "confidence": min(99.0, 85.0 + (prep - er_thr["precipitation_min"])),
                            "metrics": {"Rainfall": float(prep)}
                        })

        return anomalies
