# tests/test_system.py

import pytest
import numpy as np
from src.config import GRID_SIZE, LAT_MAX, LAT_MIN, LON_MAX, LON_MIN, latlon_to_grid, grid_to_latlon
from src.data_ingestion import ClimateDataIngestor
from src.digital_twin import ClimateDigitalTwin
from src.anomaly_detector import AnomalyDetector
from src.predictor import ClimatePredictionEngine
from src.simulation_engine import ClimateSimulationEngine
from src.optimizer import DecisionOptimizer
from src.resource_allocator import ResourceAllocator
from src.strategies import get_applicable_strategies

def test_config_coordinates():
    # Test conversions
    lat, lon = grid_to_latlon(0, 0)
    assert lat == LAT_MAX
    assert lon == LON_MIN
    
    r, c = latlon_to_grid(lat, lon)
    assert r == 0
    assert c == 0

def test_data_ingestor():
    ingestor = ClimateDataIngestor()
    grid = ingestor.ingest_current_state()
    
    assert grid.shape == (GRID_SIZE, GRID_SIZE, 7)
    # Check that temperature is within sensible physical bounds
    assert np.all(grid[:, :, 1] >= -20.0)
    assert np.all(grid[:, :, 1] <= 60.0)
    # Check precipitation is non-negative
    assert np.all(grid[:, :, 0] >= 0.0)

def test_digital_twin_and_physics():
    ingestor = ClimateDataIngestor()
    twin = ClimateDigitalTwin(history_len=3)
    
    grid1 = ingestor.ingest_current_state()
    twin.update_state(grid1)
    
    assert len(twin.get_history()) == 1
    assert np.array_equal(twin.current_state, grid1)
    
    # Test cloning
    cloned = twin.clone_state()
    assert np.array_equal(cloned, grid1)
    
    # Test physics advancement does not result in NaN values
    advanced = twin.advance_physics(grid1, steps=2)
    assert not np.isnan(advanced).any()

def test_anomaly_detection():
    detector = AnomalyDetector()
    ingestor = ClimateDataIngestor()
    
    # Ingest baseline - should be mostly clean of extreme events
    grid = ingestor.ingest_current_state()
    anomalies = detector.detect_anomalies(grid, ingestor.ocean_mask)
    
    # Inject active trigger for heatwave
    ingestor.set_disaster_trigger("heatwave", center_lat=(27.0, 74.0), intensity=1.5)
    hot_grid = ingestor.ingest_current_state(base_state=grid)
    hot_anomalies = detector.detect_anomalies(hot_grid, ingestor.ocean_mask)
    
    # Should detect at least one heatwave anomaly
    heatwaves = [a for a in hot_anomalies if a["type"] == "heatwave"]
    assert len(heatwaves) > 0
    assert heatwaves[0]["severity"] in ["high", "extreme"]

def test_optimizer_utility():
    ingestor = ClimateDataIngestor()
    twin = ClimateDigitalTwin()
    detector = AnomalyDetector()
    sim_engine = ClimateSimulationEngine(twin, detector)
    optimizer = DecisionOptimizer(sim_engine)
    
    # Setup simple anomaly representation
    anomaly = {
        "type": "flood",
        "grid_pos": (5, 5),
        "lat": 25.0,
        "lon": 78.0,
        "severity": "high",
        "confidence": 85.0,
        "metrics": {"Rainfall": 25.0, "Soil Moisture": 0.9}
    }
    
    # Setup simulated grids
    grid = ingestor.ingest_current_state()
    twin.update_state(grid)
    
    weights = {"risk": 0.5, "cost": 0.2, "feasibility": 0.1, "time": 0.2}
    
    # Test optimization execution
    result = optimizer.optimize_decision(anomaly, ingestor.ocean_mask, weights)
    
    assert "recommended" in result
    assert "all_options" in result
    assert len(result["all_options"]) > 0
    
    # Recommended strategy should have the highest utility score
    rec = result["recommended"]
    assert rec["utility_score"] == max(o["utility_score"] for o in result["all_options"])

def test_resource_allocation():
    allocator = ResourceAllocator()
    
    anomaly = {
        "type": "flood",
        "severity": "extreme",
        "lat": 19.0, # near Mumbai
        "lon": 72.8
    }
    
    resources = allocator.allocate_resources(anomaly)
    assert resources["rescue_teams"] > 0
    assert resources["relief_camps"] > 0
    assert resources["food_supply_kg"] > 0
    assert resources["water_supply_liters"] > 0
    # Confirm Mumbai proximity triggered higher density multiplier
    assert resources["density_multiplier"] == 3.0
