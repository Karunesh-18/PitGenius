# Data and ETL

## Sources
| Source | Used for | Notes |
|---|---|---|
| Jolpica F1 (`api.jolpi.ca/ergast/f1`) | Calendar, circuits, drivers, teams, qualifying, results, standings | Free. Rate-limited per IP (bursts return HTTP 429). Client throttles at 0.8 s per request and retries with backoff. |
| FastF1 3.8 | Lap times (Q and R sessions), fastest-lap telemetry, track outlines | Needs F1's timing feed. As of Oct 2026 the feed returns 401 from the GPU server, so no new laps or telemetry could be downloaded. |
| Kaggle F1 dataset | Offline bulk history (results, qualifying, standings, laps, pit stops) | One 6 MB download. Needs a Kaggle API token (`KAGGLE_API_TOKEN`), which must never be committed. |
| OpenF1 | Live session data | Free, no key. Used only by the Live page, not stored. |

## Database schema (`db/pitgenius_db/models.py`)
`circuits` (with `track_outline` JSONB and normalisation parameters) · `teams` · `drivers` · `races` (season, round, date) · `sessions` (FP1…R per race) · `qualifying_results` · `race_results` · `driver_standings` · `constructor_standings` · `lap_times` · `telemetry` (per-driver fastest-lap points). Unique keys such as `(season, round)` and `(session_id, driver_id)` make loads idempotent. Migrations are in `db/alembic/versions/` (phase 1 schema, phase 2 telemetry).

## ETL commands
Run from `etl/` with `DATABASE_URL` set (and `FASTF1_CACHE_DIR` for FastF1).
| Command | What it does | Cost |
|---|---|---|
| `python -m pitgenius_etl run --season N --results-only` | Whole-season bulk load: results, qualifying, standings. Per-round standings are derived by accumulating race points. The last round uses Jolpica's official standings. | about 12 requests |
| `python -m pitgenius_etl run --season N [--rounds 1,2]` | Per-round load including FastF1 laps and track outlines. Exact standings per round. | about 100 requests plus a large FastF1 download (about 2.4 GB per season cache) |
| `python -m pitgenius_etl telemetry --season N` | Fastest-lap telemetry per driver (run `run` first). | heavy |
| `python -m pitgenius_etl import-kaggle --dir <csv folder> --seasons 2018,2019` | Imports seasons from the Kaggle dataset `rohanrao/formula-1-world-championship-1950-2020` (an Ergast dump, 2009–2024 in the current version). No API limits. Loads results, qualifying, official per-round standings, race laps and pit-stop laps. No compound, tyre age or telemetry. Skip seasons that already have FastF1 laps (2023), or the upsert overwrites `is_pit_lap`. | seconds per season |
| `python -m pitgenius_etl sync [--season N]` | Loads rounds already raced but missing results. A no-op when up to date. | small |

## Known approximations
- Bulk (`--results-only`) standings omit sprint points mid-season. Only the final round is official.
- Pit efficiency is estimated from lap data, because there is no pit-stop table yet.
- New circuits from results-only loads have no track outline, so the 3D view works only where FastF1 data was loaded (2023).

## Archive on the GPU server
Postgres 16 runs from a user-space install (`pgserver`) in `~/pitgenius` on the server, bound to `127.0.0.1:55432`. Data directory: `~/pitgenius/pgdata`. It is not a system service, so it must be restarted with `pg_ctl` after a server reboot. Reach it from the dev machine with:
```
ssh -N -L 55432:127.0.0.1:55432 <user>@<server>
```
and set `ARCHIVE_DATABASE_URL=postgresql+psycopg://pitgenius@127.0.0.1:55432/pitgenius` in `backend/.env`. The database uses trust authentication on localhost only, so never expose the port beyond the tunnel.
