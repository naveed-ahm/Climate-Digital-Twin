# Bhoomi-Drishti Architecture

## Overview
Bhoomi-Drishti is an AI-powered digital twin for India's climate resilience. The platform combines synthetic telemetry generation, a physics-informed digital twin, anomaly detection, forecasting, strategy generation, simulation, optimization, and authority dispatch into one mission-control experience.

## Stack
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS + Framer Motion
- Backend: FastAPI + Pydantic v2 + SQLAlchemy async + WebSockets
- Simulation stack: numpy-based synthetic ingestors, physics-inspired state updates, scikit-learn scoring, and a lightweight forecasting model built from synthetic time-series data

## Runtime Flow
1. Synthetic meteorological feeds are ingested into the digital twin.
2. The twin updates its internal state and exposes live layers.
3. Detection services identify anomalies and generate events.
4. Forecasting predicts future risks with confidence scores.
5. Strategy generation compiles multiple intervention options.
6. Simulation and optimization rank each option.
7. Resources are allocated and a dispatch report is generated.

## Demo Note
The data used for the demo is intentionally synthetic and seeded to look realistic for India-wide climate scenarios. The platform is designed to demonstrate the full mission loop and report generation workflow rather than claim any real-time satellite ingestion from production systems.
