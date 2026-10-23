"""Thin wrapper around FastF1 session loading.

Assumes enable_fastf1_cache() has already been called at process startup
(see pitgenius_etl.cache) — every call here hits the local cache after
the first run for a given session.
"""
from __future__ import annotations

import fastf1
import pandas as pd

# FastF1 session identifiers -> our internal session_type column values.
FASTF1_TO_SESSION_TYPE = {
    "FP1": "FP1",
    "FP2": "FP2",
    "FP3": "FP3",
    "Q": "Q",
    "SQ": "SQ",
    "S": "S",
    "R": "R",
}


def load_session(season: int, round_: int, session_type: str) -> fastf1.core.Session:
    session = fastf1.get_session(season, round_, session_type)
    session.load(laps=True, telemetry=False, weather=False, messages=False)
    return session


def load_session_with_telemetry(season: int, round_: int, session_type: str) -> fastf1.core.Session:
    """Like load_session, but with telemetry=True. Deliberately kept
    separate from load_session (which the fast standard run_round path
    uses) since telemetry loading is much slower and only the dedicated
    telemetry ETL step needs it.
    """
    session = fastf1.get_session(season, round_, session_type)
    session.load(laps=True, telemetry=True, weather=False, messages=False)
    return session


def get_driver_fastest_lap_telemetry(
    session: fastf1.core.Session, fastf1_code: str
) -> tuple[int, int, pd.DataFrame] | None:
    """Returns (lap_number, lap_time_ms, telemetry_df) for one driver's
    fastest lap in this already-loaded (telemetry=True) session.
    telemetry_df has Distance, Time, Speed, Throttle, Brake, nGear, DRS,
    X, Y, Z columns (whichever of these FastF1 provides). None if the
    driver has no valid fastest lap or no telemetry for it.
    """
    driver_laps = session.laps.pick_drivers(fastf1_code)
    if driver_laps is None or driver_laps.empty:
        return None
    fastest = driver_laps.pick_fastest()
    if fastest is None or pd.isna(fastest.get("LapTime")) or pd.isna(fastest.get("LapNumber")):
        return None
    telemetry = fastest.get_telemetry()
    if telemetry is None or telemetry.empty:
        return None

    lap_number = int(fastest["LapNumber"])
    lap_time_ms = round(fastest["LapTime"].total_seconds() * 1000)
    cols = [
        c
        for c in ["Distance", "Time", "Speed", "Throttle", "Brake", "nGear", "DRS", "X", "Y", "Z"]
        if c in telemetry.columns
    ]
    return lap_number, lap_time_ms, telemetry[cols]


def get_laps(session: fastf1.core.Session) -> pd.DataFrame:
    return session.laps


def get_fastest_lap_telemetry(season: int, round_: int) -> pd.DataFrame | None:
    """Fastest lap of the race session, used to derive a circuit's 3D
    track outline. Returns None if the race session has no clean lap
    (e.g. wet/red-flagged race with no representative fastest lap).
    """
    session = fastf1.get_session(season, round_, "R")
    session.load(laps=True, telemetry=True, weather=False, messages=False)
    laps = session.laps
    if laps.empty:
        return None
    fastest = laps.pick_fastest()
    if fastest is None or pd.isna(fastest.get("LapTime")):
        return None
    telemetry = fastest.get_telemetry()
    if telemetry is None or telemetry.empty:
        return None
    return telemetry[["X", "Y", "Z"]]
