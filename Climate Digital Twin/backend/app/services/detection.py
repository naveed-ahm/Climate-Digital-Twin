# backend/app/services/detection.py

import numpy as np
import uuid
from datetime import datetime
from backend.app.services.config import THRESHOLDS, GRID_SIZE, grid_to_latlon

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
        
        # Approximate mapping of state indices to districts/states based on latitude
        # This will give name locations to anomalies detected anywhere in the grid.
        def get_location_name(lat, lon):
            if lat > 30:
                return "Himachal Pradesh", "Shimla"
            elif lat > 27 and lon < 78:
                return "Delhi", "New Delhi"
            elif lat > 24 and lon < 76:
                return "Rajasthan", "Churu"
            elif lat > 24 and lon > 88:
                return "Assam", "Guwahati"
            elif lat > 20 and lon > 85:
                return "Odisha", "Puri"
            elif lat > 21 and lon > 87:
                return "West Bengal", "Sundarbans"
            elif lat > 18 and lon < 74:
                return "Maharashtra", "Mumbai"
            elif lat < 14 and lon > 78:
                return "Tamil Nadu", "Chennai"
            elif lat < 15 and lon < 78:
                return "Karnataka", "Kodagu"
            else:
                return "Central India", "Deccan"

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
                        if wind >= 120:
                            sev = "critical"
                        elif wind >= 90:
                            sev = "severe"
                        elif wind >= 60:
                            sev = "high"
                        else:
                            sev = "moderate"
                            
                        state_name, district_name = get_location_name(lat, lon)
                        anomalies.append({
                            "id": f"cyc-{r}-{c}-{int(datetime.utcnow().timestamp())}",
                            "type": "cyclone",
                            "state": state_name,
                            "district": district_name,
                            "lat": lat,
                            "lon": lon,
                            "severity": sev,
                            "confidence": float(min(0.98, 0.60 + (wind - cyc_thr["wind_speed_min"]) * 0.005)),
                            "impact": {
                                "population": int(150000 + (wind * 2000)),
                                "infrastructure": int(50 + (wind * 0.3)),
                                "agriculture": int(40 + (prep * 1.5)),
                                "roads": int(60 + (prep * 0.8)),
                                "hospitals": 40,
                                "power": int(70 + (wind * 0.2)),
                                "water": int(50 + (prep * 0.5))
                            },
                            "metrics": {"SST": float(sst), "Wind Speed": float(wind), "Rainfall": float(prep)}
                        })

                # Land-specific anomalies
                if not is_ocean:
                    # 2. Flood (Saturated soil moisture + high rainfall)
                    fld_thr = self.thresholds["flood"]
                    if prep >= fld_thr["precipitation_min"] and soil_m >= fld_thr["soil_moisture_min"]:
                        sev = "critical" if prep >= 30.0 else ("severe" if prep >= 22.0 else "high")
                        state_name, district_name = get_location_name(lat, lon)
                        anomalies.append({
                            "id": f"fld-{r}-{c}-{int(datetime.utcnow().timestamp())}",
                            "type": "flood",
                            "state": state_name,
                            "district": district_name,
                            "lat": lat,
                            "lon": lon,
                            "severity": sev,
                            "confidence": float(min(0.95, 0.70 + (soil_m - fld_thr["soil_moisture_min"]) * 1.5)),
                            "impact": {
                                "population": int(100000 + (prep * 5000)),
                                "infrastructure": int(40 + (prep * 1.2)),
                                "agriculture": int(30 + (prep * 1.8)),
                                "roads": int(50 + (prep * 1.5)),
                                "hospitals": 30,
                                "power": int(30 + (prep * 0.8)),
                                "water": int(40 + (prep * 1.0))
                            },
                            "metrics": {"Rainfall": float(prep), "Soil Moisture": float(soil_m)}
                        })

                    # 3. Heatwave (High land surface temperature)
                    hw_thr = self.thresholds["heatwave"]
                    if temp >= hw_thr["temperature_min"]:
                        sev = "critical" if temp >= 45.0 else "severe"
                        state_name, district_name = get_location_name(lat, lon)
                        anomalies.append({
                            "id": f"hw-{r}-{c}-{int(datetime.utcnow().timestamp())}",
                            "type": "heatwave",
                            "state": state_name,
                            "district": district_name,
                            "lat": lat,
                            "lon": lon,
                            "severity": sev,
                            "confidence": float(min(0.99, 0.80 + (temp - hw_thr["temperature_min"]) * 0.03)),
                            "impact": {
                                "population": int(300000 + (temp * 10000)),
                                "infrastructure": 10,
                                "agriculture": int(50 + (temp * 0.8)),
                                "roads": 15,
                                "hospitals": int(20 + (temp * 0.5)),
                                "power": int(40 + (temp * 1.0)),
                                "water": int(60 + (temp * 0.8))
                            },
                            "metrics": {"Temperature": float(temp), "Humidity": float(humidity)}
                        })

                    # 4. Drought (Extremely dry soil, low rain, high temperatures)
                    dr_thr = self.thresholds["drought"]
                    if soil_m <= dr_thr["soil_moisture_max"] and prep <= dr_thr["precipitation_max"] and temp >= dr_thr["temperature_min"]:
                        sev = "severe" if soil_m <= 0.1 else "high"
                        state_name, district_name = get_location_name(lat, lon)
                        anomalies.append({
                            "id": f"dr-{r}-{c}-{int(datetime.utcnow().timestamp())}",
                            "type": "drought",
                            "state": state_name,
                            "district": district_name,
                            "lat": lat,
                            "lon": lon,
                            "severity": sev,
                            "confidence": float(min(0.90, 0.65 + (0.2 - soil_m) * 1.0)),
                            "impact": {
                                "population": int(500000 * (0.2 - soil_m)),
                                "infrastructure": 5,
                                "agriculture": int(80 + (0.2 - soil_m) * 50),
                                "roads": 5,
                                "hospitals": 20,
                                "power": int(30 + (temp * 0.5)),
                                "water": int(80 + (0.2 - soil_m) * 100)
                            },
                            "metrics": {"Soil Moisture": float(soil_m), "Temperature": float(temp)}
                        })

                    # 5. Forest Fire (High temp, dry soil, low humidity, high wind)
                    ff_thr = self.thresholds["forest_fire"]
                    if (temp >= ff_thr["temperature_min"] and 
                        soil_m <= ff_thr["soil_moisture_max"] and 
                        humidity <= ff_thr["humidity_max"] and 
                        wind >= ff_thr["wind_speed_min"]):
                        
                        sev = "critical" if wind >= 40.0 else "severe"
                        state_name, district_name = get_location_name(lat, lon)
                        anomalies.append({
                            "id": f"ff-{r}-{c}-{int(datetime.utcnow().timestamp())}",
                            "type": "forest_fire",
                            "state": state_name,
                            "district": district_name,
                            "lat": lat,
                            "lon": lon,
                            "severity": sev,
                            "confidence": float(min(0.95, 0.75 + (temp - ff_thr["temperature_min"]) * 0.02)),
                            "impact": {
                                "population": int(10000 + (wind * 500)),
                                "infrastructure": int(20 + (wind * 0.5)),
                                "agriculture": int(60 + (temp * 0.6)),
                                "roads": 20,
                                "hospitals": 10,
                                "power": int(20 + (wind * 0.4)),
                                "water": 10
                            },
                            "metrics": {"Temperature": float(temp), "Humidity": float(humidity), "Wind Speed": float(wind)}
                        })
                
                # 6. Extreme Rainfall (Applies to both land and ocean)
                er_thr = self.thresholds["extreme_rainfall"]
                if prep >= er_thr["precipitation_min"]:
                    already_logged = any(a["lat"] == lat and a["lon"] == lon and a["type"] in ["flood", "cyclone"] for a in anomalies)
                    if not already_logged:
                        sev = "severe" if prep >= 50.0 else "high"
                        state_name, district_name = get_location_name(lat, lon)
                        anomalies.append({
                            "id": f"er-{r}-{c}-{int(datetime.utcnow().timestamp())}",
                            "type": "heavy_rain",
                            "state": state_name,
                            "district": district_name,
                            "lat": lat,
                            "lon": lon,
                            "severity": sev,
                            "confidence": float(min(0.99, 0.85 + (prep - er_thr["precipitation_min"]) * 0.01)),
                            "impact": {
                                "population": int(50000 + (prep * 1000)),
                                "infrastructure": 20,
                                "agriculture": 40,
                                "roads": 50,
                                "hospitals": 10,
                                "power": 30,
                                "water": 30
                            },
                            "metrics": {"Rainfall": float(prep)}
                        })

        return anomalies

# Global singleton
detector = AnomalyDetector()
