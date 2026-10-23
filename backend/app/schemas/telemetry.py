from pydantic import BaseModel


class TelemetryAvailabilityRow(BaseModel):
    driver_ref: str
    code: str | None
    lap_number: int
    lap_time_ms: int | None


class TelemetryPoint(BaseModel):
    point_index: int
    distance_m: float
    time_ms: int
    speed_kph: float | None
    throttle_pct: int | None
    brake: bool | None
    gear: int | None
    drs: int | None
    x: float
    y: float
    z: float


class TelemetryOut(BaseModel):
    season: int
    round: int
    driver_ref: str
    code: str | None
    lap_number: int
    lap_time_ms: int | None
    points: list[TelemetryPoint]
