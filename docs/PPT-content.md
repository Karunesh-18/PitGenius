# PitGenius: slide content for the project review

**Source for the layout:** `PPT (1).pdf` is a 10-slide, 16:9 (960×540) deck for a different project, *ProcureSense*, in the course "Data Science, U23AD491". This file reuses its slide order and style for PitGenius, with two extra slides (Results and Demo, Limitations and Future Work) that a final review usually needs. Replace every `<…>` placeholder with your own details. The PDF's student, faculty and registration details belong to the other project, so they are not copied here.

**Style notes (copied from the reference deck):** each slide has a short title; 3–5 bullets or cards; a footer reading `Data Science | U23AD491 | PitGenius` plus the slide number; an italic or bold one-line takeaway under cards. Use a dark F1-style theme (near-black background, red or teal accent) to match the app, with big numbers and few words.

---

## Slide 1: Title
- Department of Computer Science and Engineering
- Course name: Data Science · Course code: U23AD491 *(keep if this is the same course)*
- **Title of the project:** PitGenius: AI-Powered Formula 1 Race Intelligence and Strategy Analytics Platform
- Visual: screenshot of the Home page or the 3D track view, or a clean car or track silhouette.

## Slide 2: Review details (two-column table, as in the reference)
| Field | Value |
|---|---|
| Class / Section / Semester | `<III CSE / B / V>` |
| Batch | `<2024-2028>` |
| Project Review | `<Final Review>` |
| Date | `<dd-mm-yyyy>` |
| Faculty I/C | `<name, qualification, designation>` |
| Title | PitGenius: AI-Powered Formula 1 Race Intelligence and Strategy Analytics Platform |
| Student name and Reg No | `<name & reg no>` |

## Slide 3: Abstract (4 bullets)
- F1 produces vast data (lap times, tyres, pit stops, weather, telemetry), yet fans and analysts mostly see raw results with little explanation.
- PitGenius is a data-driven platform that collects historical and live F1 data, rates drivers and teams, predicts tyre wear and simulates race strategies.
- Models are explainable: a transparent weighted Driver Rating, and a Random Forest tyre model whose predictions are explained with SHAP.
- An interactive dashboard with a season selector, a 3D track replay and a live timing page lets users explore any loaded season.

## Slide 4: Survey, Problem Addressed (5 cards + takeaway)
| Card | Text |
|---|---|
| Scattered data | Results, lap data and live timing sit on different sites and formats. |
| Results without reasons | Sites show who won, not why, so pace, consistency and strategy stay hidden. |
| Hard to compare | Comparing drivers or teams across seasons needs manual work. |
| Strategy is guesswork | Fans can't easily test what-if choices such as when to pit. |
| Live data is raw | Timing feeds are hard to read without tooling. |

Takeaway line: *Existing free tools list results; they rarely explain or predict.*

## Slide 5: Proposed Solution (4 cards, as in the reference: Predict, Evaluate, Recommend, Monitor)
- **Collect:** an ETL pipeline loads results, standings, laps and telemetry from Jolpica and FastF1 into Postgres.
- **Evaluate:** a Driver Rating (0–100), team reliability and pit-efficiency, and circuit intelligence (overtaking, Safety Car, pit loss).
- **Predict:** tyre degradation (Random Forest and SHAP) and a rule-based race-strategy simulator.
- **Monitor:** a dashboard with a season timeline and a live OpenF1 page (positions, gaps, weather, race control).

Takeaway line: *PitGenius turns raw F1 data into explainable, interactive decision support.*

## Slide 6: Overall System Architecture (draw as a flow with three layers)
- **Data sources:** Jolpica F1 API · FastF1 · OpenF1 (live)
- **ETL (Python):** fetch → clean and normalise → idempotent upsert · CLI commands `run`, `telemetry`, `sync`
- **Storage:** PostgreSQL archive on the GPU server (all seasons, via SSH tunnel) + Neon cloud Postgres (fallback)
- **Analytics engine (FastAPI + pandas + scikit-learn + SHAP):** Driver Rating · Constructor analytics · Circuit intelligence · Tyre-degradation model · Strategy simulator
- **Web app (React 19, Vite, Tailwind, react-query, Recharts, three.js):** Season scrubber · Home · Drivers · Teams · Circuits · Strategy · Live
- **Users:** fans, students, analysts

Diagram hint: left-to-right boxes with arrows. Show OpenF1 bypassing the database and going straight to the backend, and show Neon as a dotted fallback arrow.

## Slide 7: Core Modules (numbered tiles, 1–9)
1. Data collection (ETL)
2. Multi-season archive and season selector
3. Driver Intelligence (Driver Rating)
4. Constructor Analytics
5. Circuit Intelligence
6. Tyre Degradation Prediction (with SHAP)
7. Race Strategy Simulator
8. Telemetry viewer (3D track replay)
9. Live timing (OpenF1)

## Slide 8: Technology Stack (table)
| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4 |
| 3D / Charts | three.js (react-three-fiber), Recharts |
| Backend | Python, FastAPI, SQLAlchemy 2, Pydantic |
| Database | PostgreSQL 16 (GPU server archive), Neon Postgres, Alembic migrations |
| Data sources | Jolpica F1 API, FastF1, OpenF1 |
| Data processing | Pandas, NumPy |
| Machine learning | scikit-learn (Random Forest), SHAP |

## Slide 9: Methodology and Models (the data science slide; this one replaces nothing in the reference)
- **Data cleaning and feature engineering:** green-flag laps only (Safety Car, VSC and red-flag laps removed), pit in/out laps flagged, min-max scaling to 0–100.
- **Driver Rating = 0.35 race pace + 0.30 qualifying pace + 0.20 consistency + 0.15 finishing results.**
- **Tyre model:** RandomForestRegressor predicting lap time from compound, tyre age and circuit, explained with SHAP. Cached and retrained when data changes.
- **Circuit intelligence:** overtaking index from lap-to-lap position changes, Safety Car probability, average pit loss.
- **Strategy simulator:** lap-time curve from compound offset, degradation and pit loss → predicted finishing position and best pit lap.

## Slide 10: Results and Demo
- Screenshots (take these from the running app): season scrubber · Drivers page with rating · Strategy result and lap-time curve · tyre-degradation SHAP bars · 3D track replay · Live timing tower.
- Numbers to show (verify the day before): 2018–2024 loaded (about 150 races and about 3,000 race results, about 165,000 lap-time rows). 2023 alone has 31,839 lap rows and 23,600 telemetry points; telemetry and tyre data exist for 2023 only.
- Live demo script (about 3 minutes): choose 2023 → open Drivers → run a Strategy → open Circuits and replay a lap → open Live.

## Slide 11: Expected Outcome (5 bullets)
- Clear, data-based driver and team scores instead of opinions
- Explainable predictions: users see why a tyre estimate or strategy came out as it did
- Multi-season exploration in one place, with an archive that grows by one command
- Live race-weekend view without any paid data service
- A reusable, documented data pipeline for future F1 analytics

## Slide 12: Limitations and Future Work
**Limitations (be upfront):**
- Full laps and telemetry are loaded for 2023 only (F1's timing feed refused new downloads); other seasons have results and standings.
- Driver Rating and strategy simulator are formulas, not trained models. The tyre model is trained on one season.
- Pit efficiency is an estimate from lap data. There are no automated tests yet.

**Future work:** Monte Carlo race-outcome simulation (podium, top-10, DNF and fastest-lap probabilities) · fill laps and telemetry from OpenF1 · weather overlay and wet-weather ratings · trained driver-rating model · Celery/Redis scheduled sync · news and sentiment features.

## Slide 13: Thank You
- "Thank You" · `<your name>` · `<email>` · repository `<link>` · "Questions?"

---

## Speaker notes (about 30 seconds per slide)
1. Introduce the problem in one sentence: *F1 has more data than any fan can read.*
2. Slide 6: walk the diagram left to right and say that live data takes a shortcut.
3. Slide 9: the key point is *transparent where we lack labels, trained where we have data.*
4. Slide 10: do the live demo and have screenshots as a backup in case the network fails.
5. Slide 12: name the limits yourself before you are asked.

## Likely viva questions
- *Why not train the driver rating?* There is no ground truth for driver skill. A weighted composite is transparent and tunable.
- *Why Random Forest for tyres?* It handles non-linear wear and categorical inputs (compound, circuit) with little tuning, and SHAP's TreeExplainer explains it quickly.
- *How is live data different from historical?* Live data is proxied from OpenF1 with a 5-second cache and never stored. Historical data is stored by the ETL.
- *Why two databases?* The GPU-server archive holds every season. Neon is a small hosted fallback, so the app still works with 2023 if the archive is offline.
- *How do you add a season?* One command: `python -m pitgenius_etl run --season N --results-only`.
