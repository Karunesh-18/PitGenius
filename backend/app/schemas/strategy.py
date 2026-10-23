from pydantic import BaseModel, Field

VALID_COMPOUNDS = ("SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET")


class StrategySimulateRequest(BaseModel):
    circuit_ref: str
    starting_position: int = Field(ge=1, le=20)
    tire_compound: str = Field(pattern="^(SOFT|MEDIUM|HARD|INTERMEDIATE|WET)$")
    pit_lap: int = Field(ge=1)
    num_laps: int = Field(ge=5, le=90)


class LapTimePoint(BaseModel):
    lap: int
    lap_time_s: float


class StrategySimulateResponse(BaseModel):
    predicted_finish_position: int
    total_time_estimate_s: float
    pit_loss_s: float
    optimal_pit_lap: int
    lap_time_curve: list[LapTimePoint]
    explanation: str
