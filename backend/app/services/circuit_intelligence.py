"""Circuit Intelligence: overtaking difficulty, safety-car likelihood, and
average pit-lane loss per circuit, derived from lap_times.

Overtaking index counts lap-to-lap position changes (excluding a driver's
own pit laps and the lap immediately after one, since pit-cycle position
swaps aren't on-track overtakes), summed per circuit and min-max scaled
0-100 across every circuit raced this season — the identical scaling
technique as driver_rating.py's _min_max_scale, duplicated here rather
than imported since the two services otherwise have no coupling.

Safety car probability reuses the same green-flag track_status
substring-containment convention as tire_degradation.py. Avg pit loss is
constructor_analytics.py's _pit_efficiency_by_team logic, generalized to
group by circuit_ref instead of team_id.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session as OrmSession

from .queries import lap_times_with_context_df

# Possibly-concatenated FastF1 track-status digit codes meaning a lap ran
# under Safety Car / Red Flag / VSC / VSC-ending conditions.
NON_GREEN_STATUS_CODES = ("4", "5", "6", "7")


def _min_max_scale(series: pd.Series) -> pd.Series:
    """Scale to 0-100. Same technique as driver_rating.py's helper."""
    lo, hi = series.min(), series.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(50.0, index=series.index)
    return (series - lo) / (hi - lo) * 100


def _has_non_green_lap(track_status: str | None) -> bool:
    if not track_status:
        return False
    return any(code in track_status for code in NON_GREEN_STATUS_CODES)


def _overtaking_index_by_circuit(df: pd.DataFrame) -> pd.Series:
    pos_df = df.dropna(subset=["position"]).sort_values(["race_id", "driver_id", "lap_number"]).copy()
    if pos_df.empty:
        return pd.Series(dtype=float)

    grouped = pos_df.groupby(["race_id", "driver_id"], group_keys=False)
    pos_df["prev_position"] = grouped["position"].shift(1)
    pos_df["prev_is_pit_lap"] = grouped["is_pit_lap"].shift(1)

    # Laps where a position change *could* have been observed on track.
    comparable = (
        pos_df["prev_position"].notna()
        & ~pos_df["is_pit_lap"].astype(bool)
        & ~pos_df["prev_is_pit_lap"].fillna(False).astype(bool)
    )
    changed = comparable & (pos_df["position"] != pos_df["prev_position"])

    # A rate, not a raw count: a raw count makes short races (Monaco, 78 laps of
    # 3.3km) look static purely for being short, and would double for any circuit
    # once a second season is ingested, degenerating the min-max scale into "how
    # many times has this circuit been loaded".
    opportunities = pos_df[comparable].groupby("circuit_ref").size()
    changes = pos_df[changed].groupby("circuit_ref").size()
    all_circuits = df["circuit_ref"].unique()
    opportunities = opportunities.reindex(all_circuits, fill_value=0)
    changes = changes.reindex(all_circuits, fill_value=0)
    return (changes / opportunities.where(opportunities > 0)).fillna(0.0)


def _safety_car_probability_by_circuit(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Returns (probability_pct_by_circuit, total_races_by_circuit)."""
    total_races = df.groupby("circuit_ref")["race_id"].nunique()
    flagged = df.assign(non_green=df["track_status"].apply(_has_non_green_lap))
    races_with_sc = flagged[flagged["non_green"]].groupby("circuit_ref")["race_id"].nunique()
    races_with_sc = races_with_sc.reindex(total_races.index, fill_value=0)
    probability_pct = (races_with_sc / total_races * 100).round(1)
    return probability_pct, total_races


def _avg_pit_loss_by_circuit(df: pd.DataFrame) -> dict[str, float]:
    laps_df = df.dropna(subset=["lap_time_ms"]).copy()
    laps_df["is_pit_lap"] = laps_df["is_pit_lap"].astype(bool)
    # Safety-car and red-flag laps distort this from both directions: they slow
    # the "normal" median (making a stop look cheap) and they inflate in-laps
    # taken during a stoppage (making one look enormous). Compare green-flag
    # running only.
    laps_df = laps_df[~laps_df["track_status"].apply(_has_non_green_lap)]
    if laps_df.empty:
        return {}

    # "Normal" pace must be per driver *per race*, not per driver across the
    # season: circuit lap times span ~70s (Red Bull Ring) to ~113s (Spa), so a
    # season-wide median turns this into a measure of how long the lap is rather
    # than how much time the pit stop costs.
    normal = laps_df[~laps_df["is_pit_lap"]].groupby(["driver_id", "race_id"])["lap_time_ms"].median()
    pit_laps = laps_df[laps_df["is_pit_lap"]].copy()
    pit_laps["normal_ms"] = pit_laps.set_index(["driver_id", "race_id"]).index.map(normal)
    pit_laps = pit_laps.dropna(subset=["normal_ms"])
    pit_laps["loss_ms"] = pit_laps["lap_time_ms"] - pit_laps["normal_ms"]

    # Median, not mean — one in-lap under a safety car or red flag otherwise
    # drags the circuit's figure well off the typical stop.
    by_circuit = pit_laps.groupby("circuit_ref")["loss_ms"].median() / 1000
    return {circuit_ref: round(float(val), 2) for circuit_ref, val in by_circuit.items() if pd.notna(val)}


def compute_circuit_intelligence(db: OrmSession, season: int, circuit_ref: str) -> dict:
    df = lap_times_with_context_df(db, season)
    if df.empty or circuit_ref not in set(df["circuit_ref"].unique()):
        return {
            "overtaking_index": 50.0,
            "safety_car_probability_pct": 0.0,
            "avg_pit_loss_s": None,
            "races_analyzed": 0,
        }

    overtaking_scaled = _min_max_scale(_overtaking_index_by_circuit(df))
    sc_probability_pct, total_races = _safety_car_probability_by_circuit(df)
    pit_loss_by_circuit = _avg_pit_loss_by_circuit(df)

    return {
        "overtaking_index": round(float(overtaking_scaled.get(circuit_ref, 50.0)), 1),
        "safety_car_probability_pct": float(sc_probability_pct.get(circuit_ref, 0.0)),
        "avg_pit_loss_s": pit_loss_by_circuit.get(circuit_ref),
        "races_analyzed": int(total_races.get(circuit_ref, 0)),
    }
