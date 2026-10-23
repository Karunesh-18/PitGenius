"""Tire Degradation: a RandomForestRegressor trained on green-flag race
laps (lap_time_ms ~ compound + tyre_life + circuit), with per-prediction
SHAP explanations.

Unlike Strategy Simulator's hand-tuned formula (which predates enough
loaded data to train anything), Phase 2 has ~1 full season of real lap
times loaded, so this trains a small model directly from lap_times.

The trained model is cached in the module-level `_model_cache` below,
keyed on a cheap fingerprint of the training data (row count + summed
lap_time_ms) so repeated requests reuse it and it only retrains when the
underlying data actually changes (e.g. more rounds land via the ETL).
This in-process caching is a stopgap: the natural place to move this is
an offline-trained model artifact refreshed by a scheduled job, once
Phase 3 adds Celery — at Phase 2 data volumes (~1 season) training here
on a cache miss is still well under a second, so it's not worth the
extra moving parts yet.
"""
from __future__ import annotations

import pandas as pd
import shap
from sklearn.ensemble import RandomForestRegressor
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from pitgenius_db.models import LapTime, Race
from pitgenius_db.models import Session as SessionModel

from .queries import lap_times_with_context_df, latest_season

RANDOM_STATE = 42
N_ESTIMATORS = 200
MAX_DEPTH = 8

# "Fresh tyre" reference point. Not 1: lap-1 laps are excluded from training (see
# _get_or_train_model), and an out-lap is excluded as a pit lap, so tyre_life==1
# is essentially unobserved at racing pace and predicting there is extrapolation.
# Lap 2 of a stint is the freshest state the model has actually seen.
FRESH_TYRE_LIFE = 2

# Possibly-concatenated FastF1 track-status digit codes that mean the lap
# was NOT run under green-flag conditions: 4=SC, 5=red flag, 6=VSC,
# 7=VSC ending (1=clear, 2=yellow is kept in — still green-flag-ish pace).
NON_GREEN_STATUS_CODES = ("4", "5", "6", "7")

# {fingerprint: {model, feature_columns, compound_columns, circuit_columns}}
_model_cache: dict[tuple, dict] = {}


def _is_green_flag(track_status: str | None) -> bool:
    if not track_status:
        return True
    return not any(code in track_status for code in NON_GREEN_STATUS_CODES)


def _fingerprint(db: OrmSession, season: int) -> tuple:
    """Cheap staleness check, kept deliberately independent of the training
    DataFrame: the point of the cache is to avoid pulling ~30k lap rows through
    pandas on every prediction, which computing the fingerprint from that same
    DataFrame would defeat."""
    row = db.execute(
        select(func.count(LapTime.id), func.coalesce(func.sum(LapTime.lap_time_ms), 0))
        .join(SessionModel, LapTime.session_id == SessionModel.id)
        .join(Race, SessionModel.race_id == Race.id)
        .where(Race.season == season, SessionModel.session_type == "R")
    ).one()
    return (season, int(row[0]), int(row[1]))


def _build_feature_row(
    feature_columns: list[str], compound: str, circuit_ref: str, tyre_life: int
) -> pd.DataFrame:
    row = {c: 0.0 for c in feature_columns}
    row["tyre_life"] = float(tyre_life)
    # An unknown circuit or compound would otherwise leave its one-hot all-zero
    # and yield a confident-looking prediction for something never trained on.
    compound_col = f"compound_{compound}"
    if compound_col not in row:
        raise ValueError(f"No {compound} laps loaded to train on yet")
    row[compound_col] = 1.0
    circuit_col = f"circuit_{circuit_ref}"
    if circuit_col not in row:
        raise ValueError(f"No lap data loaded for circuit '{circuit_ref}' yet")
    row[circuit_col] = 1.0
    return pd.DataFrame([row], columns=feature_columns)


def _train(season: int, df: pd.DataFrame) -> dict:
    compound_cols = sorted(f"compound_{c}" for c in df["compound"].unique())
    circuit_cols = sorted(f"circuit_{c}" for c in df["circuit_ref"].unique())

    compound_dummies = pd.get_dummies(df["compound"], prefix="compound")
    circuit_dummies = pd.get_dummies(df["circuit_ref"], prefix="circuit")

    X = pd.DataFrame(index=df.index)
    X["tyre_life"] = df["tyre_life"].astype(float)
    for c in compound_cols:
        X[c] = compound_dummies[c].astype(float)
    for c in circuit_cols:
        X[c] = circuit_dummies[c].astype(float)
    feature_columns = list(X.columns)

    y = df["lap_time_ms"].astype(float)

    model = RandomForestRegressor(
        n_estimators=N_ESTIMATORS, max_depth=MAX_DEPTH, random_state=RANDOM_STATE, n_jobs=-1
    )
    model.fit(X, y)

    return {
        "model": model,
        "feature_columns": feature_columns,
        "compound_columns": compound_cols,
        "circuit_columns": circuit_cols,
    }


def _get_or_train_model(db: OrmSession, season: int) -> dict:
    fp = _fingerprint(db, season)
    cached = _model_cache.get(fp)
    if cached is not None:
        return cached

    df = lap_times_with_context_df(db, season)
    df = df.dropna(subset=["lap_time_ms", "compound", "tyre_life", "circuit_ref"])
    df = df[~df["is_pit_lap"].astype(bool)]
    df = df[df["track_status"].apply(_is_green_flag)]
    # Lap 1 is a standing start into turn-1 traffic, ~8s off green-flag pace, and
    # it is where essentially every tyre_life==1 sample comes from (an out-lap is
    # already excluded as a pit lap). Leaving it in makes a "fresh" tyre look
    # slower than a worn one and inverts the whole degradation curve.
    df = df[df["lap_number"] > 1]

    if df.empty:
        raise ValueError(f"No green-flag race lap data available for season={season} to train the model on")

    bundle = _train(season, df)
    _model_cache.clear()  # only ever keep the most recently trained model
    _model_cache[fp] = bundle
    return bundle


def _format_laptime(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = seconds - minutes * 60
    return f"{minutes}:{secs:04.1f}"


def _feature_field_and_value(feature: str, compound: str, circuit_ref: str, tyre_life: int) -> tuple[str, str]:
    if feature == "tyre_life":
        return "Tyre Age", f"{tyre_life} lap{'s' if tyre_life != 1 else ''}"
    if feature.startswith("compound_"):
        return "Compound", compound.title()
    if feature.startswith("circuit_"):
        return "Circuit", circuit_ref.replace("_", " ").title()
    return feature, ""


def _explanation_phrase(feature: str) -> str:
    if feature == "tyre_life":
        return "tyre age"
    if feature.startswith("compound_"):
        return "tire compound"
    if feature.startswith("circuit_"):
        return "this circuit"
    return feature


def predict(db: OrmSession, circuit_ref: str, compound: str, tyre_life: int) -> dict:
    season = latest_season(db)
    if season is None:
        raise ValueError("No season data loaded yet")

    bundle = _get_or_train_model(db, season)
    model = bundle["model"]
    feature_columns = bundle["feature_columns"]

    X_pred = _build_feature_row(feature_columns, compound, circuit_ref, tyre_life)
    X_baseline = _build_feature_row(feature_columns, compound, circuit_ref, FRESH_TYRE_LIFE)

    predicted_ms = float(model.predict(X_pred)[0])
    baseline_ms = float(model.predict(X_baseline)[0])
    predicted_s = round(predicted_ms / 1000, 3)
    baseline_s = round(baseline_ms / 1000, 3)
    degradation_s = round(predicted_s - baseline_s, 3)

    # Explain the *degradation*, not the absolute lap time. Raw SHAP values are
    # contributions relative to the training mean, so the circuit one-hot swamps
    # everything and gets narrated as the cause of tyre wear. Differencing
    # against the fresh-tyre row cancels the circuit/compound terms and leaves
    # what actually changed between the two, which is what degradation_vs_fresh_s
    # measures — so the contributions now sum to that number.
    explainer = shap.TreeExplainer(model)
    shap_pred = explainer.shap_values(X_pred)[0]
    shap_baseline = explainer.shap_values(X_baseline)[0]
    shap_row = shap_pred - shap_baseline

    contributions = []
    for feature, shap_val in zip(feature_columns, shap_row):
        if feature.startswith("compound_") and X_pred[feature].iloc[0] != 1:
            continue
        if feature.startswith("circuit_") and X_pred[feature].iloc[0] != 1:
            continue
        field, value = _feature_field_and_value(feature, compound, circuit_ref, tyre_life)
        contributions.append(
            {
                "feature": field,
                "value": value,
                "shap_value_s": round(float(shap_val) / 1000, 3),
                "_raw_feature": feature,
            }
        )
    contributions.sort(key=lambda c: abs(c["shap_value_s"]), reverse=True)

    # Only tyre age actually differs between the two rows, so the circuit and
    # compound terms cancel to near-zero and whatever is left of them is tree-path
    # residual. Naming a 0.03s residual as a cause of degradation reads as a real
    # finding, so keep it out of the sentence (it stays in shap_contributions).
    top = [c for c in contributions if abs(c["shap_value_s"]) >= 0.05][:2]
    if len(top) >= 2:
        drivers_desc = (
            f"{_explanation_phrase(top[0]['_raw_feature'])} ({top[0]['shap_value_s']:+.1f}s) and "
            f"{_explanation_phrase(top[1]['_raw_feature'])} ({top[1]['shap_value_s']:+.1f}s)"
        )
    elif top:
        drivers_desc = f"{_explanation_phrase(top[0]['_raw_feature'])} ({top[0]['shap_value_s']:+.1f}s)"
    else:
        drivers_desc = "tyre age"

    explanation = (
        f"On {compound.title()} tires at {tyre_life} lap{'s' if tyre_life != 1 else ''} of age, pace is predicted "
        f"at {_format_laptime(predicted_s)} — roughly {abs(degradation_s):.1f}s "
        f"{'slower' if degradation_s >= 0 else 'faster'} than the same tire fresh, driven mostly by {drivers_desc}."
    )

    for c in contributions:
        del c["_raw_feature"]

    return {
        "predicted_lap_time_s": predicted_s,
        "baseline_lap_time_s": baseline_s,
        "degradation_vs_fresh_s": degradation_s,
        "shap_contributions": contributions,
        "explanation": explanation,
    }
