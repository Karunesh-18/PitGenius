# PitGenius

AI-powered Formula 1 race intelligence & strategy analytics platform.

See `Project.txt` for the full long-term vision and `docs/phase1-plan.md` for the current implementation plan (MVP: ETL → Postgres → FastAPI → React, with 3D track-visualization groundwork).

## Structure

- `db/` — shared SQLAlchemy models + Alembic migrations (single source of truth for the schema)
- `etl/` — data pipeline pulling from FastF1 + Jolpica F1 API into Postgres
- `backend/` — FastAPI service serving analytics over the ETL'd data
- `frontend/` — React + TypeScript dashboard

## Setup

Each of `db/`, `etl/`, `backend/` has its own Python venv; `frontend/` is a standard npm project. See `docs/phase1-plan.md` for exact setup commands and required `.env` values (`DATABASE_URL` — a hosted Postgres such as Neon is recommended since no local Postgres/Docker is assumed).
