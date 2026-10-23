"""Normalize Jolpica qualifying/race results and standings."""
from __future__ import annotations

from typing import Any


def parse_time_to_ms(time_str: str | None) -> int | None:
    """Parse Ergast-style '1:23.456' or '23.456' into milliseconds."""
    if not time_str:
        return None
    parts = time_str.split(":")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return round(seconds * 1000)


def normalize_qualifying_results(
    race: dict[str, Any],
    driver_ref_to_id: dict[str, int],
    team_ref_to_id: dict[str, int],
) -> list[dict[str, Any]]:
    rows = []
    for entry in race.get("QualifyingResults", []):
        driver_id = driver_ref_to_id.get(entry["Driver"]["driverId"])
        team_id = team_ref_to_id.get(entry["Constructor"]["constructorId"])
        if driver_id is None or team_id is None:
            continue
        rows.append(
            {
                "driver_id": driver_id,
                "team_id": team_id,
                "position": int(entry["position"]) if entry.get("position") else None,
                "q1_ms": parse_time_to_ms(entry.get("Q1")),
                "q2_ms": parse_time_to_ms(entry.get("Q2")),
                "q3_ms": parse_time_to_ms(entry.get("Q3")),
            }
        )
    return rows


def normalize_race_results(
    race: dict[str, Any],
    driver_ref_to_id: dict[str, int],
    team_ref_to_id: dict[str, int],
) -> list[dict[str, Any]]:
    rows = []
    for entry in race.get("Results", []):
        driver_id = driver_ref_to_id.get(entry["Driver"]["driverId"])
        team_id = team_ref_to_id.get(entry["Constructor"]["constructorId"])
        if driver_id is None or team_id is None:
            continue
        time_info = entry.get("Time") or {}
        fastest_lap = entry.get("FastestLap") or {}
        rows.append(
            {
                "driver_id": driver_id,
                "team_id": team_id,
                "grid_position": int(entry["grid"]) if entry.get("grid") else None,
                "finish_position": int(entry["position"]) if entry.get("positionText", "").isdigit() else None,
                "status": entry["status"],
                "points": float(entry.get("points", 0)),
                "laps_completed": int(entry["laps"]) if entry.get("laps") else None,
                "total_time_ms": int(time_info["millis"]) if time_info.get("millis") else None,
                "fastest_lap_rank": int(fastest_lap["rank"]) if fastest_lap.get("rank") else None,
            }
        )
    return rows


def normalize_driver_standing(
    entry: dict[str, Any],
    season: int,
    round_: int,
    driver_ref_to_id: dict[str, int],
    team_ref_to_id: dict[str, int],
) -> dict[str, Any] | None:
    # Drivers tied on 0 points with no classification yet report position='-'
    # (no numeric 'position' key at all) rather than a real standing.
    position_raw = entry.get("position")
    if position_raw is None or not str(position_raw).isdigit():
        return None
    driver_id = driver_ref_to_id.get(entry["Driver"]["driverId"])
    if driver_id is None:
        return None
    constructors = entry.get("Constructors") or []
    team_id = team_ref_to_id.get(constructors[-1]["constructorId"]) if constructors else None
    return {
        "season": season,
        "round": round_,
        "driver_id": driver_id,
        "team_id": team_id,
        "position": int(position_raw),
        "points": float(entry["points"]),
        "wins": int(entry["wins"]),
    }


def normalize_constructor_standing(
    entry: dict[str, Any],
    season: int,
    round_: int,
    team_ref_to_id: dict[str, int],
) -> dict[str, Any] | None:
    position_raw = entry.get("position")
    if position_raw is None or not str(position_raw).isdigit():
        return None
    team_id = team_ref_to_id.get(entry["Constructor"]["constructorId"])
    if team_id is None:
        return None
    return {
        "season": season,
        "round": round_,
        "team_id": team_id,
        "position": int(position_raw),
        "points": float(entry["points"]),
        "wins": int(entry["wins"]),
    }
