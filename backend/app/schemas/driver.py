from pydantic import BaseModel


class RatingBreakdown(BaseModel):
    qualifying_pace: float
    race_pace: float
    consistency: float
    finishes: float


class DriverSummary(BaseModel):
    driver_ref: str
    code: str | None
    given_name: str
    family_name: str
    team_ref: str | None
    team_name: str | None
    points: float
    wins: int
    driver_rating: float
    rating_breakdown: RatingBreakdown


class RaceResultRow(BaseModel):
    round: int
    race_name: str
    grid_position: int | None
    finish_position: int | None
    status: str
    points: float


class DriverDetail(DriverSummary):
    nationality: str | None
    date_of_birth: str | None
    headshot_url: str | None
    results: list[RaceResultRow]


class PointsHistoryPoint(BaseModel):
    round: int
    points: float
    position: int
