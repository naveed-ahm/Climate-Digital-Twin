# src/simulation_engine.py

import numpy as np
from src.config import GRID_SIZE, latlon_to_grid
from src.strategies import get_applicable_strategies
from src.anomaly_detector import AnomalyDetector

class ClimateSimulationEngine:
    def __init__(self, twin, detector=None):
        self.twin = twin
        self.detector = detector or AnomalyDetector()

    def simulate_strategy_impact(self, strategy, anomaly, ocean_mask):
        """
        Simulates applying a strategy to mitigate a specific anomaly.
        Returns:
            dict containing simulation results.
        """
        # 1. Clone the current digital twin state
        grid_sim = self.twin.clone_state()
        if grid_sim is None:
            return None
            
        tr_r, tr_c = anomaly["grid_pos"]
        
        # Calculate original local anomaly score
        # Let's assess severity in a 3x3 local patch around the anomaly
        original_severity_score = self._compute_local_severity(grid_sim, tr_r, tr_c, anomaly["type"], ocean_mask)
        
        # 2. Apply modifications on the grid with spatial decay
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                dist = np.sqrt((r - tr_r)**2 + (c - tr_c)**2)
                if dist > 3.0:
                    continue  # Limit impact radius to 3 grid units
                
                # Spatial influence factor
                influence = np.exp(-dist / 1.5)
                
                for feat_idx, mod in strategy.feature_modifiers.items():
                    if mod < 0:
                        # Negative mod represents fractional reduction (e.g. -0.25 is a 25% reduction)
                        reduction = 1.0 + mod * influence
                        grid_sim[r, c, feat_idx] *= reduction
                    else:
                        # Positive mod is a delta addition (e.g. +10.0 humidity)
                        grid_sim[r, c, feat_idx] += mod * influence
                        
                # Keep variables within physical limits
                grid_sim[r, c, 3] = np.clip(grid_sim[r, c, 3], 0.0, 1.0) # Cloud Cover
                grid_sim[r, c, 4] = np.clip(grid_sim[r, c, 4], 0.05, 1.0) # Soil Moisture
                grid_sim[r, c, 6] = np.clip(grid_sim[r, c, 6], 10.0, 100.0) # Humidity
                grid_sim[r, c, 0] = np.clip(grid_sim[r, c, 0], 0.0, 100.0) # Rain
                grid_sim[r, c, 5] = np.clip(grid_sim[r, c, 5], 0.0, 200.0) # Wind Speed

        # 3. Advance physics for a few steps (simulating 6-12 hours of natural dispersion)
        # Wind vector based on current anomaly coordinates
        grid_sim = self.twin.advance_physics(grid_sim, steps=2, wind_dir=(-1, 1))

        # 4. Re-evaluate local anomaly score
        residual_severity_score = self._compute_local_severity(grid_sim, tr_r, tr_c, anomaly["type"], ocean_mask)
        
        # Calculate Risk Reduction %
        if original_severity_score > 0:
            risk_reduction = (original_severity_score - residual_severity_score) / original_severity_score
            risk_reduction_pct = float(np.clip(risk_reduction * 100.0, 0.0, 100.0))
        else:
            risk_reduction_pct = 0.0
            
        # Strategy-specific adjustments
        # Certain strategies like Evacuation do not change climate variables but directly reduce risk
        if strategy.name == "Evacuation":
            risk_reduction_pct = 85.0  # Moves people out of danger zone
        elif strategy.name == "Resource Pre-positioning":
            risk_reduction_pct = 40.0  # Builds supply readiness
        elif strategy.name == "Emergency SMS & Siren Alert":
            risk_reduction_pct = 25.0  # Fast warning, minor physical impact but saves lives
            
        if strategy.name == "Do Nothing":
            risk_reduction_pct = 0.0

        # Calculate time efficiency (how fast it works)
        time_efficiencies = {
            "Emergency SMS & Siren Alert": 0.95,
            "Drainage Clearing": 0.70,
            "Pump Deployment": 0.75,
            "Evacuation": 0.35, # Slow to implement
            "Fire containment (Air-drop)": 0.65,
            "Resource Pre-positioning": 0.50,
            "Do Nothing": 0.0
        }
        time_eff = time_efficiencies.get(strategy.name, 0.5)

        # Dynamic feasibility based on storm intensity/wind speed
        feasibility = strategy.base_feasibility
        if anomaly["type"] == "cyclone":
            wind_speed = anomaly["metrics"].get("Wind Speed", 0)
            if wind_speed > 100.0 and strategy.name == "Evacuation":
                feasibility -= 0.15  # Heavy winds hamper transport
        elif anomaly["type"] == "forest_fire":
            wind_speed = anomaly["metrics"].get("Wind Speed", 0)
            if wind_speed > 40.0 and strategy.name == "Fire containment (Air-drop)":
                feasibility -= 0.25  # High winds make air drops dangerous

        return {
            "strategy_name": strategy.name,
            "cost": strategy.cost,
            "risk_reduction_pct": round(risk_reduction_pct, 1),
            "feasibility_score": round(max(0.1, feasibility), 2),
            "time_efficiency": round(time_eff, 2),
            "residual_severity": round(residual_severity_score, 2),
            "original_severity": round(original_severity_score, 2)
        }

    def _compute_local_severity(self, state, tr_r, tr_c, anomaly_type, ocean_mask):
        """
        Scans a 3x3 region around the coordinate and returns a severity index.
        """
        score = 0.0
        for r in range(max(0, tr_r-1), min(GRID_SIZE, tr_r+2)):
            for c in range(max(0, tr_c-1), min(GRID_SIZE, tr_c+2)):
                # Detect anomalies on this state copy
                anomalies = self.detector.detect_anomalies(state, ocean_mask)
                for a in anomalies:
                    if a["grid_pos"] == (r, c) and a["type"] == anomaly_type:
                        sev_weights = {"low": 1.0, "medium": 2.0, "high": 3.0, "extreme": 4.0}
                        score += sev_weights.get(a["severity"], 1.0)
        return score

    def simulate_all_strategies(self, anomaly, ocean_mask):
        """Simulates all applicable strategies for the given anomaly."""
        strategies = get_applicable_strategies(anomaly["type"])
        results = []
        for s in strategies:
            res = self.simulate_strategy_impact(s, anomaly, ocean_mask)
            if res:
                results.append(res)
        return results
