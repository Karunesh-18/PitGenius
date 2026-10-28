# PitGenius

AI-powered Formula 1 race intelligence & strategy analytics platform.

Documentation index: `docs/README.md`. See `Project.txt` for the full long-term vision and `docs/phase1-plan.md` for the current implementation plan (MVP: ETL → Postgres → FastAPI → React, with 3D track-visualization groundwork).

## Structure

- `db/` — shared SQLAlchemy models + Alembic migrations (single source of truth for the schema)
- `etl/` — data pipeline pulling from FastF1 + Jolpica F1 API into Postgres
- `backend/` — FastAPI service serving analytics over the ETL'd data
- `frontend/` — React + TypeScript dashboard

## Setup

Each of `db/`, `etl/`, `backend/` has its own Python venv; `frontend/` is a standard npm project. See `docs/phase1-plan.md` for exact setup commands and required `.env` values (`DATABASE_URL` — a hosted Postgres such as Neon is recommended since no local Postgres/Docker is assumed).

## Multi-year archive and live data
- `ARCHIVE_DATABASE_URL` (backend `.env`) points at the full multi-season Postgres on the GPU server, reached through
  `ssh -N -L 55432:127.0.0.1:55432 <user>@<server>`. The backend uses it first and falls back to Neon (`DATABASE_URL`).
- Load seasons with `python -m pitgenius_etl run --season N --results-only` (Jolpica only, ~12 requests; per-round
  standings are derived from results). Laps/telemetry need FastF1 (`run` / `telemetry`).
- `python -m pitgenius_etl sync` loads newly raced rounds. The Live page proxies OpenF1 via `/api/live/session`.
