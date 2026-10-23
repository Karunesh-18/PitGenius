"""Normalize a FastF1 laps DataFrame into lap_times rows.

FastF1's laps DataFrame identifies drivers by their 3-letter code
(e.g. 'VER'), not Jolpica's driver_ref, so the caller must supply a
code -> driver_id mapping (built from drivers.fastf1_code).
"""
from __future__ import annotations

from typing import Any

import pandas as pd


def _timedelta_to_ms(value) -> int | None:
    if value is None or pd.isna(value):
        return None
    return round(value.total_seconds() * 1000)


def normalize_laps(
    laps_df: pd.DataFrame,
    session_id: int,
    code_to_driver_id: dict[str, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, lap in laps_df.iterrows():
        driver_id = code_to_driver_id.get(lap.get("Driver"))
        if driver_id is None or pd.isna(lap.get("LapNumber")):
            continue
        pit_in_ms = _timedelta_to_ms(lap.get("PitInTime"))
        pit_out_ms = _timedelta_to_ms(lap.get("PitOutTime"))
        rows.append(
            {
                "session_id": session_id,
                "driver_id": driver_id,
                "lap_number": int(lap["LapNumber"]),
                "lap_time_ms": _timedelta_to_ms(lap.get("LapTime")),
                "sector1_ms": _timedelta_to_ms(lap.get("Sector1Time")),
                "sector2_ms": _timedelta_to_ms(lap.get("Sector2Time")),
                "sector3_ms": _timedelta_to_ms(lap.get("Sector3Time")),
                "position": int(lap["Position"]) if pd.notna(lap.get("Position")) else None,
                "compound": lap.get("Compound") if pd.notna(lap.get("Compound")) else None,
                "tyre_life": int(lap["TyreLife"]) if pd.notna(lap.get("TyreLife")) else None,
                "is_pit_lap": pit_in_ms is not None or pit_out_ms is not None,
                "pit_in_time_ms": pit_in_ms,
                "pit_out_time_ms": pit_out_ms,
                "track_status": str(lap["TrackStatus"]) if pd.notna(lap.get("TrackStatus")) else None,
            }
        )
    return rows
