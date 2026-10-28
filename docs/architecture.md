# Architecture

## Components
```
 Jolpica API ─┐                                    ┌─ React 19 + Vite + Tailwind 4
 FastF1 ──────┼─► ETL (Python) ─► Postgres ◄─ FastAPI ◄─ proxy /api ─┤  react-query, react-router,
              │                       ▲  ▲        │                   │  recharts, three.js (R3F)
              │          GPU-server archive  Neon  └─► OpenF1 (live)  └─ pages: Home, Drivers, Teams,
              └──────────────────────(primary) (fallback)                  Strategy, Circuits, Live
```
| Folder | Role |
|---|---|
| `db/` | SQLAlchemy 2 models (`pitgenius_db/models.py`) and Alembic migrations. The single source of truth for the schema, installed as a package by both ETL and backend. |
| `etl/` | Batch pipeline: fetch → normalize → upsert. CLI: `python -m pitgenius_etl run|telemetry|sync`. |
| `backend/` | FastAPI service. Routers are thin; analytics live in `app/services/`. |
| `frontend/` | React SPA. The Vite dev server proxies `/api` to `localhost:8000`. |

## Request flow
1. The browser calls `/api/...?season=N`. The selected season comes from `SeasonProvider` (`frontend/src/api/season.tsx`) and is part of every react-query key in `api/hooks.ts`.
2. FastAPI resolves a database session through `get_db` (`backend/app/db.py`).
3. A router calls a service (pandas and scikit-learn for analytics) or a plain SQL query, and returns a Pydantic model.

## Two databases, one picker
- **Archive** (`ARCHIVE_DATABASE_URL`): Postgres 16 on the GPU server, holding every loaded season. It is reached through an SSH tunnel to `localhost:55432`.
- **Neon** (`DATABASE_URL`): hosted Postgres holding 2023. It is the fallback.
- `get_db` uses the archive when a cached probe (re-checked every 30 s) succeeds, and Neon otherwise. A dead tunnel therefore costs one failed probe per 30 s, not one per request. `/api/health` reports `archive: up|down`.

## Live data
`services/openf1.py` wraps OpenF1 with a 5-second TTL cache and serves stale data if the upstream fails. `routers/live.py` assembles the latest session (`session_key=latest`): driver list, last position and interval per driver, latest weather, last 10 race-control messages. The frontend polls every 5 s with `refetchInterval`. Polling replaced SSE or WebSockets because OpenF1 updates only every few seconds.

## Design decisions
- **Transparent formulas first.** Driver Rating and the Strategy Simulator are weighted formulas with constants in one place. There is no labelled ground truth to train against. The tyre model is trained on real lap times.
- **Per-request compute, cached models.** Ratings are computed from the DB on each request. The tyre model is cached in-process and retrained only when the training data's fingerprint changes.
- **Upserts everywhere.** All loads are idempotent (`ON CONFLICT`), so reruns and `sync` are safe.
- **Season-scoped everything.** Every query filters by `Race.season`, which is what made multi-year support a small change.

## Not built yet (deferred by design)
Celery/Redis job queue, Monte Carlo race-outcome simulation, weather overlays, news/sentiment, and a trained driver-rating model. See `../Project.txt` and `phase1-plan.md`.
