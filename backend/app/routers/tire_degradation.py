from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as OrmSession

from ..db import get_db
from ..schemas.tire_degradation import TireDegradationRequest, TireDegradationResponse
from ..services.tire_degradation import predict

router = APIRouter(prefix="/api/tire-degradation", tags=["tire-degradation"])


@router.post("/predict", response_model=TireDegradationResponse)
def predict_tire_degradation(req: TireDegradationRequest, db: OrmSession = Depends(get_db)):
    try:
        result = predict(db, circuit_ref=req.circuit_ref, compound=req.compound, tyre_life=req.tyre_life)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TireDegradationResponse(**result)
