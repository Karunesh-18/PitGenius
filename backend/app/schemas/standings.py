from pydantic import BaseModel


class DriverStandingRow(BaseModel):
    position: int
    driver_ref: str
    code: str | None
    given_name: str
    family_name: str
    team_ref: str | None
    points: float
    wins: int


class ConstructorStandingRow(BaseModel):
    position: int
    team_ref: str
    name: str
    points: float
    wins: int
