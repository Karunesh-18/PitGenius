"""Build per-driver, per-lap telemetry rows from FastF1 telemetry.

FastF1 telemetry is not uniformly time-sampled (sample rate varies), so
we resample evenly along cumulative Distance rather than Time/row-index —
matching the point-count convention in normalize/track_outline.py but
with a distance-based resampling method instead of a row-index stride,
since track_outline.py's telemetry (a fastest-lap sample) is treated as
already roughly evenly spaced by distance while a driver-lap trace here
is explicitly resampled onto a uniform distance grid.

X/Y/Z are normalized with the SAME center/scale scalars already computed
and persisted for the circuit's track_outline (see track_outline.py), so
a driver's telemetry marker lands in the same coordinate frame as the
static 3D ribbon.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

TELEMETRY_POINTS_PER_LAP = 400  # matches track_outline.py's TARGET_POINT_COUNT pattern


def build_driver_lap_telemetry(
    telemetry_df: pd.DataFrame,
    session_id: int,
    driver_id: int,
    lap_number: int,
    norm_params: tuple[float, float, float, float],
) -> list[dict[str, Any]]:
    """norm_params = (center_x, center_y, center_z, scale) from the circuit row.

    Drops NaN X/Y/Z rows, resamples to TELEMETRY_POINTS_PER_LAP points
    evenly-spaced by cumulative Distance (nearest-sample, not interpolated,
    so categorical columns like gear/DRS/brake stay real observed values),
    and applies norm_params to X/Y/Z identically to how track_outline.py
    applies its own. Emits dicts matching the Telemetry model's columns
    (minus session_id/driver_id/lap_number, which are passed straight
    through since the caller already knows them).
    """
    center_x, center_y, center_z, scale = norm_params

    required = ["X", "Y", "Z"]
    df = telemetry_df.dropna(subset=required).reset_index(drop=True)
    if df.empty:
        return []

    if "Distance" not in df.columns or df["Distance"].isna().all():
        # Writing row indices into a metres column would be silent unit
        # corruption; a lap without a usable distance channel is simply skipped.
        return []
    df = df.dropna(subset=["Distance"]).sort_values("Distance").reset_index(drop=True)
    df = df.drop_duplicates(subset=["Distance"], keep="first").reset_index(drop=True)
    if len(df) < 2:
        return []

    distances = df["Distance"].to_numpy(dtype=float)
    dist_min, dist_max = float(distances[0]), float(distances[-1])
    if dist_max <= dist_min:
        return []

    target_distances = np.linspace(dist_min, dist_max, TELEMETRY_POINTS_PER_LAP)

    # Nearest-sample resampling: for each target distance, pick the closer
    # of the two bracketing rows rather than interpolating, so gear/DRS/
    # brake reflect an actually-observed sample rather than a blended value.
    right_idx = np.clip(np.searchsorted(distances, target_distances), 0, len(distances) - 1)
    left_idx = np.clip(right_idx - 1, 0, len(distances) - 1)
    use_left = np.abs(distances[left_idx] - target_distances) < np.abs(distances[right_idx] - target_distances)
    nearest_idx = np.where(use_left, left_idx, right_idx)

    sampled = df.iloc[nearest_idx].reset_index(drop=True)

    # time_ms drives playback and is NOT NULL, so there's no way to represent
    # "unknown" — a lap without a usable Time channel would otherwise be stored
    # with every point at t=0 and stall the animation. Skip it instead.
    if "Time" not in sampled.columns or pd.isna(sampled["Time"].iloc[0]):
        return []
    t0 = sampled["Time"].iloc[0]

    rows: list[dict[str, Any]] = []
    for point_index, (_, row) in enumerate(sampled.iterrows()):
        time_ms = 0
        row_time = row.get("Time")
        if pd.notna(row_time):
            time_ms = round((row_time - t0).total_seconds() * 1000)

        speed = row.get("Speed")
        throttle = row.get("Throttle")
        brake = row.get("Brake")
        gear = row.get("nGear")
        drs = row.get("DRS")

        rows.append(
            {
                "session_id": session_id,
                "driver_id": driver_id,
                "lap_number": lap_number,
                "point_index": point_index,
                "distance_m": round(float(row["Distance"]), 2),
                "time_ms": int(time_ms),
                "speed_kph": float(speed) if pd.notna(speed) else None,
                # FastF1's raw throttle trace can read slightly over 100; clamp
                # so a column named _pct actually holds a percentage.
                "throttle_pct": min(100, max(0, round(float(throttle)))) if pd.notna(throttle) else None,
                "brake": bool(brake) if pd.notna(brake) else None,
                "gear": int(gear) if pd.notna(gear) else None,
                "drs": int(drs) if pd.notna(drs) else None,
                "x": round((float(row["X"]) - center_x) * scale, 3),
                "y": round((float(row["Y"]) - center_y) * scale, 3),
                "z": round((float(row["Z"]) - center_z) * scale, 3),
            }
        )
    return rows
