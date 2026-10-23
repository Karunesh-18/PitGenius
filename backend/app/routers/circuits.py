from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from pitgenius_db.models import Circuit, Race

from ..db import get_db
from ..schemas.circuit import CircuitIntelligenceOut, CircuitOut, CircuitSummary, TrackOutlineOut
from ..services.circuit_intelligence import compute_circuit_intelligence
from ..services.queries import latest_season

router = APIRouter(prefix="/api/circuits", tags=["circuits"])


@router.get("", response_model=list[CircuitSummary])
def list_circuits(season: int | None = Query(default=None), db: OrmSession = Depends(get_db)):
    season = season or latest_season(db)
    if season is None:
        return []

    stmt = (
        select(Circuit.circuit_ref, Circuit.name, Circuit.country, Circuit.length_km)
        .join(Race, Race.circuit_id == Circuit.id)
        .where(Race.season == season)
        .distinct()
        .order_by(Circuit.name)
    )
    return [
        CircuitSummary(
            circuit_ref=circuit_ref,
            name=name,
            country=country,
            length_km=float(length_km) if length_km is not None else None,
        )
        for circuit_ref, name, country, length_km in db.execute(stmt).all()
    ]


@router.get("/{circuit_ref}", response_model=CircuitOut)
def get_circuit(circuit_ref: str, db: OrmSession = Depends(get_db)):
    circuit = db.execute(select(Circuit).where(Circuit.circuit_ref == circuit_ref)).scalar_one_or_none()
    if circuit is None:
        raise HTTPException(status_code=404, detail="Circuit not found")
    return CircuitOut(
        circuit_ref=circuit.circuit_ref,
        name=circuit.name,
        country=circuit.country,
        length_km=float(circuit.length_km) if circuit.length_km is not None else None,
    )


@router.get("/{circuit_ref}/track-outline", response_model=TrackOutlineOut)
def get_track_outline(circuit_ref: str, db: OrmSession = Depends(get_db)):
    circuit = db.execute(select(Circuit).where(Circuit.circuit_ref == circuit_ref)).scalar_one_or_none()
    if circuit is None:
        raise HTTPException(status_code=404, detail="Circuit not found")
    if not circuit.track_outline:
        raise HTTPException(status_code=404, detail="Track outline not generated yet for this circuit")
    return TrackOutlineOut(circuit_ref=circuit.circuit_ref, points=circuit.track_outline)


@router.get("/{circuit_ref}/intelligence", response_model=CircuitIntelligenceOut)
def get_circuit_intelligence(
    circuit_ref: str, season: int | None = Query(default=None), db: OrmSession = Depends(get_db)
):
    circuit = db.execute(select(Circuit).where(Circuit.circuit_ref == circuit_ref)).scalar_one_or_none()
    if circuit is None:
        raise HTTPException(status_code=404, detail="Circuit not found")

    season = season or latest_season(db)
    if season is None:
        raise HTTPException(status_code=404, detail="No season data loaded yet")

    result = compute_circuit_intelligence(db, season, circuit_ref)
    return CircuitIntelligenceOut(circuit_ref=circuit_ref, season=season, **result)
