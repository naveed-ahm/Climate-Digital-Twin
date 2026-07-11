# src/predictor.py

import numpy as np
from src.config import GRID_SIZE, grid_to_latlon
from src.anomaly_detector import AnomalyDetector

class ClimatePredictionEngine:
    def __init__(self, detector=None):
        self.detector = detector or AnomalyDetector()

    def _spatial_convolution(self, feature_grid, kernel_type="smooth"):
        """
        Simulates a spatial CNN convolution filter on the grid.
        Identifies spatial gradients, hotspots, and accumulation patterns.
        """
        convolved = feature_grid.copy()
        
        # Simple convolution kernels
        if kernel_type == "smooth":
            kernel = np.array([
                [0.05, 0.1, 0.05],
                [0.1,  0.4, 0.1],
                [0.05, 0.1, 0.05]
            ])
        elif kernel_type == "gradient":
            # Sobel-like spatial gradient detector
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
                # Extract 3x3 patch
                patch = pad_grid[r:r+3, c:c+3]
                convolved[r, c] = np.sum(patch * kernel)
                
        return convolved

    def _temporal_recurrent_update(self, history, feature_idx):
        """
        Simulates an LSTM temporal sequence prediction.
        Analyzes historical trends (rates of change, acceleration) to extrapolate.
        """
        steps = len(history)
        if steps < 2:
            return np.zeros((GRID_SIZE, GRID_SIZE)) # Not enough history to project trends
            
        # Extract the specific feature slices
        slices = [h[:, :, feature_idx] for h in history]
        
        # Compute first order difference (velocity) and second order (acceleration)
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
            
        # Recurrent projection formula: X_new = X_current + velocity + 0.5 * accel
        # Clipped to prevent numerical runaway
        projection = avg_velocity + 0.3 * avg_accel
        return np.clip(projection, -15.0, 15.0)

    def forecast_future_states(self, history, lead_steps=4):
        """
        Projects the climate state tensor into the future.
        Returns:
            list of dicts containing the forecast step index, grid, and time label.
        """
        if not history:
            return []
            
        current_state = history[-1]
        forecasts = []
        
        # We will predict: T+6h, T+12h, T+24h, T+48h (assuming 1 step = 6 hours)
        time_labels = ["T+6h (6 hours)", "T+12h (12 hours)", "T+24h (24 hours)", "T+48h (48 hours)"]
        step_offsets = [1, 2, 4, 8]
        
        simulated_history = [h.copy() for h in history]
        
        for idx, offset in enumerate(step_offsets):
            last_state = simulated_history[-1]
            future_state = last_state.copy()
            
            # Predict each feature independently
            for feat_idx in range(7):
                # 1. Temporal trend projection (LSTM-like)
                trend = self._temporal_recurrent_update(simulated_history, feat_idx)
                
                # Apply trend for the steps between forecasts
                steps_to_project = offset if idx == 0 else (step_offsets[idx] - step_offsets[idx-1])
                projected_feat = last_state[:, :, feat_idx] + trend * steps_to_project
                
                # 2. Spatial smoothing / physics constraint (CNN-like)
                # Precipitation (0), Cloud Cover (3), SST (2) smooth out spatially
                if feat_idx in [0, 2, 3]:
                    projected_feat = self._spatial_convolution(projected_feat, "smooth")
                    
                # Climate feature bounding limits
                if feat_idx in [3, 4]: # Cloud cover, Soil Moisture
                    projected_feat = np.clip(projected_feat, 0.0, 1.0)
                elif feat_idx == 0: # Rain
                    projected_feat = np.clip(projected_feat, 0.0, 100.0)
                elif feat_idx == 6: # Humidity
                    projected_feat = np.clip(projected_feat, 10.0, 100.0)
                elif feat_idx == 5: # Wind Speed
                    projected_feat = np.clip(projected_feat, 0.0, 200.0)
                    
                future_state[:, :, feat_idx] = projected_feat
                
            forecasts.append({
                "time_label": time_labels[idx],
                "steps_ahead": offset,
                "state": future_state
            })
            
            # Append future state to simulated history to project further
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
        
        for f in forecasts:
            detected = self.detector.detect_anomalies(f["state"], ocean_mask)
            for d in detected:
                # Add time window context
                predictions.append({
                    "event_type": d["type"],
                    "location_coord": (d["lat"], d["lon"]),
                    "grid_pos": d["grid_pos"],
                    "time_window": f["time_label"],
                    "severity": d["severity"],
                    "confidence": d["confidence"] * 0.9,  # slightly discount confidence in future
                    "metrics": d["metrics"]
                })
                
        # Deduplicate predictions to keep the highest severity alert per coordinate
        unique_predictions = {}
        for p in predictions:
            key = (p["event_type"], p["grid_pos"])
            if key not in unique_predictions:
                unique_predictions[key] = p
            else:
                # Keep the earlier prediction or higher severity
                existing = unique_predictions[key]
                if p["confidence"] > existing["confidence"]:
                    unique_predictions[key] = p
                    
        return list(unique_predictions.values())
