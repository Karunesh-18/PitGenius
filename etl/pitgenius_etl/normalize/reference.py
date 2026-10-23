"""Normalize Jolpica (Ergast-shaped) reference data into our column names."""
from __future__ import annotations

import datetime as dt
from typing import Any

from ..seed.team_colors import TEAM_COLORS


def normalize_circuit(raw: dict[str, Any]) -> dict[str, Any]:
    location = raw.get("Location", {})
    return {
        "circuit_ref": raw["circuitId"],
        "name": raw["circuitName"],
        "locality": location.get("locality"),
        "country": location.get("country"),
        "lat": float(location["lat"]) if location.get("lat") is not None else None,
        "lng": float(location["long"]) if location.get("long") is not None else None,
    }


def normalize_driver(raw: dict[str, Any]) -> dict[str, Any]:
    dob = raw.get("dateOfBirth")
    return {
        "driver_ref": raw["driverId"],
        "fastf1_code": raw.get("code"),
        "permanent_number": int(raw["permanentNumber"]) if raw.get("permanentNumber") else None,
        "given_name": raw["givenName"],
        "family_name": raw["familyName"],
        "nationality": raw.get("nationality"),
        "date_of_birth": dt.date.fromisoformat(dob) if dob else None,
    }


def normalize_team(raw: dict[str, Any]) -> dict[str, Any]:
    colors = TEAM_COLORS.get(raw["constructorId"])
    return {
        "constructor_ref": raw["constructorId"],
        "name": raw["name"],
        "nationality": raw.get("nationality"),
        "color_primary": colors[0] if colors else None,
        "color_secondary": colors[1] if colors else None,
    }


def normalize_race(raw: dict[str, Any], circuit_id: int) -> dict[str, Any]:
    return {
        "season": int(raw["season"]),
        "round": int(raw["round"]),
        "circuit_id": circuit_id,
        "name": raw["raceName"],
        "race_date": dt.date.fromisoformat(raw["date"]),
        "event_format": "sprint" if "Sprint" in raw else "conventional",
    }
