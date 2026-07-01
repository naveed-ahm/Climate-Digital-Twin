# src/output_generator.py

import json
from src.config import THRESHOLDS

class OutputGenerator:
    def __init__(self):
        pass

    def generate_sms_alert(self, anomaly, recommendation=None):
        """
        Creates a structured, concise SMS broadcast template for local authorities and residents.
        """
        event_type = (anomaly["event_type"] if "event_type" in anomaly else anomaly["type"]).upper()
        severity = anomaly["severity"].upper()
        time_window = anomaly.get("time_window", "Immediate")
        lat, lon = anomaly["location_coord"] if "location_coord" in anomaly else (anomaly["lat"], anomaly["lon"])
        
        msg = (
            f"⚠️ CLIMATE ALERT: {severity} {event_type} predicted at Lat {lat:.2f}, Lon {lon:.2f}.\n"
            f"⏱️ Timeframe: {time_window}.\n"
            f"📊 Confidence: {anomaly['confidence']:.1f}%.\n"
        )
        
        if recommendation:
            msg += f"👉 Recommended Mitigation: {recommendation['strategy_name']} (Simulated Risk Reduction: {recommendation['risk_reduction_pct']}%)."
        else:
            msg += f"👉 Recommended: Monitor and prepare emergency evacuations."
            
        return msg

    def generate_geojson(self, anomaly):
        """
        Generates a standard GeoJSON FeatureCollection defining the disaster hazard boundary circle.
        Useful for GIS web interfaces (QGIS, Bhuvan, Leaflet).
        """
        event_type = anomaly["event_type"] if "event_type" in anomaly else anomaly["type"]
        severity = anomaly["severity"]
        lat, lon = anomaly["location_coord"] if "location_coord" in anomaly else (anomaly["lat"], anomaly["lon"])
        
        # Build simple circle coordinate approximation (12 vertices around center)
        import numpy as np
        num_vertices = 16
        # radius in degree terms (~50km radius = ~0.45 degrees)
        radius_deg = 0.45 if severity == "extreme" else (0.3 if severity == "high" else 0.15)
        
        coordinates = []
        for i in range(num_vertices + 1):
            angle = i * (2.0 * np.pi / num_vertices)
            c_lat = lat + radius_deg * np.sin(angle)
            c_lon = lon + radius_deg * np.cos(angle)
            coordinates.append([round(c_lon, 4), round(c_lat, 4)])
            
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "hazard_type": event_type,
                        "severity": severity,
                        "confidence_pct": round(anomaly["confidence"], 1),
                        "time_window": anomaly.get("time_window", "Now"),
                        "center_lat": lat,
                        "center_lon": lon
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [coordinates]
                    }
                }
            ]
        }
        return geojson

    def generate_explainability_report(self, anomaly):
        """
        Translates raw meteorology breaches into human-readable scientific rationale.
        Explains WHY the anomaly was flagged.
        """
        event_type = anomaly["event_type"] if "event_type" in anomaly else anomaly["type"]
        metrics = anomaly["metrics"]
        
        report = f"### AI Diagnosis: {event_type.capitalize()} Detection Rationale\n\n"
        report += f"The digital twin flagged this region because localized sensor feeds breached established warning thresholds:\n\n"
        
        for k, v in metrics.items():
            report += f"- **{k}**: {v:.2f} "
            
            # Match to thresholds
            if event_type == "flood":
                if k == "Rainfall":
                    report += f"(Breached threshold of >= {THRESHOLDS['flood']['precipitation_min']} mm/hr)\n"
                elif k == "Soil Moisture":
                    report += f"(Saturated at {v*100:.1f}%, exceeding soil capacity threshold of >= {THRESHOLDS['flood']['soil_moisture_min']*100:.1f}%)\n"
            elif event_type == "cyclone":
                if k == "SST":
                    report += f"(Sea surface warmth at {v:.1f}°C, exceeding thermodynamic threshold of >= {THRESHOLDS['cyclone']['sst_min']}°C)\n"
                elif k == "Wind Speed":
                    report += f"(Wind velocity at {v:.1f} km/h, exceeding kinetic threshold of >= {THRESHOLDS['cyclone']['wind_speed_min']} km/h)\n"
            elif event_type == "heatwave" and k == "Temperature":
                report += f"(Ambient air temperature reached {v:.1f}°C, exceeding thermal limits of >= {THRESHOLDS['heatwave']['temperature_min']}°C)\n"
            elif event_type == "forest_fire":
                if k == "Temperature":
                    report += f"(Air temperature at {v:.1f}°C >= threshold of {THRESHOLDS['forest_fire']['temperature_min']}°C)\n"
                elif k == "Humidity":
                    report += f"(Relative humidity dropped to {v:.1f}% <= fire propagation threshold of {THRESHOLDS['forest_fire']['humidity_max']}%)\n"
                elif k == "Wind Speed":
                    report += f"(Wind velocity at {v:.1f} km/h >= spreading threshold of {THRESHOLDS['forest_fire']['wind_speed_min']} km/h)\n"
            else:
                report += "\n"
                
        report += f"\n**Physical Dynamics Summary**: "
        if event_type == "flood":
            report += "When soil moisture is near saturation, the ground loses all infiltration capacity. Any additional heavy rainfall immediately converts to overland surface runoff, resulting in rapid-onset flooding."
        elif event_type == "cyclone":
            report += "Sufficiently warm sea surface temperatures (SST) act as a heat engine, feeding moisture into the convective updraft, while high wind velocities verify the formation of a low-pressure cyclonic vortex."
        elif event_type == "heatwave":
            report += "Stagnant high-pressure domes prevent cloud cover and trap terrestrial solar radiation, driving surface air temperature to critical levels hazardous to humans and livestock."
        elif event_type == "forest_fire":
            report += "High temperatures dry out ground leaf litter (fuel), while low humidity maximizes fuel flammability. Strong winds feed oxygen to the combustion site and carry embers forward, causing rapid spread."
        elif event_type == "drought":
            report += "Protracted lack of rainfall combined with elevated temperatures accelerates evaporation, depleting shallow soil moisture tables and causing agricultural water stress."
        else:
            report += "A significant meteorological divergence has been recorded, indicating high spatial anomaly gradients."
            
        return report

    def generate_action_checklist(self, anomaly, recommendation=None):
        """
        Compiles a chronological government emergency action checklist.
        """
        event_type = anomaly["event_type"] if "event_type" in anomaly else anomaly["type"]
        rec_name = recommendation["strategy_name"] if recommendation else "Do Nothing"
        
        checklist = []
        
        checklist.append("1. **Phase 1 (Immediate Alerting)**: Dispatch alerts to regional relief headquarters and trigger sirens in target coordinates.")
        
        if event_type == "cyclone":
            checklist.append("2. **Phase 2 (Coastal Safety)**: Suspend fishing and marine operations along predicted coastlines. Enforce harbor safety protocols.")
            if "Evacuation" in rec_name:
                checklist.append("3. **Phase 3 (Evacuation)**: Initiate mandatory evac routes from low-lying coastal zones to designated concrete cyclone shelters.")
            checklist.append("4. **Phase 4 (Medical Pre-positioning)**: Dispatch mobile medical units and pre-position emergency drinking water supply.")
            
        elif event_type == "flood":
            if "Pump" in rec_name:
                checklist.append("2. **Phase 2 (Deploy Assets)**: Deploy heavy duty high-volume dewatering pumps to local low-lying urban nodes.")
            if "Drainage" in rec_name:
                checklist.append("3. **Phase 3 (Drainage Check)**: Clear stormwater blockages and open barrage gates in a controlled sequence.")
            checklist.append("4. **Phase 4 (Rescue readiness)**: Position inflatable rescue boats (NDRF) at key staging hubs near coordinates.")
            
        elif event_type == "forest_fire":
            if "Air-drop" in rec_name:
                checklist.append("2. **Phase 2 (Fire Containment)**: Authorize helicopter water air-drops on the fire periphery to suppress spread.")
            checklist.append("3. **Phase 3 (Buffer creation)**: Excavate fire breaks using bulldozers to remove dry fuel lines.")
            checklist.append("4. **Phase 4 (Evacuation)**: Evacuate forest settlements and establish temporary relief camps upwind.")
            
        elif event_type == "heatwave":
            checklist.append("2. **Phase 2 (Cooling Centers)**: Activate air-conditioned cooling shelters and water kiosks.")
            checklist.append("3. **Phase 3 (Grid management)**: Request power grids to coordinate load balancing to prevent brownouts from AC usage.")
            checklist.append("4. **Phase 4 (Labor orders)**: Implement mandatory work suspension for outdoor laborers between 12:00 PM and 4:00 PM.")
            
        elif event_type == "drought":
            checklist.append("2. **Phase 2 (Water allocation)**: Restrict industrial water draws and prioritize agricultural and domestic supply.")
            checklist.append("3. **Phase 3 (Water trucking)**: Deploy municipal water tankers to affected talukas.")
            checklist.append("4. **Phase 4 (Fodder camps)**: Setup cattle fodder camps and distribute crop subsidies.")
            
        else:
            checklist.append("2. **Phase 2 (Monitoring)**: Enhance meteorological observation frequency.")
            checklist.append("3. **Phase 3 (Coordination)**: Brief administrative officers on stand-by protocols.")

        return checklist
