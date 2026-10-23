"""Read queries backing the Telemetry Viewer feature (GET /api/races/.../telemetry*)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from pitgenius_db.models import Driver, LapTime, Race, Telemetry
from pitgenius_db.models import Session as SessionModel


def list_telemetry_drivers(db: OrmSession, season: int, round_: int) -> list[dict]:
    """Distinct (driver_ref, code, lap_number, lap_time_ms) for every
    driver with telemetry rows in this race's R session."""
    stmt = (
        select(Driver.driver_ref, Driver.fastf1_code, Telemetry.lap_number, LapTime.lap_time_ms)
        .join(SessionModel, Telemetry.session_id == SessionModel.id)
        .join(Race, SessionModel.race_id == Race.id)
        .join(Driver, Telemetry.driver_id == Driver.id)
        .outerjoin(
            LapTime,
            (LapTime.session_id == Telemetry.session_id)
            & (LapTime.driver_id == Telemetry.driver_id)
            & (LapTime.lap_number == Telemetry.lap_number),
        )
        .where(Race.season == season, Race.round == round_, SessionModel.session_type == "R")
        .distinct()
        .order_by(Driver.driver_ref)
    )
    rows = db.execute(stmt).all()
    return [
        {"driver_ref": dref, "code": code, "lap_number": lap_number, "lap_time_ms": lap_time_ms}
        for dref, code, lap_number, lap_time_ms in rows
    ]


def get_driver_telemetry(db: OrmSession, season: int, round_: int, driver_ref: str) -> dict | None:
    driver_row = db.execute(
        select(Driver.id, Driver.driver_ref, Driver.fastf1_code).where(Driver.driver_ref == driver_ref)
    ).first()
    if driver_row is None:
        return None
    driver_id, driver_ref_out, code = driver_row

    session_row = db.execute(
        select(SessionModel.id)
        .join(Race, SessionModel.race_id == Race.id)
        .where(Race.season == season, Race.round == round_, SessionModel.session_type == "R")
    ).first()
    if session_row is None:
        return None
    session_id = session_row[0]

    points_stmt = (
        select(
            Telemetry.lap_number,
            Telemetry.point_index,
            Telemetry.distance_m,
            Telemetry.time_ms,
            Telemetry.speed_kph,
            Telemetry.throttle_pct,
            Telemetry.brake,
            Telemetry.gear,
            Telemetry.drs,
            Telemetry.x,
            Telemetry.y,
            Telemetry.z,
        )
        .where(Telemetry.session_id == session_id, Telemetry.driver_id == driver_id)
        .order_by(Telemetry.point_index)
    )
    rows = db.execute(points_stmt).all()
    if not rows:
        return None

    lap_number = rows[0][0]
    points = [
        {
            "point_index": point_index,
            "distance_m": float(distance_m),
            "time_ms": int(time_ms),
            "speed_kph": float(speed_kph) if speed_kph is not None else None,
            "throttle_pct": int(throttle_pct) if throttle_pct is not None else None,
            "brake": brake,
            "gear": int(gear) if gear is not None else None,
            "drs": int(drs) if drs is not None else None,
            "x": float(x),
            "y": float(y),
            "z": float(z),
        }
        for _lap, point_index, distance_m, time_ms, speed_kph, throttle_pct, brake, gear, drs, x, y, z in rows
    ]

    lap_time_row = db.execute(
        select(LapTime.lap_time_ms).where(
            LapTime.session_id == session_id, LapTime.driver_id == driver_id, LapTime.lap_number == lap_number
        )
    ).first()
    lap_time_ms = lap_time_row[0] if lap_time_row else None

    return {
        "season": season,
        "round": round_,
        "driver_ref": driver_ref_out,
        "code": code,
        "lap_number": lap_number,
        "lap_time_ms": lap_time_ms,
        "points": points,
    }
