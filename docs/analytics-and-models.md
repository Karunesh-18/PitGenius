# Analytics and models

All analytics are season-scoped and computed from the database. Code is in `backend/app/services/`.

## Driver Rating (`driver_rating.py`): weighted formula
Each component is min-max scaled to 0–100 across that season's drivers (lower-is-better values are inverted), then combined:
| Component | Weight |
|---|---|
| Race pace | 0.35 |
| Qualifying pace | 0.30 |
| Consistency (lap-time spread) | 0.20 |
| Finishing results | 0.15 |

It isn't a trained model, because no labelled "true skill" exists. The weights are the one place to tune it.

## Constructor analytics (`constructor_analytics.py`)
Points and wins, **reliability %** (classified finishes ÷ entries), and a **pit-efficiency estimate** (extra time on pit in/out laps versus normal pace, flagged as an estimate).

## Strategy simulator (`strategy_simulator.py`): rule-based
Inputs: circuit, starting position (1–20), compound, pit lap, race length (5–90). It builds a lap-time curve from a base lap (default 90 s), a compound offset (Soft −0.6 s, Medium 0, Hard +0.6 s, Intermediate +6 s, Wet +11 s), tyre degradation and a pit loss (default 22 s, or the circuit's measured average). The time difference converts to a grid shift at 1.5 s per position, capped at 6. Outputs: predicted finish, total time, pit loss, optimal pit lap, the curve and a text explanation. The constants are rough and not telemetry-derived. A trained or Monte Carlo version is future work.

## Tyre degradation (`tire_degradation.py`): trained model with explanations
A `RandomForestRegressor` predicts lap time from compound, tyre age and circuit, trained on green-flag race laps (laps under Safety Car, VSC or red flag are excluded using FastF1 status codes 4–7). The model is cached in memory and retrained only when the data fingerprint (row count plus summed lap time) changes. **SHAP** (`TreeExplainer`) gives each factor's contribution in seconds, shown in the UI. Output includes predicted lap time, fresh-tyre baseline and the degradation versus fresh.

## Circuit intelligence (`circuit_intelligence.py`)
- **Overtaking index (0–100):** counts lap-to-lap position changes, excluding pit laps and the lap after, then min-max scales across circuits.
- **Safety Car probability:** share of races with non-green laps.
- **Average pit loss:** from in/out-lap time loss grouped by circuit.

## Telemetry (`telemetry.py`)
Serves each driver's fastest-lap samples (position, speed, throttle, brake) normalised to the circuit's outline. The 3D viewer (`frontend/src/three`) replays them on the track ribbon.

## Limitations
Single-season data can make the ratings and the tyre model unstable. Ratings are relative, not absolute. Strategy outputs are illustrative. With only 2023 laps loaded, the tyre model and circuit intelligence are trained on 2023 only.
