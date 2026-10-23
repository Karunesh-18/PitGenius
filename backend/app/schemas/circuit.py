from pydantic import BaseModel


class CircuitOut(BaseModel):
    circuit_ref: str
    name: str
    country: str | None
    length_km: float | None


class TrackOutlinePoint(BaseModel):
    x: float
    y: float
    z: float


class TrackOutlineOut(BaseModel):
    circuit_ref: str
    points: list[TrackOutlinePoint]


class CircuitSummary(BaseModel):
    circuit_ref: str
    name: str
    country: str | None
    length_km: float | None


class CircuitIntelligenceOut(BaseModel):
    circuit_ref: str
    season: int
    overtaking_index: float  # 0-100, estimate — see services/circuit_intelligence.py
    safety_car_probability_pct: float
    avg_pit_loss_s: float | None
    races_analyzed: int
