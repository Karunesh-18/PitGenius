from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from pitgenius_db.models import ConstructorStanding, Driver, DriverStanding, Team

from ..db import get_db
from ..schemas.standings import ConstructorStandingRow, DriverStandingRow
from ..services.queries import latest_season

router = APIRouter(prefix="/api/standings", tags=["standings"])


def _latest_round_for_season(db: OrmSession, season: int) -> int | None:
    return db.execute(
        select(DriverStanding.round).where(DriverStanding.season == season).order_by(DriverStanding.round.desc())
    ).scalars().first()


@router.get("/drivers", response_model=list[DriverStandingRow])
def driver_standings(
    season: int | None = Query(default=None), round: int | None = Query(default=None), db: OrmSession = Depends(get_db)
):
    season = season or latest_season(db)
    if season is None:
        return []
    round = round or _latest_round_for_season(db, season)
    if round is None:
        return []

    stmt = (
        select(DriverStanding.position, Driver.driver_ref, Driver.fastf1_code, Driver.given_name, Driver.family_name,
               Team.constructor_ref, DriverStanding.points, DriverStanding.wins)
        .join(Driver, DriverStanding.driver_id == Driver.id)
        .outerjoin(Team, DriverStanding.team_id == Team.id)
        .where(DriverStanding.season == season, DriverStanding.round == round)
        .order_by(DriverStanding.position)
    )
    return [
        DriverStandingRow(position=pos, driver_ref=dref, code=code, given_name=gn, family_name=fn, team_ref=tref, points=float(pts), wins=wins)
        for pos, dref, code, gn, fn, tref, pts, wins in db.execute(stmt).all()
    ]


@router.get("/constructors", response_model=list[ConstructorStandingRow])
def constructor_standings(
    season: int | None = Query(default=None), round: int | None = Query(default=None), db: OrmSession = Depends(get_db)
):
    season = season or latest_season(db)
    if season is None:
        return []
    round = round or _latest_round_for_season(db, season)
    if round is None:
        return []

    stmt = (
        select(ConstructorStanding.position, Team.constructor_ref, Team.name, ConstructorStanding.points, ConstructorStanding.wins)
        .join(Team, ConstructorStanding.team_id == Team.id)
        .where(ConstructorStanding.season == season, ConstructorStanding.round == round)
        .order_by(ConstructorStanding.position)
    )
    return [
        ConstructorStandingRow(position=pos, team_ref=tref, name=name, points=float(pts), wins=wins)
        for pos, tref, name, pts, wins in db.execute(stmt).all()
    ]
