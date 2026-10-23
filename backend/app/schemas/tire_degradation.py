from typing import Literal

from pydantic import BaseModel, Field


class TireDegradationRequest(BaseModel):
    circuit_ref: str
    compound: Literal["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
    tyre_life: int = Field(ge=1, le=60)


class ShapContribution(BaseModel):
    feature: str
    value: str
    shap_value_s: float


class TireDegradationResponse(BaseModel):
    predicted_lap_time_s: float
    baseline_lap_time_s: float  # same compound, tyre_life=1 (fresh)
    degradation_vs_fresh_s: float
    shap_contributions: list[ShapContribution]
    explanation: str
