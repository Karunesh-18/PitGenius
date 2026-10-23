import datetime as dt

from pydantic import BaseModel


class RaceSummary(BaseModel):
    season: int
    round: int
    name: str
    circuit_ref: str
    race_date: dt.date
    status: str  # "upcoming" | "completed"
    country: str | None = None
    winner_driver_ref: str | None = None
    winner_code: str | None = None
    winner_team_ref: str | None = None


class QualifyingResultRow(BaseModel):
    position: int | None
    driver_ref: str
    code: str | None
    team_ref: str
    q1_ms: int | None
    q2_ms: int | None
    q3_ms: int | None


class RaceResultRow(BaseModel):
    finish_position: int | None
    grid_position: int | None
    driver_ref: str
    code: str | None
    team_ref: str
    status: str
    points: float
    fastest_lap_rank: int | None = None
    final_compound: str | None = None  # compound of the driver's last completed race lap


class RaceDetail(RaceSummary):
    qualifying_results: list[QualifyingResultRow]
    race_results: list[RaceResultRow]
