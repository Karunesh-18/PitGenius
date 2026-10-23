from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from pitgenius_db.models import Driver, DriverStanding, Race, RaceResult, Session as SessionModel, Team

from ..db import get_db
from ..schemas.driver import DriverDetail, DriverSummary, PointsHistoryPoint, RaceResultRow
from ..services.driver_rating import compute_driver_ratings
from ..services.queries import latest_season

router = APIRouter(prefix="/api/drivers", tags=["drivers"])


@router.get("", response_model=list[DriverSummary])
def list_drivers(season: int | None = Query(default=None), db: OrmSession = Depends(get_db)):
    season = season or latest_season(db)
    if season is None:
        return []

    ratings = compute_driver_ratings(db, season)
    if not ratings:
        return []

    drivers = {d.id: d for d in db.execute(select(Driver).where(Driver.id.in_(ratings.keys()))).scalars()}
    teams = {t.id: t for t in db.execute(select(Team)).scalars()}

    out = []
    for driver_id, rating in ratings.items():
        driver = drivers.get(driver_id)
        if driver is None:
            continue
        team = teams.get(rating["team_id"]) if rating["team_id"] else None
        out.append(
            DriverSummary(
                driver_ref=driver.driver_ref,
                code=driver.fastf1_code,
                given_name=driver.given_name,
                family_name=driver.family_name,
                team_ref=team.constructor_ref if team else None,
                team_name=team.name if team else None,
                points=rating["points"],
                wins=rating["wins"],
                driver_rating=rating["driver_rating"],
                rating_breakdown=rating["rating_breakdown"],
            )
        )
    out.sort(key=lambda d: d.driver_rating, reverse=True)
    return out


@router.get("/{driver_ref}", response_model=DriverDetail)
def get_driver(driver_ref: str, season: int | None = Query(default=None), db: OrmSession = Depends(get_db)):
    driver = db.execute(select(Driver).where(Driver.driver_ref == driver_ref)).scalar_one_or_none()
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")

    season = season or latest_season(db)
    if season is None:
        raise HTTPException(status_code=404, detail="No season data loaded yet")

    ratings = compute_driver_ratings(db, season)
    rating = ratings.get(driver.id)
    if rating is None:
        raise HTTPException(status_code=404, detail=f"No {season} results for this driver")

    team = db.get(Team, rating["team_id"]) if rating["team_id"] else None

    results_stmt = (
        select(
            Race.round,
            Race.name,
            RaceResult.grid_position,
            RaceResult.finish_position,
            RaceResult.status,
            RaceResult.points,
        )
        .join(SessionModel, RaceResult.session_id == SessionModel.id)
        .join(Race, SessionModel.race_id == Race.id)
        .where(Race.season == season, SessionModel.session_type == "R", RaceResult.driver_id == driver.id)
        .order_by(Race.round)
    )
    results = [
        RaceResultRow(round=r, race_name=name, grid_position=grid, finish_position=finish, status=status, points=float(points))
        for r, name, grid, finish, status, points in db.execute(results_stmt).all()
    ]

    return DriverDetail(
        driver_ref=driver.driver_ref,
        code=driver.fastf1_code,
        given_name=driver.given_name,
        family_name=driver.family_name,
        team_ref=team.constructor_ref if team else None,
        team_name=team.name if team else None,
        points=rating["points"],
        wins=rating["wins"],
        driver_rating=rating["driver_rating"],
        rating_breakdown=rating["rating_breakdown"],
        nationality=driver.nationality,
        date_of_birth=driver.date_of_birth.isoformat() if driver.date_of_birth else None,
        headshot_url=driver.headshot_url,
        results=results,
    )


@router.get("/{driver_ref}/points-history", response_model=list[PointsHistoryPoint])
def get_driver_points_history(
    driver_ref: str, season: int | None = Query(default=None), db: OrmSession = Depends(get_db)
):
    driver = db.execute(select(Driver).where(Driver.driver_ref == driver_ref)).scalar_one_or_none()
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")

    season = season or latest_season(db)
    if season is None:
        return []

    stmt = (
        select(DriverStanding.round, DriverStanding.points, DriverStanding.position)
        .where(DriverStanding.season == season, DriverStanding.driver_id == driver.id)
        .order_by(DriverStanding.round)
    )
    return [
        PointsHistoryPoint(round=round_, points=float(points), position=position)
        for round_, points, position in db.execute(stmt).all()
    ]
