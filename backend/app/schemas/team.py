from pydantic import BaseModel


class TeammateComparison(BaseModel):
    driver_ref: str
    code: str | None
    given_name: str
    family_name: str
    points: float
    avg_finish_position: float | None
    avg_qualifying_position: float | None


class TeamSummary(BaseModel):
    team_ref: str
    name: str
    color_primary: str | None
    color_secondary: str | None
    points: float
    wins: int
    reliability_pct: float | None
    pit_efficiency_estimate_s: float | None


class TeamDetail(TeamSummary):
    drivers: list[TeammateComparison]
