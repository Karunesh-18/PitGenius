"""Shared read queries used by more than one analytics service."""
from __future__ import annotations

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from pitgenius_db.models import Circuit, LapTime, QualifyingResult, Race, RaceResult
from pitgenius_db.models import Session as SessionModel


def latest_season(db: OrmSession) -> int | None:
    return db.execute(select(func.max(Race.season))).scalar_one_or_none()


def race_results_df(db: OrmSession, season: int) -> pd.DataFrame:
    stmt = (
        select(
            RaceResult.driver_id,
            RaceResult.team_id,
            RaceResult.finish_position,
            RaceResult.status,
            RaceResult.points,
        )
        .join(SessionModel, RaceResult.session_id == SessionModel.id)
        .join(Race, SessionModel.race_id == Race.id)
        .where(Race.season == season, SessionModel.session_type == "R")
    )
    rows = db.execute(stmt).all()
    return pd.DataFrame(rows, columns=["driver_id", "team_id", "finish_position", "status", "points"])


def qualifying_results_df(db: OrmSession, season: int) -> pd.DataFrame:
    stmt = (
        select(QualifyingResult.driver_id, QualifyingResult.position)
        .join(SessionModel, QualifyingResult.session_id == SessionModel.id)
        .join(Race, SessionModel.race_id == Race.id)
        .where(Race.season == season, SessionModel.session_type == "Q")
    )
    rows = db.execute(stmt).all()
    return pd.DataFrame(rows, columns=["driver_id", "position"])


def lap_times_df(db: OrmSession, season: int) -> pd.DataFrame:
    stmt = (
        select(LapTime.driver_id, LapTime.lap_time_ms, LapTime.is_pit_lap)
        .join(SessionModel, LapTime.session_id == SessionModel.id)
        .join(Race, SessionModel.race_id == Race.id)
        .where(Race.season == season, SessionModel.session_type == "R")
    )
    rows = db.execute(stmt).all()
    return pd.DataFrame(rows, columns=["driver_id", "lap_time_ms", "is_pit_lap"])


def lap_times_with_context_df(db: OrmSession, season: int) -> pd.DataFrame:
    """Race-session lap times joined out to circuit + race context, used by
    the tire degradation model and circuit intelligence service."""
    stmt = (
        select(
            LapTime.driver_id,
            Circuit.circuit_ref,
            Race.id.label("race_id"),
            LapTime.lap_number,
            LapTime.lap_time_ms,
            LapTime.is_pit_lap,
            LapTime.position,
            LapTime.compound,
            LapTime.tyre_life,
            LapTime.track_status,
        )
        .join(SessionModel, LapTime.session_id == SessionModel.id)
        .join(Race, SessionModel.race_id == Race.id)
        .join(Circuit, Race.circuit_id == Circuit.id)
        .where(Race.season == season, SessionModel.session_type == "R")
    )
    rows = db.execute(stmt).all()
    return pd.DataFrame(
        rows,
        columns=[
            "driver_id",
            "circuit_ref",
            "race_id",
            "lap_number",
            "lap_time_ms",
            "is_pit_lap",
            "position",
            "compound",
            "tyre_life",
            "track_status",
        ],
    )
