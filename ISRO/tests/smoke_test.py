"""End-to-end pipeline smoke test."""
from src.data_ingestion import ClimateDataIngestor
from src.digital_twin import ClimateDigitalTwin
from src.anomaly_detector import AnomalyDetector
from src.predictor import ClimatePredictionEngine
from src.simulation_engine import ClimateSimulationEngine
from src.optimizer import DecisionOptimizer
from src.resource_allocator import ResourceAllocator
from src.output_generator import OutputGenerator

ingestor = ClimateDataIngestor()
twin = ClimateDigitalTwin(history_len=5)
detector = AnomalyDetector()
predictor = ClimatePredictionEngine(detector)
sim_engine = ClimateSimulationEngine(twin, detector)
optimizer = DecisionOptimizer(sim_engine)
allocator = ResourceAllocator()
gen = OutputGenerator()

# Warm up with 5 ticks of normal weather
for _ in range(5):
    grid = ingestor.ingest_current_state(base_state=twin.current_state)
    twin.update_state(grid)

# Inject cyclone trigger
ingestor.set_disaster_trigger("cyclone", center_lat=(20.0, 86.5), intensity=1.5)
grid = ingestor.ingest_current_state(base_state=twin.current_state)
twin.update_state(grid)

# Detect anomalies
anomalies = detector.detect_anomalies(twin.current_state, ingestor.ocean_mask)
print(f"Active Anomalies Detected: {len(anomalies)}")
for a in anomalies[:3]:
    print(f"  -> [{a['severity'].upper()}] {a['type']} at ({a['lat']:.1f}, {a['lon']:.1f}) | confidence {a['confidence']:.1f}%")

# Predict future events
preds = predictor.predict_disasters(twin.get_history(), ingestor.ocean_mask)
print(f"Future Predictions: {len(preds)}")
for p in preds[:2]:
    print(f"  -> {p['event_type']} in {p['time_window']} | severity: {p['severity']}")

# Optimize response
result = None
if anomalies:
    result = optimizer.optimize_decision(anomalies[0], ingestor.ocean_mask)
    rec = result["recommended"]
    if rec:
        print(f"Best Strategy: {rec['strategy_name']} | Utility: {rec['utility_score']}% | Risk Cut: {rec['risk_reduction_pct']}%")
    print(f"All Options Evaluated: {len(result['all_options'])}")

# Resource allocation
if anomalies:
    a = anomalies[0]
    ev = {"type": a["type"], "severity": a["severity"], "lat": a["lat"], "lon": a["lon"]}
    resources = allocator.allocate_resources(ev)
    print(f"Resource Allocation: {resources['rescue_teams']} NDRF teams, {resources['ambulances']} ambulances")

# SMS alert output
if anomalies and result and result["recommended"]:
    sms = gen.generate_sms_alert(anomalies[0], result["recommended"])
    print("--- SMS Alert ---")
    print(sms)

print("PIPELINE OK")
