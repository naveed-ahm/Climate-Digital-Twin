# src/optimizer.py

import numpy as np

class DecisionOptimizer:
    def __init__(self, simulation_engine):
        self.sim_engine = simulation_engine

    def compute_utility(self, sim_res, weights):
        """
        Computes the utility score (0 to 100) of a strategy based on weights.
        Weights is a dict of: {risk: float, cost: float, feasibility: float, time: float}
        """
        w_risk = weights.get("risk", 0.4)
        w_cost = weights.get("cost", 0.2)
        w_feas = weights.get("feasibility", 0.2)
        w_time = weights.get("time", 0.2)
        
        total_w = w_risk + w_cost + w_feas + w_time
        if total_w == 0:
            return 0.0
            
        # Normalize metrics:
        # Risk Reduction: 0 to 100% -> 0.0 to 1.0
        risk_norm = sim_res["risk_reduction_pct"] / 100.0
        
        # Cost: 0 to $150,000 -> 0.0 (expensive) to 1.0 (free)
        max_cost = 150000.0
        cost_norm = 1.0 - (sim_res["cost"] / max_cost)
        cost_norm = np.clip(cost_norm, 0.0, 1.0)
        
        # Feasibility: already 0.0 to 1.0
        feas_norm = sim_res["feasibility_score"]
        
        # Time Efficiency: already 0.0 to 1.0
        time_norm = sim_res["time_efficiency"]
        
        # Weighted Utility
        utility = (
            w_risk * risk_norm +
            w_cost * cost_norm +
            w_feas * feas_norm +
            w_time * time_norm
        ) / total_w
        
        return round(utility * 100.0, 1)

    def optimize_decision(self, anomaly, ocean_mask, weights=None):
        """
        Runs the closed-loop optimization cycle.
        Simulates individual strategies, scores them, and determines the optimal path.
        """
        if weights is None:
            weights = {"risk": 0.4, "cost": 0.2, "feasibility": 0.2, "time": 0.2}

        # 1. Simulate all individual strategies
        sim_results = self.sim_engine.simulate_all_strategies(anomaly, ocean_mask)
        
        scored_strategies = []
        for res in sim_results:
            # Skip strategies that are completely infeasible (e.g. feasibility < 0.2)
            if res["feasibility_score"] < 0.2:
                continue
                
            utility = self.compute_utility(res, weights)
            res["utility_score"] = utility
            scored_strategies.append(res)
            
        # Sort by utility score descending
        scored_strategies.sort(key=lambda x: x["utility_score"], reverse=True)
        
        if not scored_strategies:
            # Fallback to do nothing
            return {"recommended": None, "all_options": []}

        best_option = scored_strategies[0]
        
        # 2. Iterative optimization: If risk reduction of the best option is low (< 35%) 
        # and we have separate complementary options, let's simulate a COMBINED strategy.
        # Example: Emergency Alert (high feasibility, low cost, 25% risk reduction) 
        # + Drainage Clearing (medium cost, 35% risk reduction).
        if best_option["risk_reduction_pct"] < 35.0 and len(scored_strategies) > 2:
            combined_candidate = self._generate_combined_strategy(scored_strategies, anomaly, ocean_mask, weights)
            if combined_candidate and combined_candidate["utility_score"] > best_option["utility_score"]:
                scored_strategies.insert(0, combined_candidate)
                best_option = combined_candidate

        return {
            "recommended": best_option,
            "all_options": scored_strategies
        }

    def _generate_combined_strategy(self, scored_options, anomaly, ocean_mask, weights):
        """
        Helper that combines the top low-cost warning strategy with a physical strategy,
        simulates the combined outcome, and returns a new candidate score.
        """
        # Find warning/alert strategy
        warning_opt = next((x for x in scored_options if x["strategy_name"] == "Emergency SMS & Siren Alert"), None)
        # Find top physical strategy that is not "Do Nothing" or "Evacuation"
        physical_opts = [x for x in scored_options if x["strategy_name"] not in ["Emergency SMS & Siren Alert", "Do Nothing", "Evacuation"]]
        
        if not warning_opt or not physical_opts:
            return None
            
        phys_opt = physical_opts[0]
        
        # Combined name
        combined_name = f"{phys_opt['strategy_name']} + Emergency SMS Warning"
        combined_cost = phys_opt["cost"] + warning_opt["cost"]
        
        # Feasibility is limited by the harder of the two
        feasibility = min(phys_opt["feasibility_score"], warning_opt["feasibility_score"]) - 0.05
        
        # Combined risk reduction (probabilistic union: A + B - AB)
        r1 = phys_opt["risk_reduction_pct"] / 100.0
        r2 = warning_opt["risk_reduction_pct"] / 100.0
        combined_reduction = (r1 + r2 - (r1 * r2)) * 100.0
        
        # Time efficiency is weighted
        time_eff = (phys_opt["time_efficiency"] + warning_opt["time_efficiency"]) / 2.0
        
        sim_res = {
            "strategy_name": combined_name,
            "cost": combined_cost,
            "risk_reduction_pct": round(combined_reduction, 1),
            "feasibility_score": round(max(0.1, feasibility), 2),
            "time_efficiency": round(time_eff, 2),
            "residual_severity": round(phys_opt["residual_severity"] * 0.7, 2), # enhanced mitigation
            "original_severity": phys_opt["original_severity"]
        }
        
        sim_res["utility_score"] = self.compute_utility(sim_res, weights)
        return sim_res
