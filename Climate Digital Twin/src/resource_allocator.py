# src/resource_allocator.py

from src.config import GRID_SIZE, REGIONS, latlon_to_grid

class ResourceAllocator:
    def __init__(self):
        # Base requirements for Medium severity
        self.base_requirements = {
            "cyclone": {
                "rescue_teams": 8,        # NDRF teams
                "ambulances": 15,
                "relief_camps": 4,
                "food_supply_kg": 2000,    # per day
                "water_supply_liters": 5000,
                "medical_units": 2
            },
            "flood": {
                "rescue_teams": 12,
                "ambulances": 10,
                "relief_camps": 6,
                "food_supply_kg": 3000,
                "water_supply_liters": 6000,
                "medical_units": 3
            },
            "heatwave": {
                "rescue_teams": 0,
                "ambulances": 8,
                "relief_camps": 2,        # Cooling centers
                "food_supply_kg": 200,
                "water_supply_liters": 8000, # Critical water needs
                "medical_units": 4
            },
            "drought": {
                "rescue_teams": 0,
                "ambulances": 2,
                "relief_camps": 0,
                "food_supply_kg": 1500,
                "water_supply_liters": 15000, # Massive water trucking
                "medical_units": 2
            },
            "forest_fire": {
                "rescue_teams": 15,       # Firefighting / evacuation crews
                "ambulances": 12,
                "relief_camps": 3,
                "food_supply_kg": 1000,
                "water_supply_liters": 4000,
                "medical_units": 3
            },
            "extreme_rainfall": {
                "rescue_teams": 4,
                "ambulances": 4,
                "relief_camps": 1,
                "food_supply_kg": 500,
                "water_supply_liters": 1000,
                "medical_units": 1
            }
        }

    def get_population_density_multiplier(self, lat, lon):
        """
        Calculates a multiplier based on geographic proximity to major population centers.
        Metros have massive population densities requiring higher resource scales.
        """
        closest_dist = float('inf')
        closest_city = ""
        
        for city, coords in REGIONS.items():
            dist = np_dist(lat, lon, coords[0], coords[1])
            if dist < closest_dist:
                closest_dist = dist
                closest_city = city
                
        # If within ~150km of a major metro, scale up resources
        if closest_dist < 1.5:  # grid-distance equivalent approx 150km
            if closest_city in ["Mumbai", "Delhi", "Kolkata", "Chennai"]:
                return 3.0, closest_city
            return 1.8, closest_city
            
        return 1.0, "Rural/Remote Zone"

    def allocate_resources(self, anomaly):
        """
        Computes resource requirement allocations for a given anomaly.
        Args:
            anomaly: dict representing detected or predicted anomaly.
        Returns:
            dict containing allocated rescue assets.
        """
        event_type = anomaly["event_type"] if "event_type" in anomaly else anomaly["type"]
        severity = anomaly["severity"]
        lat, lon = anomaly["location_coord"] if "location_coord" in anomaly else (anomaly["lat"], anomaly["lon"])
        
        # Get base requirements
        base = self.base_requirements.get(event_type, {
            "rescue_teams": 2,
            "ambulances": 2,
            "relief_camps": 1,
            "food_supply_kg": 500,
            "water_supply_liters": 1000,
            "medical_units": 1
        })
        
        # 1. Severity multiplier
        # low = 0.5x, medium = 1.0x, high = 2.5x, extreme = 5.0x
        sev_multipliers = {
            "low": 0.5,
            "medium": 1.0,
            "high": 2.5,
            "extreme": 5.0
        }
        sev_mult = sev_multipliers.get(severity, 1.0)
        
        # 2. Population density multiplier
        pop_mult, area_label = self.get_population_density_multiplier(lat, lon)
        
        # Calculate final allocated quantities (rounded up to nearest integer)
        allocated = {}
        for asset, base_qty in base.items():
            qty = base_qty * sev_mult * pop_mult
            # Round up logic depending on asset type
            if asset in ["food_supply_kg", "water_supply_liters"]:
                allocated[asset] = int(round(qty, -1)) # round to nearest 10
            else:
                allocated[asset] = int(np_ceil(qty))
                
        allocated["affected_region"] = area_label
        allocated["severity_multiplier"] = sev_mult
        allocated["density_multiplier"] = pop_mult
        
        return allocated

def np_dist(lat1, lon1, lat2, lon2):
    import numpy as np
    return np.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

def np_ceil(x):
    import numpy as np
    return int(np.ceil(x))
