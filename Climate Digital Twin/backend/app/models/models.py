# backend/app/models/models.py

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, JSON
from backend.app.db.session import Base

class ClimateEventModel(Base):
    __tablename__ = "climate_events"

    id = Column(String, primary_key=True, index=True)
    type = Column(String, nullable=False)
    state = Column(String, nullable=False)
    district = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    severity = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    predicted_time = Column(DateTime, nullable=True)
    probability = Column(Float, nullable=True)
    impact = Column(JSON, nullable=False) # JSON storing population, infra, agric, etc.

class SimulationResultModel(Base):
    __tablename__ = "simulation_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    strategy_id = Column(String, nullable=False, index=True)
    event_id = Column(String, nullable=False, index=True)
    ran_at = Column(DateTime, default=datetime.utcnow)
    before_state = Column(JSON, nullable=False)
    after_state = Column(JSON, nullable=False)
    risk_reduction_pct = Column(Float, nullable=False)
    population_saved = Column(Integer, nullable=False)
    economic_loss_reduced_inr = Column(Float, nullable=False)
    water_saved_litres = Column(Float, nullable=False)
    infrastructure_saved_pct = Column(Float, nullable=False)
    success = Column(Boolean, nullable=False)
    score = Column(Float, nullable=False)

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    module = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False) # info, warning, error, critical
    message = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
