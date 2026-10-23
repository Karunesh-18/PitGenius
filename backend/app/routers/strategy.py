from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from pitgenius_db.models import Circuit

from ..db import get_db
from ..schemas.strategy import StrategySimulateRequest, StrategySimulateResponse
from ..services.strategy_simulator import simulate

router = APIRouter(prefix="/api/strategy", tags=["strategy"])


@router.post("/simulate", response_model=StrategySimulateResponse)
def simulate_strategy(req: StrategySimulateRequest, db: OrmSession = Depends(get_db)):
    circuit = db.execute(select(Circuit).where(Circuit.circuit_ref == req.circuit_ref)).scalar_one_or_none()
    if circuit is None:
        raise HTTPException(status_code=404, detail="Circuit not found")
    if req.pit_lap >= req.num_laps:
        raise HTTPException(status_code=422, detail="pit_lap must be less than num_laps")

    result = simulate(
        db,
        circuit_ref=req.circuit_ref,
        starting_position=req.starting_position,
        tire_compound=req.tire_compound,
        pit_lap=req.pit_lap,
        num_laps=req.num_laps,
    )
    return StrategySimulateResponse(**result)
