"""Constructor Analytics: reliability and points from race_results,
plus an approximate pit-stop efficiency figure.

Pit efficiency is estimated from lap_times.is_pit_lap (extra time on the
in/out lap vs. that driver's normal race pace) rather than a dedicated
pit_stops table, which is a Phase 2 addition — see docs/phase1-plan.md.
This is flagged as an estimate, not measured pit-lane time.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session as OrmSession

from .queries import lap_times_df, qualifying_results_df, race_results_df


def compute_team_analytics(db: OrmSession, season: int) -> dict[int, dict]:
    """Returns {team_id: {points, wins, reliability_pct, pit_efficiency_estimate_s}}."""
    race_df = race_results_df(db, season)
    if race_df.empty:
        return {}

    agg = race_df.groupby("team_id").agg(points=("points", "sum"), wins=("finish_position", lambda s: int((s == 1).sum())))
    entered = race_df.groupby("team_id")["status"].count()
    classified = race_df.dropna(subset=["finish_position"]).groupby("team_id")["finish_position"].count()
    agg["reliability_pct"] = (classified / entered * 100).round(1)

    laps_df = lap_times_df(db, season)
    pit_efficiency = _pit_efficiency_by_team(db, season, laps_df, race_df)

    result: dict[int, dict] = {}
    for team_id, row in agg.iterrows():
        result[int(team_id)] = {
            "points": float(row["points"]),
            "wins": int(row["wins"]),
            "reliability_pct": float(row["reliability_pct"]) if pd.notna(row["reliability_pct"]) else None,
            "pit_efficiency_estimate_s": pit_efficiency.get(int(team_id)),
        }
    return result


def _pit_efficiency_by_team(
    db: OrmSession, season: int, laps_df: pd.DataFrame, race_df: pd.DataFrame
) -> dict[int, float]:
    if laps_df.empty:
        return {}
    driver_to_team = race_df.drop_duplicates("driver_id").set_index("driver_id")["team_id"]
    laps_df = laps_df.dropna(subset=["lap_time_ms"]).copy()
    laps_df["team_id"] = laps_df["driver_id"].map(driver_to_team)
    laps_df = laps_df.dropna(subset=["team_id"])

    normal = laps_df[~laps_df["is_pit_lap"]].groupby("driver_id")["lap_time_ms"].median()
    pit_laps = laps_df[laps_df["is_pit_lap"]].copy()
    pit_laps["normal_ms"] = pit_laps["driver_id"].map(normal)
    pit_laps = pit_laps.dropna(subset=["normal_ms"])
    pit_laps["loss_ms"] = pit_laps["lap_time_ms"] - pit_laps["normal_ms"]

    by_team = pit_laps.groupby("team_id")["loss_ms"].mean() / 1000
    return {int(team_id): round(float(val), 2) for team_id, val in by_team.items() if pd.notna(val)}


def compute_teammate_comparison(db: OrmSession, season: int, team_id: int) -> list[dict]:
    race_df = race_results_df(db, season)
    quali_df = qualifying_results_df(db, season)
    team_drivers = race_df[race_df["team_id"] == team_id]
    if team_drivers.empty:
        return []

    points = team_drivers.groupby("driver_id")["points"].sum()
    classified = team_drivers.dropna(subset=["finish_position"])
    avg_finish = classified.groupby("driver_id")["finish_position"].mean()
    avg_quali = quali_df.dropna(subset=["position"]).groupby("driver_id")["position"].mean()

    rows = []
    for driver_id in team_drivers["driver_id"].unique():
        rows.append(
            {
                "driver_id": int(driver_id),
                "points": float(points.get(driver_id, 0.0)),
                "avg_finish_position": round(float(avg_finish[driver_id]), 2) if driver_id in avg_finish else None,
                "avg_qualifying_position": round(float(avg_quali[driver_id]), 2) if driver_id in avg_quali else None,
            }
        )
    return rows
