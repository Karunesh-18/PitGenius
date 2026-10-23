"""Build a circuit's static 3D track outline from fastest-lap telemetry.

Normalization happens here (server-side, once, at ETL time) rather than
in the frontend, so every circuit renders at a consistent scale in the
3D viewer with no per-circuit client-side guesswork.
"""
from __future__ import annotations

import pandas as pd

TARGET_POINT_COUNT = 400


def build_track_outline(
    telemetry: pd.DataFrame,
) -> tuple[list[dict[str, float]], float | None, float | None, float | None, float | None]:
    """telemetry must have X, Y, Z columns (FastF1 car position, in FastF1's
    native units). Returns (points, center_x, center_y, center_z, scale):
    a downsampled, centered, unit-scaled point list ready to store in
    circuits.track_outline, plus the four normalization scalars used to
    build it so callers can persist them on the Circuit row — per-driver
    telemetry (Phase 2) reuses these same scalars so it lands in the exact
    same coordinate frame as this ribbon.
    """
    df = telemetry.dropna(subset=["X", "Y", "Z"]).reset_index(drop=True)
    if df.empty:
        return [], None, None, None, None

    if len(df) > TARGET_POINT_COUNT:
        step = len(df) / TARGET_POINT_COUNT
        indices = [int(i * step) for i in range(TARGET_POINT_COUNT)]
        df = df.iloc[indices].reset_index(drop=True)

    center_x = (df["X"].max() + df["X"].min()) / 2
    center_y = (df["Y"].max() + df["Y"].min()) / 2
    center_z = df["Z"].min()  # sit the track on the ground plane (z=0 at its lowest point)

    span = max(df["X"].max() - df["X"].min(), df["Y"].max() - df["Y"].min())
    scale = 100.0 / span if span else 1.0

    points = [
        {
            "x": round((row.X - center_x) * scale, 3),
            "y": round((row.Y - center_y) * scale, 3),
            "z": round((row.Z - center_z) * scale, 3),
        }
        for row in df.itertuples()
    ]
    return points, float(center_x), float(center_y), float(center_z), float(scale)
