# backend/app/main.py

import asyncio
import json
import logging
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import engine, Base, SessionLocal
from backend.app.api.router import router as api_router, get_layers_payload
from backend.app.ws.live import manager

from backend.app.services.synthetic_data import ingestor
from backend.app.services.physics_twin import digital_twin
from backend.app.services.detection import detector
from backend.app.services.prediction import prediction_engine
from backend.app.models.models import ClimateEventModel, AuditLogModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bhoomi_drishti")

app = FastAPI(
    title="Bhoomi-Drishti API",
    description="AI Digital Twin for India's Climate Resilience",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API
app.mount("/api", api_router)

# WebSocket Live broadcasing endpoint
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial state immediately
        initial_payload = {
            "type": "initial_state",
            "sync_pct": 98.5,
            "health": "optimal",
            "timestamp": datetime.utcnow().isoformat(),
            "active_alerts_count": len(detector.detect_anomalies(digital_twin.current_state, ingestor.ocean_mask)) if digital_twin.current_state is not None else 0
        }
        await websocket.send_json(initial_payload)
        
        while True:
            # Keep connection alive (heartbeat or listen for manual triggers)
            data = await websocket.receive_text()
            # If fronted requests meteorology trigger injection
            try:
                payload = json.loads(data)
                if payload.get("action") == "inject_trigger":
                    trigger_name = payload.get("trigger_name")
                    intensity = payload.get("intensity", 1.0)
                    
                    logger.info(f"WebSocket trigger injection: {trigger_name} ({intensity})")
                    if trigger_name == "Normal Weather":
                        ingestor.clear_trigger()
                    elif trigger_name == "Cyclone (Odisha Coast)":
                        ingestor.set_disaster_trigger("cyclone", center_lat=(20.2, 86.0), intensity=intensity)
                    elif trigger_name == "Heatwave (North Plains)":
                        ingestor.set_disaster_trigger("heatwave", center_lat=(26.0, 72.0), intensity=intensity)
                    elif trigger_name == "Monsoon Downpour (Mumbai)":
                        ingestor.set_disaster_trigger("monsoon", center_lat=(19.0, 72.8), intensity=intensity)
                    elif trigger_name == "Severe Drought (Deccan)":
                        ingestor.set_disaster_trigger("drought", center_lat=(15.0, 76.0), intensity=intensity)
                        
                    # Force immediate update step
                    await run_simulation_step()
            except Exception as e:
                logger.error(f"Error handling WebSocket client data: {e}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def run_simulation_step():
    """Performs one step of data ingestion, twin physics update, detection, and broadcasting."""
    # 1. Ingest new grid state
    grid = ingestor.ingest_current_state(base_state=digital_twin.current_state)
    digital_twin.update_state(grid)
    
    # 2. Anomaly detection
    anomalies = detector.detect_anomalies(digital_twin.current_state, ingestor.ocean_mask)
    
    # 3. Forecast prediction
    history = digital_twin.get_history()
    predictions = prediction_engine.predict_disasters(history, ingestor.ocean_mask) if len(history) >= 2 else []
    
    # Save newly detected active anomalies to DB dynamically
    async with SessionLocal() as session:
        for a in anomalies:
            from sqlalchemy import select
            stmt = select(ClimateEventModel).where(ClimateEventModel.lat == a["lat"]).where(ClimateEventModel.lon == a["lon"]).where(ClimateEventModel.type == a["type"])
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                # Save new anomaly in database
                db_evt = ClimateEventModel(
                    id=a["id"],
                    type=a["type"],
                    state=a["state"],
                    district=a["district"],
                    lat=a["lat"],
                    lon=a["lon"],
                    severity=a["severity"],
                    confidence=a["confidence"],
                    detected_at=datetime.utcnow(),
                    impact=a["impact"]
                )
                session.add(db_evt)
                
                # Audit log
                db_log = AuditLogModel(
                    module="Change Detection",
                    severity="warning" if a["severity"] in ("low", "moderate") else "critical",
                    message=f"New active anomaly detected: {a['type'].capitalize()} at {a['district']}, {a['state']}.",
                    details=a
                )
                session.add(db_log)
                
        await session.commit()

    # 4. Broadcast to WebSocket clients
    broadcast_payload = {
        "type": "telemetry_update",
        "sync_pct": float(round(98.5 + float(np_noise()), 1)),
        "health": "optimal" if digital_twin.current_step % 20 != 0 else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "tick_step": digital_twin.current_step,
        "active_anomalies": anomalies,
        "predictions": predictions,
        "layers": {
            "rainfall_avg": float(grid[:, :, 0].mean()),
            "temp_avg": float(grid[:, :, 1].mean()),
            "cloud_avg": float(grid[:, :, 3].mean()),
            "soil_moisture_avg": float(grid[:, :, 4].mean())
        }
    }
    await manager.broadcast(broadcast_payload)

async def simulation_loop():
    """Background task running the 16-step continuous climate monitoring loop."""
    logger.info("Starting background climate twin monitoring loop...")
    while True:
        try:
            await run_simulation_step()
        except Exception as e:
            logger.error(f"Error in climate simulation loop step: {e}")
        await asyncio.sleep(5.0) # 5 seconds tick rate

@app.on_event("startup")
async def on_startup():
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Warm up digital twin with initial buffer states
    logger.info("Warming up digital twin history...")
    for _ in range(5):
        grid = ingestor.ingest_current_state(base_state=digital_twin.current_state)
        digital_twin.update_state(grid)
        
    # Start background loop
    asyncio.create_task(simulation_loop())

def np_noise():
    import numpy as np
    return float(np.random.normal(0, 0.2))
