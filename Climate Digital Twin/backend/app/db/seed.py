# backend/app/db/seed.py

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from backend.app.db.session import engine, Base, SessionLocal
from backend.app.models.models import ClimateEventModel, AuditLogModel

async def seed_db():
    print("Connecting to database and dropping existing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    print("Seeding database...")
    async with SessionLocal() as session:
        # Create historical and current alerts
        now = datetime.utcnow()
        
        events = [
            # 1. Historical Anomaly: Heavy Rain in Mumbai (2 days ago)
            ClimateEventModel(
                id=str(uuid.uuid4()),
                type="heavy_rain",
                state="Maharashtra",
                district="Mumbai",
                lat=19.0,
                lon=72.8,
                severity="high",
                confidence=0.88,
                detected_at=now - timedelta(days=2),
                predicted_time=None,
                probability=None,
                impact={
                    "population": 1200000,
                    "infrastructure": 65, # % risk
                    "agriculture": 10,
                    "roads": 80,
                    "hospitals": 30,
                    "power": 45,
                    "water": 50
                }
            ),
            # 2. Current Active Anomaly: Cyclone near Odisha Coast
            ClimateEventModel(
                id="event-odisha-cyclone",
                type="cyclone",
                state="Odisha",
                district="Puri",
                lat=20.2,
                lon=86.0,
                severity="critical",
                confidence=0.94,
                detected_at=now - timedelta(hours=3),
                predicted_time=now + timedelta(hours=12),
                probability=0.98,
                impact={
                    "population": 450000,
                    "infrastructure": 85,
                    "agriculture": 75,
                    "roads": 90,
                    "hospitals": 60,
                    "power": 95,
                    "water": 80
                }
            ),
            # 3. Predicted Anomaly: Heatwave in Rajasthan (forecasted in 24 hours)
            ClimateEventModel(
                id="event-rajasthan-heatwave",
                type="heatwave",
                state="Rajasthan",
                district="Churu",
                lat=26.0,
                lon=72.0,
                severity="severe",
                confidence=0.82,
                detected_at=now,
                predicted_time=now + timedelta(days=1),
                probability=0.85,
                impact={
                    "population": 150000,
                    "infrastructure": 20,
                    "agriculture": 80,
                    "roads": 15,
                    "hospitals": 40,
                    "power": 70,
                    "water": 90
                }
            ),
            # 4. Active Anomaly: Forest Fire in Western Ghats
            ClimateEventModel(
                id="event-ghats-fire",
                type="forest_fire",
                state="Karnataka",
                district="Kodagu",
                lat=10.0,
                lon=76.5,
                severity="high",
                confidence=0.87,
                detected_at=now - timedelta(hours=6),
                predicted_time=None,
                probability=None,
                impact={
                    "population": 25000,
                    "infrastructure": 40,
                    "agriculture": 85,
                    "roads": 50,
                    "hospitals": 10,
                    "power": 30,
                    "water": 15
                }
            )
        ]
        
        session.add_all(events)
        
        # Audit Logs
        logs = [
            AuditLogModel(
                timestamp=now - timedelta(hours=24),
                module="Digital Twin",
                severity="info",
                message="Climate twin physical engine fully synchronized with INSAT-3DR and Oceansat-3 channels.",
                details={"sync_status": "optimal", "channels": ["IR", "VIS", "WV"]}
            ),
            AuditLogModel(
                timestamp=now - timedelta(hours=18),
                module="Change Detection",
                severity="warning",
                message="Thermal anomaly detected in Rajasthan sector. Temp grid reading 43.5°C.",
                details={"lat": 26.0, "lon": 72.0, "temp_c": 43.5}
            ),
            AuditLogModel(
                timestamp=now - timedelta(hours=3),
                module="Change Detection",
                severity="critical",
                message="Cyclone boundary formation confirmed off Odisha Coast. Deep depression detected.",
                details={"event_id": "event-odisha-cyclone", "wind_speed": 125.0, "sst": 28.4}
            ),
            AuditLogModel(
                timestamp=now - timedelta(minutes=45),
                module="AI Optimizer",
                severity="info",
                message="Ran 6 mitigation strategy wargames for Odisha Cyclone. ev_12_odisha strategy outputted optimal composite score of 87.5.",
                details={"event_id": "event-odisha-cyclone", "recommended_strategy": "Evacuation + Resource Pre-positioning"}
            )
        ]
        
        session.add_all(logs)
        await session.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_db())
