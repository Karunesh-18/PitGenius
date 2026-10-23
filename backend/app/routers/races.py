import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.orm import Session as OrmSession

from pitgenius_db.models import (
    Circuit,
    Driver,
    LapTime,
    QualifyingResult,
    Race,
    RaceResult,
)
from pitgenius_db.models import Session as SessionModel
from pitgenius_db.models import Team

from ..db import get_db
from ..schemas.race import QualifyingResultRow
from ..schemas.race import RaceResultRow as RaceResultRowSchema
from ..schemas.race import RaceDetail, RaceSummary
from ..schemas.telemetry import TelemetryAvailabilityRow, TelemetryOut
from ..services.queries import latest_season
from ..services.telemetry import get_driver_telemetry, list_telemetry_drivers

router = APIRouter(prefix="/api/races", tags=["races"])


def _winner_subquery():
    """race_id -> winning driver/team refs, one row per race. A single
    subquery joined once into the list query rather than a per-race lookup."""
    return (
        select(
            SessionModel.race_id.label("race_id"),
            Driver.driver_ref.label("winner_driver_ref"),
            Driver.fastf1_code.label("winner_code"),
            Team.constructor_ref.label("winner_team_ref"),
        )
        .select_from(RaceResult)
        .join(SessionModel, RaceResult.session_id == SessionModel.id)
        .join(Driver, RaceResult.driver_id == Driver.id)
        .join(Team, RaceResult.team_id == Team.id)
        .where(SessionModel.session_type == "R", RaceResult.finish_position == 1)
        .subquery()
    )


@router.get("", response_model=list[RaceSummary])
def list_races(season: int | None = Query(default=None), db: OrmSession = Depends(get_db)):
    season = season or latest_season(db)
    if season is None:
        return []

    winner_subq = _winner_subquery()
    stmt = (
        select(
            Race.round,
            Race.name,
            Circuit.circuit_ref,
            Circuit.country,
            Race.race_date,
            winner_subq.c.winner_driver_ref,
            winner_subq.c.winner_code,
            winner_subq.c.winner_team_ref,
        )
        .join(Circuit, Race.circuit_id == Circuit.id)
        .outerjoin(winner_subq, winner_subq.c.race_id == Race.id)
        .where(Race.season == season)
        .order_by(Race.round)
    )
    today = dt.date.today()
    return [
        RaceSummary(
            season=season,
            round=round_,
            name=name,
            circuit_ref=circuit_ref,
            race_date=race_date,
            status="completed" if race_date < today else "upcoming",
            country=country,
            winner_driver_ref=winner_driver_ref,
            winner_code=winner_code,
            winner_team_ref=winner_team_ref,
        )
        for round_, name, circuit_ref, country, race_date, winner_driver_ref, winner_code, winner_team_ref in db.execute(
            stmt
        ).all()
    ]


@router.get("/{season}/{round}", response_model=RaceDetail)
def get_race(season: int, round: int, db: OrmSession = Depends(get_db)):
    row = db.execute(
        select(Race.id, Race.name, Circuit.circuit_ref, Circuit.country, Race.race_date)
        .join(Circuit, Race.circuit_id == Circuit.id)
        .where(Race.season == season, Race.round == round)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Race not found")
    race_id, name, circuit_ref, country, race_date = row

    quali_stmt = (
        select(QualifyingResult.position, Driver.driver_ref, Driver.fastf1_code, Team.constructor_ref,
               QualifyingResult.q1_ms, QualifyingResult.q2_ms, QualifyingResult.q3_ms)
        .join(SessionModel, QualifyingResult.session_id == SessionModel.id)
        .join(Race, SessionModel.race_id == Race.id)
        .join(Driver, QualifyingResult.driver_id == Driver.id)
        .join(Team, QualifyingResult.team_id == Team.id)
        .where(Race.season == season, Race.round == round, SessionModel.session_type == "Q")
        .order_by(QualifyingResult.position)
    )
    qualifying_results = [
        QualifyingResultRow(position=pos, driver_ref=dref, code=code, team_ref=tref, q1_ms=q1, q2_ms=q2, q3_ms=q3)
        for pos, dref, code, tref, q1, q2, q3 in db.execute(quali_stmt).all()
    ]

    # Compound of each driver's last completed race lap. Scoped to this race's
    # own session ids — without that the GROUP BY scans the whole lap_times
    # table (the outer join's ON clause can't be pushed down into it), which
    # grows with every season ingested rather than staying per-race.
    race_session_ids = select(SessionModel.id).where(SessionModel.race_id == race_id).scalar_subquery()
    final_compound_subq = (
        select(
            LapTime.session_id.label("session_id"),
            LapTime.driver_id.label("driver_id"),
            LapTime.compound.label("final_compound"),
        )
        .where(LapTime.session_id.in_(race_session_ids))
        .distinct(LapTime.session_id, LapTime.driver_id)
        .order_by(LapTime.session_id, LapTime.driver_id, LapTime.lap_number.desc())
        .subquery()
    )

    race_stmt = (
        select(
            RaceResult.finish_position, RaceResult.grid_position, Driver.driver_ref, Driver.fastf1_code,
            Team.constructor_ref, RaceResult.status, RaceResult.points, RaceResult.fastest_lap_rank,
            final_compound_subq.c.final_compound,
        )
        .join(SessionModel, RaceResult.session_id == SessionModel.id)
        .join(Race, SessionModel.race_id == Race.id)
        .join(Driver, RaceResult.driver_id == Driver.id)
        .join(Team, RaceResult.team_id == Team.id)
        .outerjoin(
            final_compound_subq,
            and_(
                final_compound_subq.c.session_id == RaceResult.session_id,
                final_compound_subq.c.driver_id == RaceResult.driver_id,
            ),
        )
        .where(Race.season == season, Race.round == round, SessionModel.session_type == "R")
        .order_by(RaceResult.finish_position.is_(None), RaceResult.finish_position)
    )
    race_results = [
        RaceResultRowSchema(
            finish_position=fp, grid_position=gp, driver_ref=dref, code=code, team_ref=tref, status=status,
            points=float(points), fastest_lap_rank=fl_rank, final_compound=final_compound,
        )
        for fp, gp, dref, code, tref, status, points, fl_rank, final_compound in db.execute(race_stmt).all()
    ]

    winner_row = next((r for r in race_results if r.finish_position == 1), None)

    today = dt.date.today()
    return RaceDetail(
        season=season,
        round=round,
        name=name,
        circuit_ref=circuit_ref,
        race_date=race_date,
        status="completed" if race_date < today else "upcoming",
        country=country,
        winner_driver_ref=winner_row.driver_ref if winner_row else None,
        winner_code=winner_row.code if winner_row else None,
        winner_team_ref=winner_row.team_ref if winner_row else None,
        qualifying_results=qualifying_results,
        race_results=race_results,
    )


@router.get("/{season}/{round}/telemetry", response_model=list[TelemetryAvailabilityRow])
def get_race_telemetry_availability(season: int, round: int, db: OrmSession = Depends(get_db)):
    rows = list_telemetry_drivers(db, season, round)
    return [TelemetryAvailabilityRow(**row) for row in rows]


@router.get("/{season}/{round}/telemetry/{driver_ref}", response_model=TelemetryOut)
def get_race_driver_telemetry(season: int, round: int, driver_ref: str, db: OrmSession = Depends(get_db)):
    result = get_driver_telemetry(db, season, round, driver_ref)
    if result is None:
        raise HTTPException(status_code=404, detail="No telemetry found for this driver/race")
    return TelemetryOut(**result)
