# Bhoomi-Drishti API Reference

## Core Endpoints
- GET /api/twin/state — returns the current digital twin state and live layers
- GET /api/twin/history — returns recent historical twin snapshots
- POST /api/twin/whatif — previews how the twin responds to parameter changes
- GET /api/monitoring/feeds — returns synthetic monitoring feed metadata
- GET /api/detection/events — returns detected climate events
- GET /api/prediction/timeline — returns forecasted events
- GET /api/strategies/{event_id} — returns a set of candidate strategies
- POST /api/simulation/run — runs one strategy against the sandbox twin
- POST /api/simulation/undo — reverts the twin to the pre-simulation snapshot
- GET /api/optimizer/leaderboard/{event_id} — returns ranked simulation outcomes
- POST /api/optimizer/run-all/{event_id} — runs the full optimizer loop
- GET /api/resources/allocation/{event_id} — returns allocated resources
- POST /api/resources/auto-allocate — auto-assigns a resource plan
- GET /api/authority/report/{event_id} — returns an authority dispatch payload
- GET /api/authority/report/{event_id}/pdf — streams a PDF report
- GET /api/logs — returns an audit log stream
- WS /ws/live — streams live updates for telemetry and strategy progression
