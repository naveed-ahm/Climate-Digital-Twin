# backend/app/services/allocator.py

import numpy as np
from typing import List, Dict, Any
from backend.app.services.config import REGIONS

class ResourceAllocator:
    def __init__(self):
        # Base requirements for Medium/Moderate severity
        self.base_requirements = {
            "cyclone": {
                "NDRF Rescue Unit": 8,
                "Ambulance": 15,
                "Relief Camp Site": 4,
                "Food Supply Truck": 10,
                "Rescue Helicopter": 3,
                "Mobile Medical Station": 2
            },
            "flood": {
                "NDRF Rescue Unit": 12,
                "Ambulance": 10,
                "Relief Camp Site": 6,
                "Food Supply Truck": 15,
                "Heavy Excavator": 4,
                "Mobile Medical Station": 3
            },
            "heavy_rain": {
                "NDRF Rescue Unit": 4,
                "Ambulance": 4,
                "Relief Camp Site": 1,
                "Food Supply Truck": 4,
                "Mobile Medical Station": 1
            },
            "heatwave": {
                "Ambulance": 8,
                "Relief Camp Site": 2, # Cooling centers
                "Food Supply Truck": 2,
                "Mobile Medical Station": 4
            },
            "drought": {
                "Ambulance": 2,
                "Food Supply Truck": 25, # Water/food distribution
                "Mobile Medical Station": 2
            },
            "forest_fire": {
                "NDRF Rescue Unit": 15, # Fire containment groups
                "Ambulance": 12,
                "Relief Camp Site": 3,
                "Rescue Helicopter": 4,
                "Mobile Medical Station": 3
            }
        }
        
        # Max available inventory pools
        self.inventory_pools = {
            "NDRF Rescue Unit": 100,
            "Ambulance": 150,
            "Relief Camp Site": 50,
            "Food Supply Truck": 200,
            "Rescue Helicopter": 15,
            "Mobile Medical Station": 40,
            "Heavy Excavator": 30,
            "Telecom Broadcast Channel": 10,
            "Municipal Labor Group": 80,
            "High-Capacity Pump": 50,
            "Mobile Generator": 40
        }

    def _get_distance(self, lat1, lon1, lat2, lon2):
        return np.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

    def get_population_density_multiplier(self, lat: float, lon: float):
        closest_dist = float('inf')
        closest_city = ""
        
        for city, coords in REGIONS.items():
            dist = self._get_distance(lat, lon, coords[0], coords[1])
            if dist < closest_dist:
                closest_dist = dist
                closest_city = city
                
        # If within ~150km of a major metro, scale up resources
        if closest_dist < 1.5:
            if closest_city in ["Mumbai", "Delhi", "Kolkata", "Chennai"]:
                return 3.0, closest_city
            return 1.8, closest_city
            
        return 1.0, "Rural/Remote Zone"

    def allocate_resources(self, anomaly: Dict[str, Any]) -> List[Dict[str, Any]]:
        event_type = anomaly["type"]
        severity = anomaly["severity"]
        lat = anomaly["location"]["lat"]
        lon = anomaly["location"]["lon"]
        
        base = self.base_requirements.get(event_type, {
            "NDRF Rescue Unit": 2,
            "Ambulance": 2,
            "Relief Camp Site": 1
        })
        
        # Severity multiplier
        sev_multipliers = {
            "low": 0.5,
            "moderate": 1.0,
            "high": 2.5,
            "severe": 3.5,
            "critical": 5.0
        }
        sev_mult = sev_multipliers.get(severity, 1.0)
        
        # Population density multiplier
        pop_mult, area_label = self.get_population_density_multiplier(lat, lon)
        
        allocations = []
        for resource, base_qty in base.items():
            qty = int(np.ceil(base_qty * sev_mult * pop_mult))
            total_avail = self.inventory_pools.get(resource, 50)
            allocated = min(qty, total_avail)
            
            # Estimate ETA: 30 mins base + random noise based on distance from nearest region center
            eta = 30.0 + int(np.random.uniform(15, 60))
            
            allocations.append({
                "resource_type": resource,
                "available": total_avail,
                "allocated": allocated,
                "location": {"lat": lat, "lon": lon},
                "eta_minutes": float(round(eta, 1))
            })
            
        return allocations

# Global singleton
allocator = ResourceAllocator()
