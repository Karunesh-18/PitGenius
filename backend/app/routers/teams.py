from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from pitgenius_db.models import Driver, Team

from ..db import get_db
from ..schemas.team import TeamDetail, TeammateComparison, TeamSummary
from ..services.constructor_analytics import compute_team_analytics, compute_teammate_comparison
from ..services.queries import latest_season

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("", response_model=list[TeamSummary])
def list_teams(season: int | None = Query(default=None), db: OrmSession = Depends(get_db)):
    season = season or latest_season(db)
    if season is None:
        return []

    analytics = compute_team_analytics(db, season)
    if not analytics:
        return []

    teams = {t.id: t for t in db.execute(select(Team).where(Team.id.in_(analytics.keys()))).scalars()}

    out = []
    for team_id, stats in analytics.items():
        team = teams.get(team_id)
        if team is None:
            continue
        out.append(
            TeamSummary(
                team_ref=team.constructor_ref,
                name=team.name,
                color_primary=team.color_primary,
                color_secondary=team.color_secondary,
                points=stats["points"],
                wins=stats["wins"],
                reliability_pct=stats["reliability_pct"],
                pit_efficiency_estimate_s=stats["pit_efficiency_estimate_s"],
            )
        )
    out.sort(key=lambda t: t.points, reverse=True)
    return out


@router.get("/{team_ref}", response_model=TeamDetail)
def get_team(team_ref: str, season: int | None = Query(default=None), db: OrmSession = Depends(get_db)):
    team = db.execute(select(Team).where(Team.constructor_ref == team_ref)).scalar_one_or_none()
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    season = season or latest_season(db)
    if season is None:
        raise HTTPException(status_code=404, detail="No season data loaded yet")

    analytics = compute_team_analytics(db, season)
    stats = analytics.get(team.id)
    if stats is None:
        raise HTTPException(status_code=404, detail=f"No {season} results for this team")

    teammate_rows = compute_teammate_comparison(db, season, team.id)
    drivers = {d.id: d for d in db.execute(select(Driver).where(Driver.id.in_([r["driver_id"] for r in teammate_rows]))).scalars()}

    comparisons = []
    for row in teammate_rows:
        driver = drivers.get(row["driver_id"])
        if driver is None:
            continue
        comparisons.append(
            TeammateComparison(
                driver_ref=driver.driver_ref,
                code=driver.fastf1_code,
                given_name=driver.given_name,
                family_name=driver.family_name,
                points=row["points"],
                avg_finish_position=row["avg_finish_position"],
                avg_qualifying_position=row["avg_qualifying_position"],
            )
        )

    return TeamDetail(
        team_ref=team.constructor_ref,
        name=team.name,
        color_primary=team.color_primary,
        color_secondary=team.color_secondary,
        points=stats["points"],
        wins=stats["wins"],
        reliability_pct=stats["reliability_pct"],
        pit_efficiency_estimate_s=stats["pit_efficiency_estimate_s"],
        drivers=comparisons,
    )
