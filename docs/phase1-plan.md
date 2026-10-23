# PitGenius — Phase 1 (MVP) Implementation Plan

## Context
`Project.txt` in the repo root is a long-term vision brain-dump covering 10 modules, 7 APIs, 8 ML models, and a full Docker/Redis/Celery stack. That scope was cut into a 3-phase roadmap so there's always a working, demoable product instead of one giant undifferentiated build. This document covers **Phase 1**: a real, demoable F1 analytics app — ETL → Postgres → FastAPI → React — including groundwork for a 3D track-visualization feature, while deliberately excluding Phase 2/3 items (Celery/Redis, animated telemetry playback, trained ML, weather, NLP/sentiment, OpenF1) in a way that doesn't block adding them later.

## Repository Structure

```
PitGenius/
├── .gitignore
├── README.md
├── Project.txt                     # long-term vision doc, kept for reference
├── docs/phase1-plan.md             # this plan
├── db/                              # shared schema — single source of truth
│   ├── pitgenius_db/{__init__.py, models.py}   # SQLAlchemy models, all Phase 1 tables
│   ├── alembic/{env.py, versions/}
│   ├── alembic.ini
│   ├── pyproject.toml               # installable as `pip install -e ../db`
│   └── .env.example
├── etl/
│   ├── pitgenius_etl/
│   │   ├── config.py                # DATABASE_URL, FASTF1_CACHE_DIR, JOLPICA_BASE_URL
│   │   ├── cache.py                 # fastf1.Cache.enable_cache(...)
│   │   ├── sources/{jolpica_client.py, fastf1_client.py}
│   │   ├── normalize/{reference.py, results.py, laps.py, track_outline.py}
│   │   ├── load/upsert.py           # Postgres ON CONFLICT upsert helpers
│   │   ├── pipeline.py              # run_season(), run_round()
│   │   └── cli.py                   # `python -m pitgenius_etl run --season 2023`
│   ├── seed/driver_aliases.csv      # manual FastF1<->Jolpica identity overrides
│   ├── tests/, requirements.txt, .env.example
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, router registration
│   │   ├── db.py                    # engine/session (reuses db/pitgenius_db models)
│   │   ├── schemas/                 # Pydantic response models
│   │   ├── routers/{drivers,teams,races,standings,circuits,strategy}.py
│   │   ├── services/{driver_rating,constructor_analytics,strategy_simulator}.py
│   │   └── tests/
│   └── requirements.txt, .env.example
└── frontend/
    ├── src/
    │   ├── pages/{Home,DriverAnalytics,TeamAnalytics,StrategySimulator}.tsx
    │   ├── components/
    │   ├── three/Track3DView.tsx
    │   ├── api/client.ts            # fetch wrapper + react-query hooks
    │   ├── styles/tokens.css        # design tokens (colors, type scale)
    │   └── theme/                   # team-color map, tire-compound palette (reserved for Phase 2)
    ├── index.html, vite.config.ts, package.json
```

**Rationale:** `db/` is a standalone installable package (SQLAlchemy models + Alembic migrations) that both `etl` and `backend` depend on via `pip install -e ../db` — one schema definition, no drift, and Phase 2 tables get added in exactly one place. `etl`/`backend` have separate venvs since they have different runtime profiles (FastF1/pandas batch job vs. request-serving API); this also mirrors where a future Celery worker would live — `etl.pipeline`'s functions become task bodies later with no rework. `frontend` is a standard Vite app talking to the backend only over HTTP.

## Postgres Schema (Phase 1)

Surrogate integer PKs everywhere; stable natural-key `_ref` text columns (Jolpica/Ergast-style IDs, e.g. `driver_ref='max_verstappen'`) drive idempotent upserts and cross-source joins. `season`+`round` is the shared join key between FastF1 and Jolpica. Managed via Alembic from commit 1, so Phase 2 tables (`tyre_stints`, `telemetry`, `weather`, `pit_stops`, `strategy_simulations`, `predictions`) are pure additive migrations later.

Tables: `teams`, `drivers`, `circuits` (includes `track_outline JSONB` for the static 3D pipeline), `races` (unique on `season, round`), `sessions` (unique on `race_id, session_type`), `lap_times` (includes `compound`, `tyre_life`, and per-lap `is_pit_lap`/`pit_in_time_ms`/`pit_out_time_ms` so pit-efficiency can be approximated without the full Phase-2 `pit_stops` table), `qualifying_results`, `race_results`, `driver_standings`, `constructor_standings`.

**Deliberate choice to flag:** Constructor Analytics' "pit stop efficiency" is approximated from `lap_times`' pit columns rather than waiting for the Phase-2 `pit_stops` table — those columns stay useful as raw timing source once that table exists.

**Standings are pulled directly from Jolpica's own standings endpoints**, not re-derived from `race_results` in SQL — F1's points rules have changed across eras (fastest-lap bonus 2019–2021, sprint points), so re-deriving would be error-prone; pulling the authoritative per-round snapshot is simpler and correct.

## ETL Plan

| Data | Source |
|---|---|
| Season schedule, circuits | Jolpica `/{season}.json` |
| Drivers, teams | Jolpica `/{season}/drivers.json`, `/constructors.json` |
| Race results | Jolpica `/{season}/results.json` (paginated) |
| Qualifying results | Jolpica `/{season}/qualifying.json` |
| Standings | Jolpica `/{season}/driverStandings.json`, `/constructorStandings.json` |
| Sessions + lap times | FastF1 `get_session(year, round, 'R'|'Q').load()` → `.laps` |
| Track outline | FastF1 fastest lap's `.get_telemetry()` (X/Y/Z) → stored once per circuit |

Identity resolution joins primarily on `season`+`round`, then matches drivers within a session by number + 3-letter code + surname, with `etl/seed/driver_aliases.csv` as a manual override for edge cases.

Pipeline (`pipeline.py`): `run_season(season, rounds=None)` — upsert reference data → upsert races → per round: upsert quali/race results + standings (Jolpica) → load FastF1 Q/R sessions → upsert sessions/lap_times → backfill missing `track_outline`s from one clean dry session per circuit. All writes use `INSERT ... ON CONFLICT DO UPDATE` on the unique constraints above, so **the script is idempotent** and safe to re-run.

FastF1 caching: `fastf1.Cache.enable_cache(FASTF1_CACHE_DIR)` at ETL startup, gitignored local cache dir — first season pull is slow, reruns are near-instant. Start with **one completed season** (2023 or 2024) as the MVP dataset before considering backfill.

CLI: `python -m pitgenius_etl run --season 2023 [--rounds 1,2,3]`.

## Backend (FastAPI)

Routes: `GET /api/health`; `GET /api/drivers?season=` and `/api/drivers/{driver_ref}` (list/detail + computed rating); `GET /api/teams?season=` and `/api/teams/{team_ref}` (+ driver-vs-teammate comparison); `GET /api/races?season=` and `/api/races/{season}/{round}`; `GET /api/standings/drivers` and `/constructors`; `GET /api/circuits/{circuit_ref}` and `/track-outline`; `POST /api/strategy/simulate` (body: circuit, starting position, tire compound, pit lap, laps → predicted finish, time estimate, pit loss, lap-time curve, plain-text explanation).

Routers stay thin; logic lives in `backend/app/services/`. **Driver Rating is an explicit weighted formula, not a trained model** (no labeled target exists yet) — weights are named constants in `driver_rating.py`, easy to tune later or replace with a trained model once enough seasons are loaded. Services pull rows via SQLAlchemy into pandas for aggregation/normalization; at Phase 1 data volume (~1 season) this is sub-second, so no caching layer yet (Redis is the natural Phase 2+ slot). CORS configured for the Vite dev origin.

## Frontend (React + TypeScript)

Stack: Vite + React + TS, `react-router-dom`, `@tanstack/react-query`, `recharts` for 2D charts, Tailwind CSS driven by CSS-variable design tokens, `three` + `@react-three/fiber` + `@react-three/drei` for the 3D track view.

**Exactly 4 routes**, per the agreed Phase 1 scope:
1. `/` **Home** — live standings tabs, upcoming race card, season progress, top-rated drivers widget.
2. `/drivers`, `/drivers/:driverRef` **Driver Analytics** — team-color-accented list, profile header, pace-trend chart, rating-breakdown radar, results table.
3. `/teams`, `/teams/:teamRef` **Team Analytics** — team list/profile, driver-vs-teammate chart, reliability stat, pit-efficiency estimate (flagged as approximate — see schema note), season points progression.
4. `/strategy` **Strategy Simulator** — circuit/position/compound/pit-lap controls, result summary, lap-time curve chart, plain-text explanation panel, and the embedded `<Track3DView circuitRef=... />` (kept inside this page rather than adding a 5th route).

**Design tokens** (`src/styles/tokens.css`): dark F1-broadcast base palette (`--color-bg-base`, `--color-bg-panel`, `--color-text-*`), per-team accent color driven from `teams.color_primary/secondary`, and **colorblind-safe tire-compound tokens defined now but unused until Phase 2** so no redesign is needed later. Typography: Titillium Web for body/UI, a condensed weight for stat numerics.

**3D track outline — react-three-fiber, not deck.gl:** deck.gl targets GPU-instanced overlays on a geospatial basemap; react-three-fiber is a declarative Three.js renderer suited to a custom extruded track ribbon *and* to Phase 2's animation (moving a marker along a `CatmullRomCurve3` via telemetry timestamps) — so Phase 2 adds animation onto this same scene graph rather than bolting Three.js on separately later. Build: fetch `/api/circuits/{ref}/track-outline` via react-query → `CatmullRomCurve3` from the points → `TubeGeometry` ribbon → dark asphalt material with accent emissive glow → `<Canvas>` with `OrbitControls` + lighting. Outline points are normalized/centered/scaled **server-side in the ETL step**, not client-side, so every circuit renders at consistent scale.

## Build Order / Milestones

| # | Milestone | Verify |
|---|---|---|
| M0 | Repo scaffold, venvs, Vite app, Neon Postgres provisioned | health route 200; `npm run dev` shows default page |
| M1 | Schema live via Alembic | all 10 tables exist; `alembic downgrade -1`/`upgrade head` round-trips |
| M2 | ETL: Jolpica reference + results/standings, one season | race/result counts plausible; re-run is idempotent (identical counts) |
| M3 | ETL: FastF1 sessions + lap_times, same season | lap counts spot-check against a known real race; second run is cache-fast |
| M4 | Backend read API | `GET /api/standings/drivers?season=2023` matches real-world final standings |
| M5 | Driver Rating + Constructor Analytics wired in | ratings in [0,100], no NaNs; pytest bounds/sanity tests |
| M6 | Frontend scaffold + tokens + Home page live | dark-themed Home renders real data, no CORS errors |
| M7 | Driver + Team Analytics pages | detail pages match a manual curl of the same endpoint |
| M8 | Circuit track-outline pipeline + 3D viewer | outline stored for ≥1 circuit; recognizable closed-loop 3D shape with working orbit controls |
| M9 | Strategy Simulator end-to-end | changing pit lap/compound moves the result in the expected direction; deterministic pytest unit tests on the formula |
| M10 | Polish: loading/error/empty states, token consistency | click through all 4 routes, no console errors |

## Postgres

No local `psql`/Docker available, so a hosted free-tier instance is used — **Neon** (neon.tech) recommended for zero local-install friction. Connection string goes in `db/.env`, `etl/.env`, `backend/.env` as `DATABASE_URL=postgresql+psycopg://...?sslmode=require`.

## Critical Files
- `db/pitgenius_db/models.py` — single source of truth for the schema
- `etl/pitgenius_etl/pipeline.py` — fetch → normalize → upsert orchestration
- `backend/app/services/driver_rating.py` — the composite rating formula, central to the "AI intelligence" differentiator
- `backend/app/main.py` — FastAPI wiring, CORS, routers
- `frontend/src/three/Track3DView.tsx` — 3D rendering pipeline Phase 2 animation builds on
