# backend/app/services/optimizer.py

import numpy as np
import uuid
from datetime import datetime
from typing import List, Dict, Any
from backend.app.services.config import GRID_SIZE, latlon_to_grid, STRATEGY_COSTS
from backend.app.services.physics_twin import digital_twin
from backend.app.services.detection import detector

class MitigationStrategyTemplate:
    def __init__(self, id: str, title: str, description: str, advantages: List[str],
                 disadvantages: List[str], implementation_time_hours: float,
                 estimated_cost_inr: float, required_resources: Dict[str, int],
                 expected_risk_reduction_pct: float, feature_modifiers: Dict[int, float],
                 base_feasibility: float = 0.9):
        self.id = id
        self.title = title
        self.description = description
        self.advantages = advantages
        self.disadvantages = disadvantages
        self.implementation_time_hours = implementation_time_hours
        self.estimated_cost_inr = estimated_cost_inr
        self.required_resources = required_resources
        self.expected_risk_reduction_pct = expected_risk_reduction_pct
        self.feature_modifiers = feature_modifiers
        self.base_feasibility = base_feasibility

def get_strategy_templates() -> List[MitigationStrategyTemplate]:
    return [
        MitigationStrategyTemplate(
            id="strat-evac",
            title="Evacuation",
            description="Organize mass evacuation of low-lying/high-risk areas to pre-designated safety shelters.",
            advantages=["Protects human life directly", "Saves vulnerable populations from storm surges"],
            disadvantages=["High implementation time", "High logistical challenge", "High cost"],
            implementation_time_hours=18.0,
            estimated_cost_inr=12000000.0, # 1.2 Crore INR
            required_resources={"NDRF Rescue Unit": 15, "Rescue Helicopter": 4, "Ambulance": 25, "Relief Camp Site": 8},
            expected_risk_reduction_pct=85.0,
            feature_modifiers={},
            base_feasibility=0.65
        ),
        MitigationStrategyTemplate(
            id="strat-drainage",
            title="Drainage Clearing",
            description="Clear storm water drains, culverts, and channels to accelerate flood water runoff.",
            advantages=["Improves local water runoff", "Reduces duration of urban flooding"],
            disadvantages=["Requires manual labor availability", "Limited utility once flooding peaks"],
            implementation_time_hours=8.0,
            estimated_cost_inr=2400000.0, # 24 Lakh INR
            required_resources={"NDRF Rescue Unit": 3, "Municipal Labor Group": 12, "Heavy Excavator": 6},
            expected_risk_reduction_pct=35.0,
            feature_modifiers={4: -0.25, 0: -0.1},
            base_feasibility=0.85
        ),
        MitigationStrategyTemplate(
            id="strat-pumps",
            title="Pump Deployment",
            description="Install high-capacity diesel/electric pumps at water-logging hotspots.",
            advantages=["Actively drains water from roads and critical infrastructure", "Flexible setup"],
            disadvantages=["Requires backup power/fuel supply", "Maintenance heavy"],
            implementation_time_hours=6.0,
            estimated_cost_inr=3600000.0, # 36 Lakh INR
            required_resources={"Municipal Labor Group": 5, "High-Capacity Pump": 20, "Mobile Generator": 10},
            expected_risk_reduction_pct=50.0,
            feature_modifiers={4: -0.35, 0: -0.2},
            base_feasibility=0.75
        ),
        MitigationStrategyTemplate(
            id="strat-prepos",
            title="Resource Pre-positioning",
            description="Pre-deploy food, water, medical kits, and rescue equipment at regional storage depots.",
            advantages=["Ensures rapid response post-event", "Minimizes logistics bottlenecks"],
            disadvantages=["Requires pre-existing storage facilities", "Wasted resources if event path changes"],
            implementation_time_hours=12.0,
            estimated_cost_inr=4800000.0, # 48 Lakh INR
            required_resources={"NDRF Rescue Unit": 5, "Ambulance": 10, "Food Supply Truck": 15},
            expected_risk_reduction_pct=40.0,
            feature_modifiers={},
            base_feasibility=0.80
        ),
        MitigationStrategyTemplate(
            id="strat-firecontain",
            title="Fire containment (Air-drop)",
            description="Deploy specialized firefighting helicopters to dump fire retardant and water on active fronts.",
            advantages=["Direct containment of remote fire lines", "Fast response over rough terrain"],
            disadvantages=["Extremely expensive", "Risk to flight crew under high wind/smoke conditions"],
            implementation_time_hours=4.0,
            estimated_cost_inr=9600000.0, # 96 Lakh INR
            required_resources={"Rescue Helicopter": 6, "Fire Engine Group": 8, "Chemical Retardant Payload": 12},
            expected_risk_reduction_pct=70.0,
            feature_modifiers={1: -8.0, 4: 0.25, 6: 15.0},
            base_feasibility=0.55
        ),
        MitigationStrategyTemplate(
            id="strat-sms",
            title="Emergency SMS & Siren Alert",
            description="Broadcast emergency warning alerts via cellular networks and activate community sirens.",
            advantages=["Ultra-low cost", "Instant deployment", "Alerts maximum population"],
            disadvantages=["Does not prevent infrastructure damage", "Relies on operational network towers"],
            implementation_time_hours=0.5,
            estimated_cost_inr=400000.0, # 4 Lakh INR
            required_resources={"Telecom Broadcast Channel": 1},
            expected_risk_reduction_pct=25.0,
            feature_modifiers={},
            base_feasibility=0.98
        ),
        MitigationStrategyTemplate(
            id="strat-nothing",
            title="Do Nothing",
            description="Maintain standard alert levels without deploying extra resources.",
            advantages=["Zero cost"],
            disadvantages=["Maximum exposure to damage", "No risk reduction"],
            implementation_time_hours=0.0,
            estimated_cost_inr=0.0,
            required_resources={},
            expected_risk_reduction_pct=0.0,
            feature_modifiers={},
            base_feasibility=1.0
        )
    ]

def get_applicable_strategies(anomaly_type: str) -> List[MitigationStrategyTemplate]:
    templates = get_strategy_templates()
    if anomaly_type == "cyclone":
        return [s for s in templates if s.title in ["Evacuation", "Emergency SMS & Siren Alert", "Resource Pre-positioning", "Do Nothing"]]
    elif anomaly_type in ("flood", "heavy_rain", "urban_flood"):
        return [s for s in templates if s.title in ["Pump Deployment", "Drainage Clearing", "Evacuation", "Emergency SMS & Siren Alert", "Do Nothing"]]
    elif anomaly_type in ("heatwave", "urban_heat_island"):
        return [s for s in templates if s.title in ["Emergency SMS & Siren Alert", "Resource Pre-positioning", "Do Nothing"]]
    elif anomaly_type in ("drought", "cold_wave"):
        return [s for s in templates if s.title in ["Resource Pre-positioning", "Do Nothing"]]
    elif anomaly_type == "forest_fire":
        return [s for s in templates if s.title in ["Fire containment (Air-drop)", "Evacuation", "Emergency SMS & Siren Alert", "Do Nothing"]]
    else:
        return templates

class DecisionOptimizer:
    def __init__(self, twin=None, anomaly_detector=None):
        self.twin = twin or digital_twin
        self.detector = anomaly_detector or detector

    def _compute_local_severity(self, state, tr_r, tr_c, anomaly_type, ocean_mask):
        score = 0.0
        for r in range(max(0, tr_r-1), min(GRID_SIZE, tr_r+2)):
            for c in range(max(0, tr_c-1), min(GRID_SIZE, tr_c+2)):
                anomalies = self.detector.detect_anomalies(state, ocean_mask)
                for a in anomalies:
                    if a["lat"] == float(r) and a["lon"] == float(c): # or close proximity
                        continue
                    # Approximate match
                    if a["type"] == anomaly_type:
                        sev_weights = {"low": 1.0, "moderate": 2.0, "high": 3.0, "severe": 4.0, "critical": 5.0}
                        score += sev_weights.get(a["severity"], 1.0)
        # Fallback to general threshold severity if empty
        return max(1.0, score)

    def compute_utility(self, sim_res: Dict[str, Any], weights: Dict[str, float]) -> float:
        w_risk = weights.get("risk", 0.45)
        w_cost = weights.get("cost", 0.20)
        w_feas = weights.get("feasibility", 0.15)
        w_time = weights.get("time", 0.20)
        
        total_w = w_risk + w_cost + w_feas + w_time
        if total_w == 0:
            return 0.0
            
        risk_norm = sim_res["risk_reduction_pct"] / 100.0
        
        max_cost = 15000000.0 # 1.5 Crore max cost
        cost_norm = 1.0 - (sim_res["cost"] / max_cost)
        cost_norm = np.clip(cost_norm, 0.0, 1.0)
        
        feas_norm = sim_res["feasibility_score"]
        time_norm = sim_res["time_efficiency"]
        
        utility = (
            w_risk * risk_norm +
            w_cost * cost_norm +
            w_feas * feas_norm +
            w_time * time_norm
        ) / total_w
        
        return float(round(utility * 100.0, 1))

    def simulate_strategy(self, strategy: MitigationStrategyTemplate, anomaly: Dict[str, Any], ocean_mask) -> Dict[str, Any]:
        grid_sim = self.twin.clone_state()
        if grid_sim is None:
            # Create a mock/empty grid if none available (e.g. at startup)
            grid_sim = np.zeros((GRID_SIZE, GRID_SIZE, 7))
            grid_sim[:, :, 1] = 28.0 # temp
            grid_sim[:, :, 4] = 0.5 # soil moisture
            
        # Coordinates mapping is Lat vs Lon
        from backend.app.services.config import latlon_to_grid
        tr_r, tr_c = latlon_to_grid(anomaly["location"]["lat"], anomaly["location"]["lon"])
        
        original_severity_score = self._compute_local_severity(grid_sim, tr_r, tr_c, anomaly["type"], ocean_mask)
        
        # Apply features
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                dist = np.sqrt((r - tr_r)**2 + (c - tr_c)**2)
                if dist > 3.0:
                    continue
                influence = np.exp(-dist / 1.5)
                
                for feat_idx, mod in strategy.feature_modifiers.items():
                    if mod < 0:
                        grid_sim[r, c, feat_idx] *= (1.0 + mod * influence)
                    else:
                        grid_sim[r, c, feat_idx] += mod * influence
                        
                # Clip bounds
                grid_sim[r, c, 3] = np.clip(grid_sim[r, c, 3], 0.0, 1.0)
                grid_sim[r, c, 4] = np.clip(grid_sim[r, c, 4], 0.05, 1.0)
                grid_sim[r, c, 6] = np.clip(grid_sim[r, c, 6], 10.0, 100.0)
                grid_sim[r, c, 0] = np.clip(grid_sim[r, c, 0], 0.0, 100.0)
                grid_sim[r, c, 5] = np.clip(grid_sim[r, c, 5], 0.0, 200.0)
                
        # Natural physics twin steps
        grid_sim = self.twin.advance_physics(grid_sim, steps=2, wind_dir=(-1, 1))
        
        residual_severity_score = self._compute_local_severity(grid_sim, tr_r, tr_c, anomaly["type"], ocean_mask)
        
        # Calculate Risk Reduction
        if original_severity_score > 0:
            risk_reduction = (original_severity_score - residual_severity_score) / original_severity_score
            risk_reduction_pct = float(np.clip(risk_reduction * 100.0, 0.0, 100.0))
        else:
            risk_reduction_pct = 0.0
            
        # Strategy specific overrides
        if strategy.title == "Evacuation":
            risk_reduction_pct = 85.0
        elif strategy.title == "Resource Pre-positioning":
            risk_reduction_pct = 40.0
        elif strategy.title == "Emergency SMS & Siren Alert":
            risk_reduction_pct = 25.0
        elif strategy.title == "Do Nothing":
            risk_reduction_pct = 0.0
            
        time_efficiencies = {
            "Emergency SMS & Siren Alert": 0.95,
            "Drainage Clearing": 0.70,
            "Pump Deployment": 0.75,
            "Evacuation": 0.35,
            "Fire containment (Air-drop)": 0.65,
            "Resource Pre-positioning": 0.50,
            "Do Nothing": 0.0
        }
        time_eff = time_efficiencies.get(strategy.title, 0.5)
        
        feasibility = strategy.base_feasibility
        
        # Impact model calculations
        impact = anomaly.get("impact", {})
        pop = impact.get("population", 100000)
        infra = impact.get("infrastructure", 50)
        
        # Calculate survivors & economic benefit
        pop_saved = int(pop * (risk_reduction_pct / 100.0))
        econ_saved = float(pop * (risk_reduction_pct / 100.0) * 1500.0) # mock value multiplier
        water_saved = float(pop_saved * 25.0) if anomaly["type"] == "drought" else 0.0
        infra_saved = float(infra * (risk_reduction_pct / 100.0))
        
        # Format grids for Pydantic serialization (converting float grids to list of lists)
        before_state_flat = {"avg_temp": float(np.mean(self.twin.current_state[:, :, 1])) if self.twin.current_state is not None else 28.0}
        after_state_flat = {"avg_temp": float(np.mean(grid_sim[:, :, 1]))}

        return {
            "strategy_id": strategy.id,
            "ran_at": datetime.utcnow(),
            "before_state": before_state_flat,
            "after_state": after_state_flat,
            "risk_reduction_pct": float(round(risk_reduction_pct, 1)),
            "population_saved": pop_saved,
            "economic_loss_reduced_inr": econ_saved,
            "water_saved_litres": water_saved,
            "infrastructure_saved_pct": float(round(infra_saved, 1)),
            "success": bool(risk_reduction_pct > 20.0 or strategy.title == "Do Nothing"),
            "cost": float(strategy.estimated_cost_inr),
            "feasibility_score": float(feasibility),
            "time_efficiency": float(time_eff),
            "strategy_name": strategy.title
        }

    def optimize_decision(self, anomaly: Dict[str, Any], ocean_mask, weights=None) -> Dict[str, Any]:
        if weights is None:
            weights = {"risk": 0.45, "cost": 0.20, "feasibility": 0.15, "time": 0.20}
            
        applicable = get_applicable_strategies(anomaly["type"])
        results = []
        for strat in applicable:
            res = self.simulate_strategy(strat, anomaly, ocean_mask)
            res["score"] = self.compute_utility(res, weights)
            results.append(res)
            
        # Sort by composite AI score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Combined strategy logic (similar to prototype)
        best_option = results[0] if results else None
        
        # If best strategy has low risk reduction (< 35%), we can simulate a combined one
        if best_option and best_option["risk_reduction_pct"] < 35.0 and len(results) > 2:
            combined = self._generate_combined_strategy(results, anomaly, ocean_mask, weights)
            if combined:
                results.insert(0, combined)
                best_option = combined
                
        return {
            "recommended": best_option,
            "all_options": results
        }

    def _generate_combined_strategy(self, scored_options, anomaly, ocean_mask, weights):
        warning_opt = next((x for x in scored_options if x["strategy_name"] == "Emergency SMS & Siren Alert"), None)
        physical_opts = [x for x in scored_options if x["strategy_name"] not in ["Emergency SMS & Siren Alert", "Do Nothing", "Evacuation"]]
        
        if not warning_opt or not physical_opts:
            return None
            
        phys_opt = physical_opts[0]
        
        combined_name = f"{phys_opt['strategy_name']} + Emergency SMS Warning"
        combined_cost = phys_opt["cost"] + warning_opt["cost"]
        feasibility = min(phys_opt["feasibility_score"], warning_opt["feasibility_score"]) - 0.05
        
        r1 = phys_opt["risk_reduction_pct"] / 100.0
        r2 = warning_opt["risk_reduction_pct"] / 100.0
        combined_reduction = (r1 + r2 - (r1 * r2)) * 100.0
        
        time_eff = (phys_opt["time_efficiency"] + warning_opt["time_efficiency"]) / 2.0
        
        pop = anomaly.get("impact", {}).get("population", 100000)
        infra = anomaly.get("impact", {}).get("infrastructure", 50)
        
        pop_saved = int(pop * (combined_reduction / 100.0))
        econ_saved = float(pop * (combined_reduction / 100.0) * 1500.0)
        water_saved = float(pop_saved * 25.0) if anomaly["type"] == "drought" else 0.0
        infra_saved = float(infra * (combined_reduction / 100.0))

        sim_res = {
            "strategy_id": f"comb-{phys_opt['strategy_id']}",
            "ran_at": datetime.utcnow(),
            "before_state": phys_opt["before_state"],
            "after_state": phys_opt["after_state"],
            "risk_reduction_pct": float(round(combined_reduction, 1)),
            "population_saved": pop_saved,
            "economic_loss_reduced_inr": econ_saved,
            "water_saved_litres": water_saved,
            "infrastructure_saved_pct": float(round(infra_saved, 1)),
            "success": True,
            "cost": float(combined_cost),
            "feasibility_score": float(round(max(0.1, feasibility), 2)),
            "time_efficiency": float(round(time_eff, 2)),
            "strategy_name": combined_name
        }
        
        sim_res["score"] = self.compute_utility(sim_res, weights)
        return sim_res

# Global singleton
optimizer = DecisionOptimizer()
