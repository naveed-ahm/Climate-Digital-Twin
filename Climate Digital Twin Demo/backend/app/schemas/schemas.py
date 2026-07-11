# backend/app/schemas/schemas.py

from datetime import datetime
from typing import Literal, Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

EventType = Literal[
    "rain", "heavy_rain", "flood", "urban_flood", "cyclone",
    "heatwave", "cold_wave", "drought", "forest_fire", "urban_heat_island"
]

SeverityType = Literal["low", "moderate", "high", "severe", "critical"]
HealthType = Literal["optimal", "degraded", "critical"]

class ClimateEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: EventType
    location: Dict[str, Any]  # {state: str, district: str, lat: float, lon: float}
    severity: SeverityType
    confidence: float # 0-1
    detected_at: datetime
    predicted_time: Optional[datetime] = None
    probability: Optional[float] = None
    impact: Dict[str, Any] # population, infrastructure, agriculture, roads, hospitals, power, water
    time_window: Optional[str] = None  # e.g. "T+6h (6 hours)"

    @model_validator(mode="before")
    @classmethod
    def assemble_location(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "location" not in data and all(k in data for k in ("state", "district", "lat", "lon")):
                data = dict(data)
                data["location"] = {
                    "state": data.pop("state"),
                    "district": data.pop("district"),
                    "lat": data.pop("lat"),
                    "lon": data.pop("lon")
                }
        elif hasattr(data, "state") and hasattr(data, "district") and hasattr(data, "lat") and hasattr(data, "lon"):
            # SQLAlchemy ORM object
            location = {
                "state": data.state,
                "district": data.district,
                "lat": data.lat,
                "lon": data.lon
            }
            # We construct a dict representing the data
            return {
                "id": data.id,
                "type": data.type,
                "location": location,
                "severity": data.severity,
                "confidence": data.confidence,
                "detected_at": data.detected_at,
                "predicted_time": data.predicted_time,
                "probability": data.probability,
                "impact": data.impact
            }
        return data

class Strategy(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    title: str
    description: str
    advantages: List[str]
    disadvantages: List[str]
    implementation_time_hours: float
    estimated_cost_inr: float
    required_resources: Dict[str, int] # {resource_type: quantity}
    expected_risk_reduction_pct: float

class SimulationResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    strategy_id: str
    ran_at: datetime
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    risk_reduction_pct: float
    population_saved: int
    economic_loss_reduced_inr: float
    water_saved_litres: float
    infrastructure_saved_pct: float
    success: bool
    score: float # composite AI-optimizer score
    strategy_name: Optional[str] = None

class ResourceAllocation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resource_type: str
    available: int
    allocated: int
    location: Dict[str, float] # {lat: float, lon: float}
    eta_minutes: float

class TwinState(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sync_pct: float
    health: HealthType
    last_updated: datetime
    layers: Dict[str, Any] # {rainfall, temperature, cloud, terrain, vegetation, water: layer payload}

class AuditLog(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    module: str
    severity: str
    message: str
    details: Optional[Dict[str, Any]] = None
