"""Race Strategy Simulator: rule-based arithmetic, not a trained model.

Phase 1 has no labeled strategy-outcome data to train an ML model on, so
this uses a transparent tire-degradation-curve + pit-loss formula. Phase 2
replaces/augments this with a trained tire degradation model and Monte
Carlo race-outcome simulation once telemetry/weather data is loaded —
see docs/phase1-plan.md.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from pitgenius_db.models import Circuit, LapTime, Race
from pitgenius_db.models import Session as SessionModel

DEFAULT_BASE_LAP_S = 90.0
DEFAULT_PIT_LOSS_S = 22.0
SECONDS_PER_GRID_POSITION = 1.5  # rough midpack gap used to translate a time delta into a position shift
MAX_POSITION_SHIFT = 6

# Rough, compound-relative offsets/degradation — not derived from telemetry yet.
COMPOUND_OFFSET_S = {
    "SOFT": -0.6,
    "MEDIUM": 0.0,
    "HARD": 0.6,
    "INTERMEDIATE": 6.0,
    "WET": 11.0,
}
COMPOUND_DEG_RATE_S_PER_LAP = {
    "SOFT": 0.09,
    "MEDIUM": 0.05,
    "HARD": 0.03,
    "INTERMEDIATE": 0.04,
    "WET": 0.03,
}


def _get_base_lap_time_s(db: OrmSession, circuit_ref: str) -> float:
    """Median non-pit race lap time actually observed at this circuit, if
    we have any loaded; otherwise a generic fallback."""
    stmt = (
        select(LapTime.lap_time_ms)
        .join(SessionModel, LapTime.session_id == SessionModel.id)
        .join(Race, SessionModel.race_id == Race.id)
        .join(Circuit, Race.circuit_id == Circuit.id)
        .where(
            Circuit.circuit_ref == circuit_ref,
            SessionModel.session_type == "R",
            LapTime.is_pit_lap.is_(False),
            LapTime.lap_time_ms.is_not(None),
        )
    )
    values = sorted(row[0] for row in db.execute(stmt).all())
    if not values:
        return DEFAULT_BASE_LAP_S
    return values[len(values) // 2] / 1000


def _stint_time_s(compound: str, num_laps: int, base_lap_s: float) -> float:
    if num_laps <= 0:
        return 0.0
    offset = COMPOUND_OFFSET_S[compound]
    deg = COMPOUND_DEG_RATE_S_PER_LAP[compound]
    per_lap_base = base_lap_s + offset
    return num_laps * per_lap_base + deg * num_laps * (num_laps - 1) / 2


def _lap_time_curve(compound: str, pit_lap: int, total_laps: int, base_lap_s: float) -> list[dict]:
    offset = COMPOUND_OFFSET_S[compound]
    deg = COMPOUND_DEG_RATE_S_PER_LAP[compound]
    curve = []
    for lap in range(1, total_laps + 1):
        stint_lap_index = (lap - 1) if lap <= pit_lap else (lap - pit_lap - 1)
        lap_time = base_lap_s + offset + deg * stint_lap_index
        curve.append({"lap": lap, "lap_time_s": round(lap_time, 3)})
    return curve


def _total_time_s(compound: str, pit_lap: int, total_laps: int, base_lap_s: float, pit_loss_s: float) -> float:
    stint1 = _stint_time_s(compound, pit_lap, base_lap_s)
    stint2 = _stint_time_s(compound, total_laps - pit_lap, base_lap_s)
    return stint1 + stint2 + pit_loss_s


def _find_optimal_pit_lap(compound: str, total_laps: int, base_lap_s: float, pit_loss_s: float) -> int:
    candidates = range(2, total_laps - 1) if total_laps > 4 else range(1, total_laps)
    best_lap = total_laps // 2
    best_time = float("inf")
    for lap in candidates:
        t = _total_time_s(compound, lap, total_laps, base_lap_s, pit_loss_s)
        if t < best_time:
            best_time = t
            best_lap = lap
    return best_lap


def simulate(
    db: OrmSession,
    circuit_ref: str,
    starting_position: int,
    tire_compound: str,
    pit_lap: int,
    num_laps: int,
) -> dict:
    base_lap_s = _get_base_lap_time_s(db, circuit_ref)
    pit_lap = min(pit_lap, num_laps - 1) if num_laps > 1 else pit_lap
    pit_loss_s = DEFAULT_PIT_LOSS_S

    user_total = _total_time_s(tire_compound, pit_lap, num_laps, base_lap_s, pit_loss_s)
    curve = _lap_time_curve(tire_compound, pit_lap, num_laps, base_lap_s)

    baseline_compound = "MEDIUM"
    baseline_pit_lap = num_laps // 2
    baseline_total = _total_time_s(baseline_compound, baseline_pit_lap, num_laps, base_lap_s, pit_loss_s)

    delta_s = baseline_total - user_total  # positive => user strategy is faster
    position_shift = max(-MAX_POSITION_SHIFT, min(MAX_POSITION_SHIFT, round(delta_s / SECONDS_PER_GRID_POSITION)))
    predicted_finish = max(1, min(20, starting_position - position_shift))

    optimal_pit_lap = _find_optimal_pit_lap(tire_compound, num_laps, base_lap_s, pit_loss_s)

    explanation = (
        f"{tire_compound.title()} tires carry a "
        f"{'pace' if COMPOUND_OFFSET_S[tire_compound] < 0 else 'durability'} trade-off "
        f"({COMPOUND_OFFSET_S[tire_compound]:+.1f}s/lap vs. medium baseline, "
        f"{COMPOUND_DEG_RATE_S_PER_LAP[tire_compound]:.2f}s/lap degradation). "
        f"Pitting on lap {pit_lap} is "
        f"{'close to' if abs(pit_lap - optimal_pit_lap) <= 2 else 'away from'} "
        f"the estimated optimal window for this compound (lap {optimal_pit_lap} of {num_laps}). "
        f"Versus a baseline medium-tire, mid-race-stop strategy, this is "
        f"{'faster' if delta_s >= 0 else 'slower'} by {abs(delta_s):.1f}s over the race, "
        f"moving the predicted finish from P{starting_position} to P{predicted_finish}."
    )

    return {
        "predicted_finish_position": predicted_finish,
        "total_time_estimate_s": round(user_total, 1),
        "pit_loss_s": pit_loss_s,
        "optimal_pit_lap": optimal_pit_lap,
        "lap_time_curve": curve,
        "explanation": explanation,
    }
