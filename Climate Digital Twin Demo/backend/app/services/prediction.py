# backend/app/services/prediction.py

import numpy as np
from datetime import datetime, timedelta
from backend.app.services.config import GRID_SIZE, grid_to_latlon
from backend.app.services.detection import detector

class ClimatePredictionEngine:
    def __init__(self, anomaly_detector=None):
        self.detector = anomaly_detector or detector

    def _spatial_convolution(self, feature_grid, kernel_type="smooth"):
        convolved = feature_grid.copy()
        
        if kernel_type == "smooth":
            kernel = np.array([
                [0.05, 0.1, 0.05],
                [0.1,  0.4, 0.1],
                [0.05, 0.1, 0.05]
            ])
        elif kernel_type == "gradient":
            kernel = np.array([
                [-1, 0, 1],
                [-2, 0, 2],
                [-1, 0, 1]
            ])
        else:
            return convolved
            
        pad_grid = np.pad(feature_grid, 1, mode='edge')
        
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                patch = pad_grid[r:r+3, c:c+3]
                convolved[r, c] = np.sum(patch * kernel)
                
        return convolved

    def _temporal_recurrent_update(self, history, feature_idx):
        steps = len(history)
        if steps < 2:
            return np.zeros((GRID_SIZE, GRID_SIZE))
            
        slices = [h[:, :, feature_idx] for h in history]
        
        velocities = []
        for i in range(1, steps):
            velocities.append(slices[i] - slices[i-1])
            
        avg_velocity = np.mean(velocities, axis=0)
        
        if len(velocities) >= 2:
            accelerations = []
            for i in range(1, len(velocities)):
                accelerations.append(velocities[i] - velocities[i-1])
            avg_accel = np.mean(accelerations, axis=0)
        else:
            avg_accel = np.zeros((GRID_SIZE, GRID_SIZE))
            
        projection = avg_velocity + 0.3 * avg_accel
        return np.clip(projection, -15.0, 15.0)

    def forecast_future_states(self, history, lead_steps=4):
        if not history:
            return []
            
        forecasts = []
        time_labels = ["T+6h (6 hours)", "T+12h (12 hours)", "T+24h (24 hours)", "T+48h (48 hours)"]
        step_offsets = [1, 2, 4, 8]
        
        simulated_history = [h.copy() for h in history]
        
        for idx, offset in enumerate(step_offsets):
            last_state = simulated_history[-1]
            future_state = last_state.copy()
            
            for feat_idx in range(7):
                trend = self._temporal_recurrent_update(simulated_history, feat_idx)
                steps_to_project = offset if idx == 0 else (step_offsets[idx] - step_offsets[idx-1])
                projected_feat = last_state[:, :, feat_idx] + trend * steps_to_project
                
                if feat_idx in [0, 2, 3]:
                    projected_feat = self._spatial_convolution(projected_feat, "smooth")
                    
                if feat_idx in [3, 4]:
                    projected_feat = np.clip(projected_feat, 0.0, 1.0)
                elif feat_idx == 0:
                    projected_feat = np.clip(projected_feat, 0.0, 100.0)
                elif feat_idx == 6:
                    projected_feat = np.clip(projected_feat, 10.0, 100.0)
                elif feat_idx == 5:
                    projected_feat = np.clip(projected_feat, 0.0, 200.0)
                    
                future_state[:, :, feat_idx] = projected_feat
                
            forecasts.append({
                "time_label": time_labels[idx],
                "steps_ahead": offset,
                "state": future_state
            })
            simulated_history.append(future_state)
            
        return forecasts

    def predict_disasters(self, history, ocean_mask):
        """
        Runs the anomaly detector on forecasted states to predict disasters.
        Returns:
            list of future disaster alerts
        """
        forecasts = self.forecast_future_states(history)
        predictions = []
        now = datetime.utcnow()
        
        for f in forecasts:
            detected = self.detector.detect_anomalies(f["state"], ocean_mask)
            hours_ahead = f["steps_ahead"] * 6 # assuming 1 step = 6 hours
            pred_time = now + timedelta(hours=hours_ahead)
            
            for d in detected:
                # Add time window context
                predictions.append({
                    "id": f"pred-{d['id']}-{f['steps_ahead']}",
                    "type": d["type"],
                    "state": d["state"],
                    "district": d["district"],
                    "lat": d["lat"],
                    "lon": d["lon"],
                    "severity": d["severity"],
                    "confidence": float(d["confidence"] * 0.9), # slightly discount confidence in future
                    "predicted_time": pred_time,
                    "probability": float(d["confidence"] * 0.9),
                    "impact": d["impact"],
                    "metrics": d["metrics"],
                    "time_window": f["time_label"]
                })
                
        # Deduplicate predictions to keep the highest severity alert per coordinate/type
        unique_predictions = {}
        for p in predictions:
            key = (p["type"], (p["lat"], p["lon"]))
            if key not in unique_predictions:
                unique_predictions[key] = p
            else:
                existing = unique_predictions[key]
                if p["confidence"] > existing["confidence"]:
                    unique_predictions[key] = p
                    
        return list(unique_predictions.values())

# Global singleton
prediction_engine = ClimatePredictionEngine()
