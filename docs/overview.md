# PitGenius: overview (no technical background needed)

## What it is
PitGenius is a web dashboard that turns Formula 1 race data into answers. It shows who is really fast, which teams are reliable, which tyre strategy is likely to work, and what is happening in a race right now.

## The problem
F1 produces huge amounts of data: lap times, tyre choices, pit stops, weather, car telemetry. It is spread across several websites and formats, so fans, students and analysts can't easily compare drivers, teams or strategies across seasons. Most free sites only list results. They don't explain them.

## What PitGenius does
| Feature | Plain-language description |
|---|---|
| **Season selector** | A strip of years at the top. Click a year and every page switches to that season. |
| **Home** | Season calendar, race winners, podium and championship tables. |
| **Drivers** | A 0–100 *Driver Rating* made from qualifying speed, race pace, consistency and finishing results, plus a points-over-the-season chart. |
| **Teams** | Points, wins, reliability (how often cars finish) and an estimate of pit-stop efficiency. |
| **Circuits** | For each track: how hard it is to overtake, how likely a Safety Car is, and how much time a pit stop costs. A 3D track view replays a driver's fastest lap (2023). |
| **Strategy** | "What if I start 8th on Mediums and pit on lap 22?" gives a predicted finishing position, a lap-time curve and the best pit lap. |
| **Tyre wear prediction** | A trained model estimates how much slower a tyre gets with age, and shows which factors drove the estimate. |
| **Live** | The current or most recent session: running order, gaps, weather and race-control messages (flags, penalties), refreshed every 5 seconds. |

## Who it's for
- **Fans** who want to see why a result happened.
- **Students and analysts** who want clean multi-season F1 data and worked examples of data science.
- **Team-style decision makers** who want to test strategy ideas quickly.

## Where the data comes from
- **Jolpica F1 API:** race results, qualifying, standings, calendars (free).
- **FastF1:** lap times and car telemetry from the official timing feed.
- **OpenF1:** live session data (free, no key).

## What is complete and what isn't (honest status)
- **2023** is complete: results, laps and telemetry.
- **2018–2022 and 2024** are loaded from the Kaggle "Formula 1 World Championship" dataset: full results, qualifying, official per-round standings, race lap times and pit-stop laps. They have no tyre or telemetry data.
- **2025** has only rounds 1–6 and **2026** has none, because the free results API (Jolpica) was rate-limiting the loader. Re-run `run --results-only` for those two once the limit lifts.
- The season selector shows only seasons that have results.
- Laps and telemetry for other seasons are not available yet, because the official timing server currently refuses downloads. OpenF1 could fill part of the gap later.
- The Driver Rating and strategy simulator are transparent, tunable formulas, not "black box" AI. The tyre model is a real trained model.

## Glossary
- **ETL:** Extract, Transform, Load. The script that downloads data, cleans it and stores it.
- **Telemetry:** per-car sensor data (speed, throttle, brake, gear) sampled many times a second.
- **Compound:** the tyre type (Soft, Medium, Hard, Intermediate, Wet).
- **Undercut / pit window:** pitting earlier than a rival to gain time on fresh tyres, and the range of laps when a stop makes sense.
- **Safety Car (SC):** a pace car that bunches up the field after an incident.
- **SHAP:** a method that explains how much each input pushed a model's prediction up or down.
- **API:** the way the dashboard asks the server for data.
