"""Offline import of the Kaggle 'Formula 1 World Championship' CSVs (an Ergast dump) for seasons Jolpica
cannot serve under its rate limit. Gives results, qualifying, official per-round standings, race laps and
pit-stop laps. It has no tyre compound/age or telemetry, so those features stay limited to FastF1 seasons.
"""
from __future__ import annotations

import logging
import os

import pandas as pd
from pitgenius_db.models import (
    Circuit,
    ConstructorStanding,
    Driver,
    DriverStanding,
    LapTime,
    QualifyingResult,
    Race,
    RaceResult,
    Team,
)
from sqlalchemy.orm import Session as OrmSession

from ..load.upsert import fetch_ref_id_map, upsert_rows
from ..normalize.results import parse_time_to_ms
from ..pipeline import _upsert_session
from ..seed.team_colors import TEAM_COLORS

log = logging.getLogger(__name__)


def _csv(directory: str, name: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(directory, f"{name}.csv"), na_values=["\\N"], keep_default_na=False)


def _int(v):
    return None if pd.isna(v) else int(v)


def _ms(v):
    return parse_time_to_ms(None if pd.isna(v) else v)


def import_kaggle_season(db: OrmSession, directory: str, season: int) -> None:
    races = _csv(directory, "races")
    races = races[races.year == season]
    if races.empty:
        log.warning("No races for %s in the Kaggle data", season)
        return
    circuits = _csv(directory, "circuits").set_index("circuitId")
    drivers = _csv(directory, "drivers").set_index("driverId")
    constructors = _csv(directory, "constructors").set_index("constructorId")
    status = _csv(directory, "status").set_index("statusId")["status"]
    race_ids = set(races.raceId)
    results = _csv(directory, "results")
    results = results[results.raceId.isin(race_ids)]

    # Reference rows. The circuit upsert carries only reference fields, so FastF1 track outlines survive.
    upsert_rows(
        db,
        Circuit.__table__,
        [
            {"circuit_ref": c.circuitRef, "name": c.name, "locality": c.location, "country": c.country,
             "lat": None if pd.isna(c.lat) else float(c.lat), "lng": None if pd.isna(c.lng) else float(c.lng)}
            for c in circuits.loc[races.circuitId.unique()].itertuples()
        ],
        conflict_cols=["circuit_ref"],
    )
    upsert_rows(
        db,
        Team.__table__,
        [
            {"constructor_ref": c.constructorRef, "name": c.name, "nationality": c.nationality,
             "color_primary": (TEAM_COLORS.get(c.constructorRef) or (None, None))[0],
             "color_secondary": (TEAM_COLORS.get(c.constructorRef) or (None, None))[1]}
            for c in constructors.loc[results.constructorId.unique()].itertuples()
        ],
        conflict_cols=["constructor_ref"],
    )
    upsert_rows(
        db,
        Driver.__table__,
        [
            {"driver_ref": d.driverRef, "fastf1_code": None if pd.isna(d.code) else d.code,
             "permanent_number": _int(d.number), "given_name": d.forename, "family_name": d.surname,
             "nationality": d.nationality, "date_of_birth": None if pd.isna(d.dob) else pd.Timestamp(d.dob).date()}
            for d in drivers.loc[results.driverId.unique()].itertuples()
        ],
        conflict_cols=["driver_ref"],
    )
    db.flush()
    circuit_by_ref = fetch_ref_id_map(db, Circuit.__table__, "circuit_ref")
    team_by_ref = fetch_ref_id_map(db, Team.__table__, "constructor_ref")
    driver_by_ref = fetch_ref_id_map(db, Driver.__table__, "driver_ref")
    team_id = {k: team_by_ref[r] for k, r in constructors.constructorRef.items() if r in team_by_ref}
    driver_id = {k: driver_by_ref[r] for k, r in drivers.driverRef.items() if r in driver_by_ref}

    upsert_rows(
        db,
        Race.__table__,
        [
            {"season": season, "round": int(r.round),
             "circuit_id": circuit_by_ref[circuits.loc[r.circuitId, "circuitRef"]],
             "name": r.name, "race_date": pd.Timestamp(r.date).date(),
             "event_format": "sprint" if not pd.isna(r.sprint_date) else "conventional"}
            for r in races.itertuples()
        ],
        conflict_cols=["season", "round"],
    )
    db.flush()
    race_db_id = {r.round: r.id for r in db.execute(Race.__table__.select().where(Race.season == season)).all()}
    round_of = dict(zip(races.raceId, races["round"]))

    qualifying = _csv(directory, "qualifying")
    pit = _csv(directory, "pit_stops")
    laps = _csv(directory, "lap_times")
    standings_d = _csv(directory, "driver_standings")
    standings_c = _csv(directory, "constructor_standings")
    pit_laps = {(r.raceId, r.driverId, r.lap) for r in pit[pit.raceId.isin(race_ids)].itertuples()}

    for race_id, round_ in round_of.items():
        rid = race_db_id[int(round_)]
        q_sid, r_sid = _upsert_session(db, rid, "Q"), _upsert_session(db, rid, "R")

        upsert_rows(
            db,
            QualifyingResult.__table__,
            [
                {"session_id": q_sid, "driver_id": driver_id[x.driverId], "team_id": team_id[x.constructorId],
                 "position": _int(x.position), "q1_ms": _ms(x.q1), "q2_ms": _ms(x.q2), "q3_ms": _ms(x.q3)}
                for x in qualifying[qualifying.raceId == race_id].itertuples()
            ],
            conflict_cols=["session_id", "driver_id"],
        )

        r = results[results.raceId == race_id]
        upsert_rows(
            db,
            RaceResult.__table__,
            [
                {"session_id": r_sid, "driver_id": driver_id[x.driverId], "team_id": team_id[x.constructorId],
                 "grid_position": _int(x.grid),
                 "finish_position": int(x.positionOrder) if str(x.positionText).isdigit() else None,
                 "status": status[x.statusId], "points": float(x.points), "laps_completed": _int(x.laps),
                 "total_time_ms": _int(x.milliseconds), "fastest_lap_rank": _int(x.rank)}
                for x in r.itertuples()
            ],
            conflict_cols=["session_id", "driver_id"],
        )
        team_of_driver = {x.driverId: x.constructorId for x in r.itertuples()}

        upsert_rows(
            db,
            DriverStanding.__table__,
            [
                {"season": season, "round": int(round_), "driver_id": driver_id[x.driverId],
                 "team_id": team_id.get(team_of_driver.get(x.driverId)), "position": int(x.position),
                 "points": float(x.points), "wins": int(x.wins)}
                for x in standings_d[standings_d.raceId == race_id].itertuples()
            ],
            conflict_cols=["season", "round", "driver_id"],
        )
        upsert_rows(
            db,
            ConstructorStanding.__table__,
            [
                {"season": season, "round": int(round_), "team_id": team_id[x.constructorId],
                 "position": int(x.position), "points": float(x.points), "wins": int(x.wins)}
                for x in standings_c[standings_c.raceId == race_id].itertuples()
            ],
            conflict_cols=["season", "round", "team_id"],
        )
        upsert_rows(
            db,
            LapTime.__table__,
            [
                {"session_id": r_sid, "driver_id": driver_id[x.driverId], "lap_number": int(x.lap),
                 "lap_time_ms": _int(x.milliseconds), "position": _int(x.position),
                 "is_pit_lap": (race_id, x.driverId, x.lap) in pit_laps}
                for x in laps[laps.raceId == race_id].itertuples()
            ],
            conflict_cols=["session_id", "driver_id", "lap_number"],
        )
        db.commit()
        log.info("Kaggle import season=%s round=%s done", season, round_)
