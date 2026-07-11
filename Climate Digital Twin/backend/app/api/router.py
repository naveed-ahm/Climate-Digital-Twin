# backend/app/api/router.py

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

from backend.app.db.session import get_db
from backend.app.models.models import ClimateEventModel, SimulationResultModel, AuditLogModel
from backend.app.schemas.schemas import ClimateEvent, Strategy, SimulationResult, ResourceAllocation, TwinState, AuditLog

from backend.app.services.config import GRID_SIZE, get_grid_coords, REGIONS
from backend.app.services.synthetic_data import ingestor
from backend.app.services.physics_twin import digital_twin
from backend.app.services.detection import detector
from backend.app.services.prediction import prediction_engine
from backend.app.services.optimizer import optimizer, get_applicable_strategies
from backend.app.services.allocator import allocator
from backend.app.services.pdf_report import generate_pdf_report, output_generator

router = APIRouter()

# Helper: format grids
def grid_to_list(grid):
    if grid is None:
        return []
    return grid.tolist()

def get_layers_payload():
    if digital_twin.current_state is None:
        return {}
    return {
        "rainfall": grid_to_list(digital_twin.current_state[:, :, 0]),
        "temperature": grid_to_list(digital_twin.current_state[:, :, 1]),
        "cloud": grid_to_list(digital_twin.current_state[:, :, 3]),
        "soil_moisture": grid_to_list(digital_twin.current_state[:, :, 4]),
        "wind": grid_to_list(digital_twin.current_state[:, :, 5]),
        "humidity": grid_to_list(digital_twin.current_state[:, :, 6]),
        "terrain": grid_to_list(ingestor.elevation_map)
    }

# 1. Digital Twin
@router.get("/twin/state", response_model=TwinState)
async def get_twin_state():
    if digital_twin.current_state is None:
        raise HTTPException(status_code=503, detail="Digital twin not initialized yet.")
    return TwinState(
        sync_pct=float(round(98.5 + 1.0 * np_noise(), 1)),
        health="optimal" if digital_twin.current_step % 20 != 0 else "degraded",
        last_updated=datetime.utcnow(),
        layers=get_layers_payload()
    )

@router.get("/twin/history", response_model=List[TwinState])
async def get_twin_history():
    history = digital_twin.get_history()
    return [
        TwinState(
            sync_pct=float(round(98.5 + 1.0 * np_noise(), 1)),
            health="optimal",
            last_updated=datetime.utcnow(),
            layers={
                "rainfall": grid_to_list(h[:, :, 0]),
                "temperature": grid_to_list(h[:, :, 1]),
                "cloud": grid_to_list(h[:, :, 3]),
                "soil_moisture": grid_to_list(h[:, :, 4])
            }
        ) for h in history[-5:]
    ]

@router.post("/twin/whatif", response_model=TwinState)
async def run_whatif_preview(params: Dict[str, float]):
    """
    Takes sliders: rainfall, temperature, wind_speed, humidity, soil_moisture, cloud_cover.
    Returns simulated preview of twin state.
    """
    grid_sim = digital_twin.clone_state()
    if grid_sim is None:
        grid_sim = np_zeros_grid()
        
    # Scale variables
    if "rainfall" in params:
        grid_sim[:, :, 0] = params["rainfall"]
    if "temperature" in params:
        grid_sim[:, :, 1] = params["temperature"]
    if "cloud_cover" in params:
        grid_sim[:, :, 3] = params["cloud_cover"]
    if "soil_moisture" in params:
        grid_sim[:, :, 4] = params["soil_moisture"]
    if "wind_speed" in params:
        grid_sim[:, :, 5] = params["wind_speed"]
    if "humidity" in params:
        grid_sim[:, :, 6] = params["humidity"]
        
    grid_sim = digital_twin.advance_physics(grid_sim, steps=3)
    
    return TwinState(
        sync_pct=90.0,
        health="optimal",
        last_updated=datetime.utcnow(),
        layers={
            "rainfall": grid_to_list(grid_sim[:, :, 0]),
            "temperature": grid_to_list(grid_sim[:, :, 1]),
            "cloud": grid_to_list(grid_sim[:, :, 3]),
            "soil_moisture": grid_to_list(grid_sim[:, :, 4]),
            "wind": grid_to_list(grid_sim[:, :, 5]),
            "humidity": grid_to_list(grid_sim[:, :, 6]),
            "terrain": grid_to_list(ingestor.elevation_map)
        }
    )

# 2. Monitoring
@router.get("/monitoring/feeds")
async def get_monitoring_feeds():
    return [
        {"name": "INSAT-3DR Multispectral Imagery", "source": "ISRO/MOSDAC", "quality": 98.4, "status": "active", "payload_preview": "IR: 10.8µm, WV: 6.7µm channel active"},
        {"name": "Oceansat-3 Scatterometer Feeds", "source": "ISRO/NRSC", "quality": 95.8, "status": "active", "payload_preview": "Wind vectors at 12.5km resolution loaded"},
        {"name": "Bhuvan AWS Telemetry Networks", "source": "ISRO/Bhuvan", "quality": 99.1, "status": "active", "payload_preview": "942 of 950 telemetry nodes reporting"},
        {"name": "IMD Radar Network (DWR)", "source": "IMD", "quality": 92.5, "status": "active", "payload_preview": "Radar reflectivity grids compiled"},
        {"name": "NICES Soil Moisture & Vegetation Indices", "source": "ISRO/NICES", "quality": 94.2, "status": "active", "payload_preview": "SMAP soil moisture grids aligned"}
    ]

# 3. Change Detection
@router.get("/detection/events", response_model=List[ClimateEvent])
async def get_active_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClimateEventModel))
    events = result.scalars().all()
    # Also scan current state dynamically to add real-time detected events
    dyn_detected = detector.detect_anomalies(digital_twin.current_state, ingestor.ocean_mask) if digital_twin.current_state is not None else []
    
    # Merge db events and dynamic anomalies to prevent empty states
    all_events = []
    seen = set()
    for e in events:
        all_events.append(e)
        seen.add((e.type, e.lat, e.lon))
        
    for d in dyn_detected:
        loc_key = (d["type"], d["lat"], d["lon"])
        if loc_key not in seen:
            # Create a model instance for serializing
            evt = ClimateEventModel(
                id=d["id"],
                type=d["type"],
                state=d["state"],
                district=d["district"],
                lat=d["lat"],
                lon=d["lon"],
                severity=d["severity"],
                confidence=d["confidence"],
                detected_at=datetime.utcnow(),
                impact=d["impact"]
            )
            all_events.append(evt)
            
    return all_events

@router.get("/detection/heatmap")
async def get_heatmap(type: str = "rainfall"):
    lats, lons = get_grid_coords()
    feat_map = {"rainfall": 0, "temperature": 1, "soil_moisture": 4, "wind": 5}
    feat_idx = feat_map.get(type, 0)
    
    points = []
    grid = digital_twin.current_state if digital_twin.current_state is not None else np_zeros_grid()
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            points.append({
                "lat": float(lats[r]),
                "lon": float(lons[c]),
                "value": float(grid[r, c, feat_idx])
            })
    return points

# 4. Predictions
@router.get("/prediction/timeline", response_model=List[ClimateEvent])
async def get_prediction_timeline():
    # Run prediction engine
    history = digital_twin.get_history()
    if not history:
        return []
    predictions = prediction_engine.predict_disasters(history, ingestor.ocean_mask)
    return predictions

@router.get("/prediction/{event_id}/impact")
async def get_event_impact(event_id: str, db: AsyncSession = Depends(get_db)):
    # Find in DB or dynamic detection
    result = await db.execute(select(ClimateEventModel).where(ClimateEventModel.id == event_id))
    event = result.scalar_one_or_none()
    if event:
        return event.impact
        
    # Check predictions
    history = digital_twin.get_history()
    if history:
        preds = prediction_engine.predict_disasters(history, ingestor.ocean_mask)
        for p in preds:
            if p["id"] == event_id:
                return p["impact"]
                
    raise HTTPException(status_code=404, detail="Event not found")

# 5. Strategies
@router.get("/strategies/{event_id}", response_model=List[Strategy])
async def get_strategies(event_id: str, db: AsyncSession = Depends(get_db)):
    event = await get_event_by_id(event_id, db)
    applicable = get_applicable_strategies(event["type"])
    
    return [
        Strategy(
            id=s.id,
            event_id=event_id,
            title=s.title,
            description=s.description,
            advantages=s.advantages,
            disadvantages=s.disadvantages,
            implementation_time_hours=s.implementation_time_hours,
            estimated_cost_inr=s.estimated_cost_inr,
            required_resources=s.required_resources,
            expected_risk_reduction_pct=s.expected_risk_reduction_pct
        ) for s in applicable
    ]

# 6. Simulation & Optimizer
@router.post("/simulation/run", response_model=SimulationResult)
async def run_simulation(payload: Dict[str, str], db: AsyncSession = Depends(get_db)):
    event_id = payload.get("event_id")
    strategy_id = payload.get("strategy_id")
    if not event_id or not strategy_id:
        raise HTTPException(status_code=400, detail="Missing event_id or strategy_id")
        
    event = await get_event_by_id(event_id, db)
    strategies = get_applicable_strategies(event["type"])
    strategy = next((s for s in strategies if s.id == strategy_id), None)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not applicable or not found")
        
    res = optimizer.simulate_strategy(strategy, event, ingestor.ocean_mask)
    res["score"] = optimizer.compute_utility(res, {"risk": 0.45, "cost": 0.20, "feasibility": 0.15, "time": 0.20})
    
    # Save to database
    db_res = SimulationResultModel(
        strategy_id=res["strategy_id"],
        event_id=event_id,
        before_state=res["before_state"],
        after_state=res["after_state"],
        risk_reduction_pct=res["risk_reduction_pct"],
        population_saved=res["population_saved"],
        economic_loss_reduced_inr=res["economic_loss_reduced_inr"],
        water_saved_litres=res["water_saved_litres"],
        infrastructure_saved_pct=res["infrastructure_saved_pct"],
        success=res["success"],
        score=res["score"]
    )
    db.add(db_res)
    
    # Add Audit log
    log = AuditLogModel(
        module="AI Simulator",
        severity="info",
        message=f"Simulated strategy '{strategy.title}' for event {event_id}. Risk Reduction: {res['risk_reduction_pct']}%",
        details={"event_id": event_id, "strategy": strategy.title, "risk_reduction_pct": res["risk_reduction_pct"]}
    )
    db.add(log)
    await db.commit()
    
    return SimulationResult(
        strategy_id=res["strategy_id"],
        ran_at=res["ran_at"],
        before_state=res["before_state"],
        after_state=res["after_state"],
        risk_reduction_pct=res["risk_reduction_pct"],
        population_saved=res["population_saved"],
        economic_loss_reduced_inr=res["economic_loss_reduced_inr"],
        water_saved_litres=res["water_saved_litres"],
        infrastructure_saved_pct=res["infrastructure_saved_pct"],
        success=res["success"],
        score=res["score"]
    )

@router.post("/simulation/undo")
async def undo_simulation():
    # Return current state of twin unmodified
    return await get_twin_state()

@router.get("/optimizer/leaderboard/{event_id}", response_model=List[SimulationResult])
async def get_leaderboard(event_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SimulationResultModel)
        .where(SimulationResultModel.event_id == event_id)
        .order_by(desc(SimulationResultModel.score))
    )
    res = result.scalars().all()
    
    # Build strategy name lookup from all known strategies
    try:
        event = await get_event_by_id(event_id, db)
        strats = get_applicable_strategies(event["type"])
        strat_name_map = {s.id: s.title for s in strats}
    except Exception:
        strat_name_map = {}
    
    # Enrich results with strategy_name
    enriched = []
    for r in res:
        enriched.append(SimulationResult(
            strategy_id=r.strategy_id,
            ran_at=r.ran_at,
            before_state=r.before_state,
            after_state=r.after_state,
            risk_reduction_pct=r.risk_reduction_pct,
            population_saved=r.population_saved,
            economic_loss_reduced_inr=r.economic_loss_reduced_inr,
            water_saved_litres=r.water_saved_litres,
            infrastructure_saved_pct=r.infrastructure_saved_pct,
            success=r.success,
            score=r.score,
            strategy_name=strat_name_map.get(r.strategy_id, r.strategy_id.replace("strat-", "").title())
        ))
    return enriched


@router.post("/optimizer/run-all/{event_id}")
async def run_optimizer_all(event_id: str, db: AsyncSession = Depends(get_db)):
    event = await get_event_by_id(event_id, db)
    weights = {"risk": 0.45, "cost": 0.20, "feasibility": 0.15, "time": 0.20}
    
    opt_res = optimizer.optimize_decision(event, ingestor.ocean_mask, weights)
    
    # Save all simulations to DB
    for res in opt_res["all_options"]:
        # Verify if already simulated
        existing = await db.execute(
            select(SimulationResultModel)
            .where(SimulationResultModel.event_id == event_id)
            .where(SimulationResultModel.strategy_id == res["strategy_id"])
        )
        if not existing.scalar_one_or_none():
            db_res = SimulationResultModel(
                strategy_id=res["strategy_id"],
                event_id=event_id,
                before_state=res["before_state"],
                after_state=res["after_state"],
                risk_reduction_pct=res["risk_reduction_pct"],
                population_saved=res["population_saved"],
                economic_loss_reduced_inr=res["economic_loss_reduced_inr"],
                water_saved_litres=res["water_saved_litres"],
                infrastructure_saved_pct=res["infrastructure_saved_pct"],
                success=res["success"],
                score=res["score"]
            )
            db.add(db_res)
            
    # Add audit log
    log = AuditLogModel(
        module="AI Optimizer",
        severity="info",
        message=f"Closed-loop optimization settled. Recommended: {opt_res['recommended']['strategy_name'] if opt_res['recommended'] else 'None'}",
        details={"event_id": event_id, "best_strategy": opt_res["recommended"]["strategy_name"] if opt_res["recommended"] else None}
    )
    db.add(log)
    await db.commit()
    
    return opt_res

# 7. Resources
@router.get("/resources/allocation/{event_id}", response_model=List[ResourceAllocation])
async def get_resource_allocations(event_id: str, db: AsyncSession = Depends(get_db)):
    event = await get_event_by_id(event_id, db)
    return allocator.allocate_resources(event)

@router.post("/resources/auto-allocate", response_model=List[ResourceAllocation])
async def auto_allocate_resources(payload: Dict[str, str], db: AsyncSession = Depends(get_db)):
    event_id = payload.get("event_id")
    strategy_id = payload.get("strategy_id")
    event = await get_event_by_id(event_id, db)
    
    res = allocator.allocate_resources(event)
    
    log = AuditLogModel(
        module="Resource Dispatcher",
        severity="info",
        message=f"Dispatched resources for event {event_id}. NDRF units and vehicles routed to coordinates.",
        details={"event_id": event_id, "strategy_id": strategy_id, "resources": [r["resource_type"] for r in res]}
    )
    db.add(log)
    await db.commit()
    
    return res

# 8. Authority Module
@router.get("/authority/report/{event_id}")
async def get_authority_report(event_id: str, db: AsyncSession = Depends(get_db)):
    event = await get_event_by_id(event_id, db)
    weights = {"risk": 0.45, "cost": 0.20, "feasibility": 0.15, "time": 0.20}
    opt_res = optimizer.optimize_decision(event, ingestor.ocean_mask, weights)
    recommended = opt_res["recommended"]
    resources = allocator.allocate_resources(event)
    
    sms = output_generator.generate_sms_alert(event, recommended)
    geojson = output_generator.generate_geojson(event)
    rationale = output_generator.generate_explainability_report(event)
    checklist = output_generator.generate_action_checklist(event, recommended)
    
    return {
        "event": event,
        "recommendation": recommended,
        "resources": resources,
        "sms_broadcast": sms,
        "geojson": geojson,
        "scientific_rationale": rationale,
        "operational_checklist": checklist
    }

@router.get("/authority/report/{event_id}/pdf")
async def download_report_pdf(event_id: str, db: AsyncSession = Depends(get_db)):
    event = await get_event_by_id(event_id, db)
    weights = {"risk": 0.45, "cost": 0.20, "feasibility": 0.15, "time": 0.20}
    opt_res = optimizer.optimize_decision(event, ingestor.ocean_mask, weights)
    recommended = opt_res["recommended"]
    resources = allocator.allocate_resources(event)
    
    pdf_buffer = BytesIO()
    generate_pdf_report(event, recommended, resources, pdf_buffer)
    pdf_buffer.seek(0)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=bhoomi_drishti_report_{event_id}.pdf"}
    )

# 9. Mission Logs
@router.get("/logs", response_model=List[AuditLog])
async def get_mission_logs(
    module: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditLogModel)
    if module:
        query = query.where(AuditLogModel.module == module)
    if severity:
        query = query.where(AuditLogModel.severity == severity)
        
    query = query.order_by(desc(AuditLogModel.timestamp)).limit(limit).offset(offset)
    result = await db.execute(query)
    logs = result.scalars().all()
    return logs

# Internal Helpers
async def get_event_by_id(event_id: str, db: AsyncSession) -> Dict[str, Any]:
    result = await db.execute(select(ClimateEventModel).where(ClimateEventModel.id == event_id))
    event = result.scalar_one_or_none()
    if event:
        return {
            "id": event.id,
            "type": event.type,
            "state": event.state,
            "district": event.district,
            "location": {"lat": event.lat, "lon": event.lon},
            "severity": event.severity,
            "confidence": event.confidence,
            "detected_at": event.detected_at,
            "predicted_time": event.predicted_time,
            "probability": event.probability,
            "impact": event.impact
        }
        
    # Check predictions
    history = digital_twin.get_history()
    if history:
        preds = prediction_engine.predict_disasters(history, ingestor.ocean_mask)
        for p in preds:
            if p["id"] == event_id:
                return p
                
    raise HTTPException(status_code=404, detail="Event not found")

def np_noise():
    return float(np.random.normal(0, 0.2))

def np_zeros_grid():
    import numpy as np
    grid = np.zeros((GRID_SIZE, GRID_SIZE, 7))
    grid[:, :, 1] = 28.0 # temp
    grid[:, :, 4] = 0.5 # soil moisture
    return grid
