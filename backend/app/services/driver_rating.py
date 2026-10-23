"""Driver Rating: a weighted formula over Phase-1 data, not a trained model.

There's no labeled "true skill" target to train against yet (that would
need many more seasons + a defined ground truth), so this is deliberately
a transparent, tunable weighted composite — the weights below are the
one place to adjust behavior, and this is the natural spot to swap in a
trained model in a later phase once enough historical data is loaded.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session as OrmSession

from .queries import qualifying_results_df, race_results_df

WEIGHT_QUALIFYING_PACE = 0.30
WEIGHT_RACE_PACE = 0.35
WEIGHT_CONSISTENCY = 0.20
WEIGHT_FINISHES = 0.15


def _min_max_scale(series: pd.Series, invert: bool = False) -> pd.Series:
    """Scale to 0-100. invert=True means a lower raw value is better
    (e.g. finishing position), so it maps to a higher score."""
    lo, hi = series.min(), series.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(50.0, index=series.index)
    scaled = (series - lo) / (hi - lo) * 100
    return 100 - scaled if invert else scaled


def compute_driver_ratings(db: OrmSession, season: int) -> dict[int, dict]:
    """Returns {driver_id: {rating, breakdown, points, wins, team_id, ...}}."""
    race_df = race_results_df(db, season)
    quali_df = qualifying_results_df(db, season)

    if race_df.empty:
        return {}

    classified = race_df.dropna(subset=["finish_position"])

    agg = race_df.groupby("driver_id").agg(
        races_entered=("status", "count"),
        points=("points", "sum"),
        wins=("finish_position", lambda s: int((s == 1).sum())),
        team_id=("team_id", "last"),
    )
    agg["races_classified"] = classified.groupby("driver_id")["finish_position"].count()
    agg["races_classified"] = agg["races_classified"].fillna(0)
    agg["avg_finish_position"] = classified.groupby("driver_id")["finish_position"].mean()
    agg["finish_std"] = classified.groupby("driver_id")["finish_position"].std().fillna(0)
    agg["completion_rate"] = agg["races_classified"] / agg["races_entered"]

    quali_agg = quali_df.dropna(subset=["position"]).groupby("driver_id")["position"].mean()
    agg["avg_quali_position"] = quali_agg

    # Drivers with no classified finishes at all (e.g. DNF'd every race) get
    # the worst-in-field pace/consistency score rather than a NaN midpoint.
    worst_finish = agg["avg_finish_position"].max()
    agg["avg_finish_position"] = agg["avg_finish_position"].fillna(worst_finish if pd.notna(worst_finish) else 20)
    worst_quali = agg["avg_quali_position"].max()
    agg["avg_quali_position"] = agg["avg_quali_position"].fillna(worst_quali if pd.notna(worst_quali) else 20)

    agg["qualifying_pace_score"] = _min_max_scale(agg["avg_quali_position"], invert=True)
    agg["race_pace_score"] = _min_max_scale(agg["avg_finish_position"], invert=True)
    agg["consistency_score"] = _min_max_scale(agg["finish_std"], invert=True)
    agg["finishes_score"] = agg["completion_rate"] * 100

    agg["driver_rating"] = (
        WEIGHT_QUALIFYING_PACE * agg["qualifying_pace_score"]
        + WEIGHT_RACE_PACE * agg["race_pace_score"]
        + WEIGHT_CONSISTENCY * agg["consistency_score"]
        + WEIGHT_FINISHES * agg["finishes_score"]
    ).round(1)

    result: dict[int, dict] = {}
    for driver_id, row in agg.iterrows():
        result[int(driver_id)] = {
            "team_id": int(row["team_id"]) if pd.notna(row["team_id"]) else None,
            "points": float(row["points"]),
            "wins": int(row["wins"]),
            "driver_rating": float(row["driver_rating"]),
            "rating_breakdown": {
                "qualifying_pace": round(float(row["qualifying_pace_score"]), 1),
                "race_pace": round(float(row["race_pace_score"]), 1),
                "consistency": round(float(row["consistency_score"]), 1),
                "finishes": round(float(row["finishes_score"]), 1),
            },
        }
    return result
