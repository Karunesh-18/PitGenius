# Setup and operations

## Prerequisites
Python 3.11+, Node 20+, a Postgres database (Neon is fine), and for the multi-year archive SSH access to the GPU server. On Windows with Android Studio installed, ignore the Java note: nothing here needs Java.

## First-time setup
```
# db: migrations
cd db && python -m venv .venv && .venv/Scripts/activate && pip install -e . alembic psycopg[binary] python-dotenv
DATABASE_URL=... alembic upgrade head

# etl
cd etl && python -m venv .venv && pip install -r requirements.txt   # remove the machine-specific "-e ...\db" line, then: pip install -e ../db

# backend
cd backend && python -m venv .venv && pip install -r requirements.txt
cp .env.example .env     # DATABASE_URL, optional ARCHIVE_DATABASE_URL, CORS_ORIGINS

# frontend
cd frontend && npm install
```

## Run
```
cd backend  && .venv/Scripts/python -m uvicorn app.main:app --port 8000 --reload
cd frontend && npm run dev          # http://localhost:5173
ssh -N -L 55432:127.0.0.1:55432 <user>@<server>     # only for the archive
```

## Configuration
| Variable | Where | Meaning |
|---|---|---|
| `DATABASE_URL` | backend, etl | Neon (fallback, 2023) |
| `ARCHIVE_DATABASE_URL` | backend | GPU-server archive (optional) |
| `CORS_ORIGINS` | backend | Allowed frontend origins (default `http://localhost:5173`) |
| `FASTF1_CACHE_DIR`, `JOLPICA_BASE_URL` | etl | FastF1 cache and Jolpica base URL |

## Operations
- **Add a season:** `python -m pitgenius_etl run --season N --results-only`. It appears in the season selector once results exist.
- **Keep current:** schedule `python -m pitgenius_etl sync` (for example daily).
- **Restart the archive after a server reboot:** run `pg_ctl -D ~/pitgenius/pgdata -l pg.log start` using the binary under the venv's `pgserver/pginstall/bin`.
- **Check state:** `GET /api/health`.

## Troubleshooting
| Symptom | Cause and fix |
|---|---|
| All API calls hang | Neon unreachable (some networks block port 5432) and no archive tunnel. Open the tunnel, or restart the backend. |
| `archive: down` | The SSH tunnel is closed or the server Postgres is stopped. The app serves Neon (2023 only) meanwhile. |
| Loader fails with 429 | Jolpica rate limit. Wait, run seasons one at a time, or run from another network. |
| `ModuleNotFoundError: httpx` | Run `pip install -r backend/requirements.txt` in the backend venv. |
| FastF1 "No data for this session" | The timing feed returned 401, or the session is too recent. Use `--results-only`. |

## Security notes
- Never commit `.env` files or `neon_setup.txt`. Rotate the Neon keys in that file, and change any password that has been shared in chat or screenshots.
- The archive database trusts localhost connections. Keep it reachable only through the SSH tunnel.
- The OpenF1 and Jolpica APIs are public and keyless.

## Testing status
There are no automated tests yet (`backend/app/tests/` and `etl/tests/` are empty). A first target would be `/api/races/seasons` and the rating math. Frontend checks: `npm run lint` and `npm run build`.
