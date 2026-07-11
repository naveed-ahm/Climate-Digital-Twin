# src/strategies.py

from src.config import STRATEGY_COSTS

class MitigationStrategy:
    def __init__(self, name, cost, feature_modifiers, base_feasibility=0.9):
        self.name = name
        self.cost = cost
        self.feature_modifiers = feature_modifiers # dict of {feature_idx: modifier_multiplier_or_delta}
        self.base_feasibility = base_feasibility

def get_strategy_templates():
    """
    Returns templates of all emergency mitigation strategies.
    Feature Index mapping:
      0: Precipitation (mm/hr)
      1: Temperature (°C)
      2: SST (°C)
      3: Cloud_Cover (0-1)
      4: Soil_Moisture (0-1)
      5: Wind_Speed (km/h)
      6: Humidity (%)
    """
    return [
        MitigationStrategy(
            name="Evacuation",
            cost=STRATEGY_COSTS["Evacuation"],
            feature_modifiers={}, # Does not change weather physics directly, acts on human exposure
            base_feasibility=0.65
        ),
        MitigationStrategy(
            name="Drainage Clearing",
            cost=STRATEGY_COSTS["Drainage Clearing"],
            # Reduces water logging by lowering soil moisture saturation delta
            feature_modifiers={4: -0.25, 0: -0.1},
            base_feasibility=0.85
        ),
        MitigationStrategy(
            name="Pump Deployment",
            cost=STRATEGY_COSTS["Pump Deployment"],
            # Actively reduces precipitation accumulation impact and soil moisture
            feature_modifiers={4: -0.35, 0: -0.2},
            base_feasibility=0.75
        ),
        MitigationStrategy(
            name="Resource Pre-positioning",
            cost=STRATEGY_COSTS["Resource Pre-positioning"],
            feature_modifiers={}, # Improves readiness, no direct weather impact
            base_feasibility=0.80
        ),
        MitigationStrategy(
            name="Fire containment (Air-drop)",
            cost=STRATEGY_COSTS["Fire containment (Air-drop)"],
            # Drops water to cool temperature, increase soil moisture, and dampen humidity
            feature_modifiers={1: -8.0, 4: 0.25, 6: 15.0}, 
            base_feasibility=0.55
        ),
        MitigationStrategy(
            name="Emergency SMS & Siren Alert",
            cost=STRATEGY_COSTS["Emergency SMS & Siren Alert"],
            feature_modifiers={}, # Communication only
            base_feasibility=0.98
        ),
        MitigationStrategy(
            name="Do Nothing",
            cost=STRATEGY_COSTS["Do Nothing"],
            feature_modifiers={},
            base_feasibility=1.0
        )
    ]

def get_applicable_strategies(anomaly_type):
    """Filters strategies applicable to specific disaster types."""
    templates = get_strategy_templates()
    
    if anomaly_type == "cyclone":
        # Evac, Alerts, Pre-positioning
        return [s for s in templates if s.name in ["Evacuation", "Emergency SMS & Siren Alert", "Resource Pre-positioning", "Do Nothing"]]
    elif anomaly_type == "flood" or anomaly_type == "extreme_rainfall":
        # Pumps, Drainage, Evac, Alerts
        return [s for s in templates if s.name in ["Pump Deployment", "Drainage Clearing", "Evacuation", "Emergency SMS & Siren Alert", "Do Nothing"]]
    elif anomaly_type == "heatwave":
        # Alerts, Resource pre-positioning (shelters/water)
        return [s for s in templates if s.name in ["Emergency SMS & Siren Alert", "Resource Pre-positioning", "Do Nothing"]]
    elif anomaly_type == "drought":
        # Resources pre-positioning (water distribution)
        return [s for s in templates if s.name in ["Resource Pre-positioning", "Do Nothing"]]
    elif anomaly_type == "forest_fire":
        # Fire containment, evacuation, alerts
        return [s for s in templates if s.name in ["Fire containment (Air-drop)", "Evacuation", "Emergency SMS & Siren Alert", "Do Nothing"]]
    else:
        return templates
