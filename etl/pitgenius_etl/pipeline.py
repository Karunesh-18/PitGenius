"""ETL orchestration: fetch (Jolpica + FastF1) -> normalize -> upsert (Postgres).

Entry points are run_season() and run_round(); both are pure functions of
their arguments (no CLI/global-state coupling) so they can later become
Celery task bodies with no rework — see docs/phase1-plan.md.
"""
from __future__ import annotations

import logging

from pitgenius_db.models import (
    Circuit,
    ConstructorStanding,
    Driver,
    DriverStanding,
    LapTime,
    QualifyingResult,
    Race,
    RaceResult,
    Telemetry,
)
from pitgenius_db.models import Session as SessionModel
from pitgenius_db.models import Team
from sqlalchemy.orm import Session as OrmSession

from .cache import enable_fastf1_cache
from .config import Settings, get_settings
from .db import make_session_factory
from .load.upsert import fetch_ref_id_map, upsert_rows
from .normalize.laps import normalize_laps
from .normalize.reference import normalize_circuit, normalize_driver, normalize_race, normalize_team
from .normalize.results import (
    normalize_constructor_standing,
    normalize_driver_standing,
    normalize_qualifying_results,
    normalize_race_results,
)
from .normalize.telemetry import build_driver_lap_telemetry
from .normalize.track_outline import build_track_outline
from .sources.fastf1_client import (
    get_driver_fastest_lap_telemetry,
    get_fastest_lap_telemetry,
    get_laps,
    load_session,
    load_session_with_telemetry,
)
from .sources.jolpica_client import JolpicaClient

log = logging.getLogger(__name__)


def _sync_reference_data(db: OrmSession, jolpica: JolpicaClient, season: int) -> list[dict]:
    """Upsert circuits, races, teams, drivers for a season. Returns the raw
    season schedule (list of Jolpica race dicts) for the caller to iterate.
    """
    schedule = jolpica.get_season_races(season)

    circuit_rows = [normalize_circuit(race["Circuit"]) for race in schedule]
    # dedupe by circuit_ref (a circuit can host multiple rounds across seasons, not within one, but be safe)
    circuit_rows = list({row["circuit_ref"]: row for row in circuit_rows}.values())
    upsert_rows(db, Circuit.__table__, circuit_rows, conflict_cols=["circuit_ref"])
    db.flush()
    circuit_ref_to_id = fetch_ref_id_map(db, Circuit.__table__, "circuit_ref")

    race_rows = [normalize_race(race, circuit_ref_to_id[race["Circuit"]["circuitId"]]) for race in schedule]
    upsert_rows(db, Race.__table__, race_rows, conflict_cols=["season", "round"])

    team_rows = [normalize_team(c) for c in jolpica.get_constructors(season)]
    upsert_rows(db, Team.__table__, team_rows, conflict_cols=["constructor_ref"])

    driver_rows = [normalize_driver(d) for d in jolpica.get_drivers(season)]
    upsert_rows(db, Driver.__table__, driver_rows, conflict_cols=["driver_ref"])

    db.flush()
    return schedule


def _upsert_session(db: OrmSession, race_id: int, session_type: str) -> int:
    upsert_rows(
        db,
        SessionModel.__table__,
        [{"race_id": race_id, "session_type": session_type}],
        conflict_cols=["race_id", "session_type"],
    )
    db.flush()
    row = db.execute(
        SessionModel.__table__.select().where(
            SessionModel.race_id == race_id, SessionModel.session_type == session_type
        )
    ).first()
    return row.id


def run_round(
    db: OrmSession, jolpica: JolpicaClient, season: int, round_: int, race_id: int, results_only: bool = False
) -> None:
    driver_ref_to_id = fetch_ref_id_map(db, Driver.__table__, "driver_ref")
    team_ref_to_id = fetch_ref_id_map(db, Team.__table__, "constructor_ref")
    code_to_driver_id = {
        row.fastf1_code: row.id
        for row in db.execute(Driver.__table__.select()).all()
        if row.fastf1_code
    }

    # --- Jolpica: qualifying + race results, standings ---
    quali_races = jolpica.get_qualifying(season, round_)
    if quali_races:
        q_session_id = _upsert_session(db, race_id, "Q")
        quali_rows = normalize_qualifying_results(quali_races[0], driver_ref_to_id, team_ref_to_id)
        for row in quali_rows:
            row["session_id"] = q_session_id
        upsert_rows(db, QualifyingResult.__table__, quali_rows, conflict_cols=["session_id", "driver_id"])

    result_races = jolpica.get_results(season, round_)
    if result_races:
        r_session_id = _upsert_session(db, race_id, "R")
        result_rows = normalize_race_results(result_races[0], driver_ref_to_id, team_ref_to_id)
        for row in result_rows:
            row["session_id"] = r_session_id
        upsert_rows(db, RaceResult.__table__, result_rows, conflict_cols=["session_id", "driver_id"])
    else:
        r_session_id = _upsert_session(db, race_id, "R")

    standing_rows = [
        s
        for entry in jolpica.get_driver_standings(season, round_)
        if (s := normalize_driver_standing(entry, season, round_, driver_ref_to_id, team_ref_to_id))
    ]
    upsert_rows(db, DriverStanding.__table__, standing_rows, conflict_cols=["season", "round", "driver_id"])

    constructor_standing_rows = [
        s
        for entry in jolpica.get_constructor_standings(season, round_)
        if (s := normalize_constructor_standing(entry, season, round_, team_ref_to_id))
    ]
    upsert_rows(
        db, ConstructorStanding.__table__, constructor_standing_rows, conflict_cols=["season", "round", "team_id"]
    )

    if results_only:
        db.commit()
        return

    # --- FastF1: lap times for Q and R sessions ---
    for session_type, session_id in (("Q", q_session_id if quali_races else None), ("R", r_session_id)):
        if session_id is None:
            continue
        try:
            ff1_session = load_session(season, round_, session_type)
        except Exception:
            log.warning("FastF1 session load failed for %s %s %s", season, round_, session_type, exc_info=True)
            continue
        laps_df = get_laps(ff1_session)
        lap_rows = normalize_laps(laps_df, session_id, code_to_driver_id)
        upsert_rows(db, LapTime.__table__, lap_rows, conflict_cols=["session_id", "driver_id", "lap_number"])

    db.commit()


def _backfill_track_outlines(db: OrmSession, season: int, schedule: list[dict]) -> None:
    # A circuit needs backfilling if it has no outline OR (having been written
    # before the Phase 2 columns existed) no normalization params — telemetry
    # can't be placed in the ribbon's coordinate frame without the latter.
    circuits_missing = {
        row.circuit_ref: row.id
        for row in db.execute(
            Circuit.__table__.select().where(
                Circuit.track_outline.is_(None) | Circuit.track_outline_scale.is_(None)
            )
        ).all()
    }
    if not circuits_missing:
        return
    for race in schedule:
        circuit_ref = race["Circuit"]["circuitId"]
        if circuit_ref not in circuits_missing:
            continue
        try:
            telemetry = get_fastest_lap_telemetry(season, int(race["round"]))
        except Exception:
            # One circuit's telemetry failing must not abort the remaining ones.
            log.warning("Track outline telemetry failed for %s round %s", season, race["round"], exc_info=True)
            continue
        if telemetry is None:
            continue
        outline, center_x, center_y, center_z, scale = build_track_outline(telemetry)
        if not outline:
            continue
        db.execute(
            Circuit.__table__.update()
            .where(Circuit.circuit_ref == circuit_ref)
            .values(
                track_outline=outline,
                track_outline_center_x=center_x,
                track_outline_center_y=center_y,
                track_outline_center_z=center_z,
                track_outline_scale=scale,
            )
        )
        db.commit()
        del circuits_missing[circuit_ref]


def run_season(
    season: int, rounds: list[int] | None = None, settings: Settings | None = None, results_only: bool = False
) -> None:
    settings = settings or get_settings()
    enable_fastf1_cache(settings)
    session_factory = make_session_factory(settings)
    jolpica = JolpicaClient(settings.jolpica_base_url)

    with session_factory() as db:
        schedule = _sync_reference_data(db, jolpica, season)
        db.commit()

        race_id_by_round = {
            row.round: row.id for row in db.execute(Race.__table__.select().where(Race.season == season)).all()
        }

        target_rounds = rounds if rounds is not None else sorted(int(r["round"]) for r in schedule)
        for round_ in target_rounds:
            race_id = race_id_by_round.get(round_)
            if race_id is None:
                log.warning("No race row for season=%s round=%s, skipping", season, round_)
                continue
            log.info("Running season=%s round=%s", season, round_)
            run_round(db, jolpica, season, round_, race_id, results_only)

        if not results_only:
            _backfill_track_outlines(db, season, schedule)


def run_telemetry_round(db: OrmSession, season: int, round_: int, race_id: int) -> None:
    """Load one representative (fastest) lap of telemetry per driver for
    the race's R session and upsert into the telemetry table.

    Not called from run_season — this is a separate, deliberately slower
    pipeline step (telemetry=True FastF1 loads are much heavier), invoked
    via its own CLI subcommand / run_telemetry_season.
    """
    race_row = db.execute(Race.__table__.select().where(Race.id == race_id)).first()
    if race_row is None:
        log.warning("No race row for race_id=%s (season=%s round=%s), skipping telemetry", race_id, season, round_)
        return

    circuit_row = db.execute(Circuit.__table__.select().where(Circuit.id == race_row.circuit_id)).first()
    if circuit_row is None or any(
        v is None
        for v in (
            circuit_row.track_outline_center_x,
            circuit_row.track_outline_center_y,
            circuit_row.track_outline_center_z,
            circuit_row.track_outline_scale,
        )
    ):
        log.warning(
            "Circuit normalization params not yet backfilled for season=%s round=%s "
            "(run_season's track-outline backfill hasn't reached this circuit yet), skipping telemetry",
            season,
            round_,
        )
        return
    norm_params = (
        float(circuit_row.track_outline_center_x),
        float(circuit_row.track_outline_center_y),
        float(circuit_row.track_outline_center_z),
        float(circuit_row.track_outline_scale),
    )

    r_session_row = db.execute(
        SessionModel.__table__.select().where(SessionModel.race_id == race_id, SessionModel.session_type == "R")
    ).first()
    if r_session_row is None:
        log.warning(
            "No R session row for season=%s round=%s (run the standard `run` pipeline first), skipping telemetry",
            season,
            round_,
        )
        return
    r_session_id = r_session_row.id

    try:
        ff1_session = load_session_with_telemetry(season, round_, "R")
    except Exception:
        log.warning("FastF1 telemetry session load failed for %s %s R", season, round_, exc_info=True)
        return

    code_to_driver_id = {
        row.fastf1_code: row.id
        for row in db.execute(Driver.__table__.select()).all()
        if row.fastf1_code
    }

    codes = sorted({c for c in ff1_session.laps["Driver"].unique() if isinstance(c, str)})
    for code in codes:
        driver_id = code_to_driver_id.get(code)
        if driver_id is None:
            log.warning("No driver_id for FastF1 code=%s, skipping telemetry for this driver", code)
            continue
        result = get_driver_fastest_lap_telemetry(ff1_session, code)
        if result is None:
            continue
        lap_number, _lap_time_ms, telemetry_df = result
        rows = build_driver_lap_telemetry(telemetry_df, r_session_id, driver_id, lap_number, norm_params)
        if not rows:
            continue
        # lap_number is part of the unique key, so if a re-run picks a different
        # fastest lap (refreshed FastF1 cache, corrected timing) the upsert would
        # leave both laps behind and reads would interleave them. Clear first.
        db.execute(
            Telemetry.__table__.delete().where(
                Telemetry.session_id == r_session_id,
                Telemetry.driver_id == driver_id,
                Telemetry.lap_number != lap_number,
            )
        )
        upsert_rows(
            db,
            Telemetry.__table__,
            rows,
            conflict_cols=["session_id", "driver_id", "lap_number", "point_index"],
        )
    db.commit()


def run_telemetry_season(season: int, rounds: list[int] | None = None, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    enable_fastf1_cache(settings)
    session_factory = make_session_factory(settings)

    with session_factory() as db:
        race_id_by_round = {
            row.round: row.id for row in db.execute(Race.__table__.select().where(Race.season == season)).all()
        }

        target_rounds = rounds or sorted(race_id_by_round.keys())
        for round_ in target_rounds:
            race_id = race_id_by_round.get(round_)
            if race_id is None:
                log.warning("No race row for season=%s round=%s, skipping telemetry", season, round_)
                continue
            log.info("Running telemetry season=%s round=%s", season, round_)
            run_telemetry_round(db, season, round_, race_id)


def sync_season(season: int, settings: Settings | None = None) -> list[int]:
    """Load rounds that have already been raced but have no results yet.
    Cheap to run repeatedly: returns [] (and downloads nothing) when up to date.
    """
    import datetime as dt

    settings = settings or get_settings()
    session_factory = make_session_factory(settings)
    with session_factory() as db:
        done = {
            r.round
            for r in db.execute(
                Race.__table__.select()
                .join(SessionModel.__table__, SessionModel.race_id == Race.id)
                .join(RaceResult.__table__, RaceResult.session_id == SessionModel.id)
                .where(Race.season == season)
            ).all()
        }
        due = [
            r.round
            for r in db.execute(Race.__table__.select().where(Race.season == season)).all()
            if r.race_date < dt.date.today() and r.round not in done
        ]
    if not due:
        # The calendar itself may be new (fresh season) or have no rounds yet.
        run_season(season, rounds=[], settings=settings)
        return []
    run_season(season, rounds=due, settings=settings)
    run_telemetry_season(season, rounds=due, settings=settings)
    return due


def _merge_rounds(races: list[dict], key: str) -> list[dict]:
    """Jolpica paginates by result row, so one race can arrive split across pages: merge by round."""
    merged: dict[int, dict] = {}
    for race in races:
        m = merged.setdefault(int(race["round"]), {**race, key: []})
        m[key].extend(race.get(key, []))
    return [merged[r] for r in sorted(merged)]


def run_season_bulk(season: int, settings: Settings | None = None) -> None:
    """Whole-season load in ~12 Jolpica calls (vs ~100 for run_season): results, qualifying and
    standings only, no FastF1. Free-tier rate limits make the per-round path impractical for old seasons.

    ponytail: per-round standings are cumulated from race results, so sprint points are missing
    mid-season; the last round uses Jolpica's official standings. Use `run` for exact per-round data.
    """
    settings = settings or get_settings()
    session_factory = make_session_factory(settings)
    jolpica = JolpicaClient(settings.jolpica_base_url)

    with session_factory() as db:
        _sync_reference_data(db, jolpica, season)
        db.commit()
        race_id_by_round = {
            r.round: r.id for r in db.execute(Race.__table__.select().where(Race.season == season)).all()
        }
        driver_ref_to_id = fetch_ref_id_map(db, Driver.__table__, "driver_ref")
        team_ref_to_id = fetch_ref_id_map(db, Team.__table__, "constructor_ref")

        for race in _merge_rounds(jolpica.get_qualifying(season), "QualifyingResults"):
            race_id = race_id_by_round.get(int(race["round"]))
            if race_id is None:
                continue
            sid = _upsert_session(db, race_id, "Q")
            rows = normalize_qualifying_results(race, driver_ref_to_id, team_ref_to_id)
            for row in rows:
                row["session_id"] = sid
            upsert_rows(db, QualifyingResult.__table__, rows, conflict_cols=["session_id", "driver_id"])

        d_pts: dict[int, float] = {}
        d_wins: dict[int, int] = {}
        d_team: dict[int, int] = {}
        t_pts: dict[int, float] = {}
        t_wins: dict[int, int] = {}
        last_round = 0
        for race in _merge_rounds(jolpica.get_results(season), "Results"):
            round_ = int(race["round"])
            race_id = race_id_by_round.get(round_)
            if race_id is None:
                continue
            sid = _upsert_session(db, race_id, "R")
            rows = normalize_race_results(race, driver_ref_to_id, team_ref_to_id)
            for row in rows:
                row["session_id"] = sid
                d, t = row["driver_id"], row["team_id"]
                d_pts[d] = d_pts.get(d, 0) + row["points"]
                t_pts[t] = t_pts.get(t, 0) + row["points"]
                d_team[d] = t
                if row["finish_position"] == 1:
                    d_wins[d] = d_wins.get(d, 0) + 1
                    t_wins[t] = t_wins.get(t, 0) + 1
            upsert_rows(db, RaceResult.__table__, rows, conflict_cols=["session_id", "driver_id"])

            ranked_d = sorted(d_pts, key=lambda d: (-d_pts[d], -d_wins.get(d, 0)))
            upsert_rows(
                db,
                DriverStanding.__table__,
                [
                    {"season": season, "round": round_, "driver_id": d, "team_id": d_team[d], "position": i,
                     "points": d_pts[d], "wins": d_wins.get(d, 0)}
                    for i, d in enumerate(ranked_d, 1)
                ],
                conflict_cols=["season", "round", "driver_id"],
            )
            ranked_t = sorted(t_pts, key=lambda t: (-t_pts[t], -t_wins.get(t, 0)))
            upsert_rows(
                db,
                ConstructorStanding.__table__,
                [
                    {"season": season, "round": round_, "team_id": t, "position": i,
                     "points": t_pts[t], "wins": t_wins.get(t, 0)}
                    for i, t in enumerate(ranked_t, 1)
                ],
                conflict_cols=["season", "round", "team_id"],
            )
            last_round = round_
        db.commit()

        if last_round:  # overwrite the final round with official standings (includes sprint points)
            ds = [
                s for e in jolpica.get_driver_standings(season)
                if (s := normalize_driver_standing(e, season, last_round, driver_ref_to_id, team_ref_to_id))
            ]
            upsert_rows(db, DriverStanding.__table__, ds, conflict_cols=["season", "round", "driver_id"])
            cs = [
                s for e in jolpica.get_constructor_standings(season)
                if (s := normalize_constructor_standing(e, season, last_round, team_ref_to_id))
            ]
            upsert_rows(db, ConstructorStanding.__table__, cs, conflict_cols=["season", "round", "team_id"])
            db.commit()
