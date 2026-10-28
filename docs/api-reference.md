# API reference

Base URL `http://localhost:8000` (the frontend reaches it at `/api`). Interactive docs: `/docs` (Swagger). Most routes accept `?season=YYYY`. If omitted, the latest season in the active database is used.

| Method and path | Purpose |
|---|---|
| `GET /api/health` | `{"status":"ok","archive":"up"|"down"}` |
| `GET /api/races/seasons` | Seasons that have results: `[{season, has_telemetry}]`, newest first |
| `GET /api/races` | Season calendar with winners |
| `GET /api/races/{season}/{round}` | Race detail: results and qualifying |
| `GET /api/races/{season}/{round}/telemetry` | Drivers with telemetry for the race |
| `GET /api/races/{season}/{round}/telemetry/{driver_ref}` | Fastest-lap telemetry samples |
| `GET /api/drivers` | Drivers with ratings |
| `GET /api/drivers/{driver_ref}` | Driver detail and rating breakdown |
| `GET /api/drivers/{driver_ref}/points-history` | Cumulative points by round |
| `GET /api/teams` · `GET /api/teams/{team_ref}` | Team analytics |
| `GET /api/standings/drivers` · `/constructors` | Standings. Optional `season`, `round`. |
| `GET /api/circuits` · `/{circuit_ref}` | Circuit list and detail |
| `GET /api/circuits/{circuit_ref}/track-outline` | Outline points for the 3D view |
| `GET /api/circuits/{circuit_ref}/intelligence` | Overtaking index, Safety Car probability, pit loss |
| `POST /api/strategy/simulate` | Body: `circuit_ref, starting_position (1-20), tire_compound (SOFT|MEDIUM|HARD|INTERMEDIATE|WET), pit_lap, num_laps (5-90)` |
| `POST /api/tire-degradation/predict` | Body: `circuit_ref, compound, tyre_life (1-60)`. Returns the prediction with SHAP contributions. |
| `GET /api/live/session` | Latest OpenF1 session: `session`, `tower[]` (position, code, team, gap, interval), `weather`, `race_control[]` |

Errors use standard HTTP codes (404 unknown ref, 422 validation). The live route returns `{"session": null}` if OpenF1 has nothing.

Example:
```
curl -X POST localhost:8000/api/strategy/simulate -H 'Content-Type: application/json' \
  -d '{"circuit_ref":"monza","starting_position":8,"tire_compound":"MEDIUM","pit_lap":22,"num_laps":53}'
```
