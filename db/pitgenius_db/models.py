"""Single source of truth for the PitGenius schema.

Both the ETL pipeline and the FastAPI backend install this package
(`pip install -e ../db`) and import these models rather than defining
their own — this is what keeps the schema from drifting between the
process that writes the data and the process that reads it.

Phase 2 adds `Telemetry` and four normalization columns on `Circuit`
(see docs/phase2-plan.md). Remaining Phase 2+ tables (tyre_stints,
weather, pit_stops, strategy_simulations, predictions) are still not
defined yet; they'll be added here as additive models + migrations
without touching anything below.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    constructor_ref: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    nationality: Mapped[str | None] = mapped_column(String(100))
    color_primary: Mapped[str | None] = mapped_column(String(7))
    color_secondary: Mapped[str | None] = mapped_column(String(7))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    drivers_current: Mapped[list["Driver"]] = relationship(back_populates="current_team")


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    driver_ref: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    fastf1_code: Mapped[str | None] = mapped_column(String(3))
    permanent_number: Mapped[int | None] = mapped_column(Integer)
    given_name: Mapped[str] = mapped_column(String(100), nullable=False)
    family_name: Mapped[str] = mapped_column(String(100), nullable=False)
    nationality: Mapped[str | None] = mapped_column(String(100))
    date_of_birth: Mapped[dt.date | None] = mapped_column(Date)
    headshot_url: Mapped[str | None] = mapped_column(String(500))
    current_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    current_team: Mapped[Team | None] = relationship(back_populates="drivers_current")


class Circuit(Base):
    __tablename__ = "circuits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    circuit_ref: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    locality: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    lat: Mapped[float | None] = mapped_column(Numeric(9, 6))
    lng: Mapped[float | None] = mapped_column(Numeric(9, 6))
    length_km: Mapped[float | None] = mapped_column(Numeric(5, 3))
    # Static 3D track outline: [{"x": ..., "y": ..., "z": ...}, ...],
    # normalized/centered/scaled server-side by the ETL track_outline step.
    track_outline: Mapped[list | None] = mapped_column(JSON)
    # The exact center/scale params used to build track_outline above, persisted
    # so per-driver telemetry (Phase 2) can be normalized into the SAME coordinate
    # frame as the ribbon — otherwise a telemetry-driven marker would drift off it.
    track_outline_center_x: Mapped[float | None] = mapped_column(Numeric(10, 4))
    track_outline_center_y: Mapped[float | None] = mapped_column(Numeric(10, 4))
    track_outline_center_z: Mapped[float | None] = mapped_column(Numeric(10, 4))
    track_outline_scale: Mapped[float | None] = mapped_column(Numeric(10, 6))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Race(Base):
    __tablename__ = "races"
    __table_args__ = (UniqueConstraint("season", "round", name="uq_races_season_round"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    circuit_id: Mapped[int] = mapped_column(ForeignKey("circuits.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    race_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    event_format: Mapped[str] = mapped_column(String(20), nullable=False, default="conventional")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    circuit: Mapped[Circuit] = relationship()
    sessions: Mapped[list["Session"]] = relationship(back_populates="race", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        UniqueConstraint("race_id", "session_type", name="uq_sessions_race_type"),
        CheckConstraint(
            "session_type IN ('FP1','FP2','FP3','Q','SQ','S','R')", name="ck_sessions_session_type"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id", ondelete="CASCADE"), nullable=False)
    session_type: Mapped[str] = mapped_column(String(3), nullable=False)
    session_date: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    race: Mapped[Race] = relationship(back_populates="sessions")
    lap_times: Mapped[list["LapTime"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class LapTime(Base):
    __tablename__ = "lap_times"
    __table_args__ = (UniqueConstraint("session_id", "driver_id", "lap_number", name="uq_lap_times_session_driver_lap"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    lap_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lap_time_ms: Mapped[int | None] = mapped_column(Integer)
    sector1_ms: Mapped[int | None] = mapped_column(Integer)
    sector2_ms: Mapped[int | None] = mapped_column(Integer)
    sector3_ms: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[int | None] = mapped_column(Integer)
    compound: Mapped[str | None] = mapped_column(String(20))
    tyre_life: Mapped[int | None] = mapped_column(Integer)
    is_pit_lap: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pit_in_time_ms: Mapped[int | None] = mapped_column(Integer)
    pit_out_time_ms: Mapped[int | None] = mapped_column(Integer)
    track_status: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[Session] = relationship(back_populates="lap_times")
    driver: Mapped[Driver] = relationship()


class QualifyingResult(Base):
    __tablename__ = "qualifying_results"
    __table_args__ = (UniqueConstraint("session_id", "driver_id", name="uq_quali_results_session_driver"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    position: Mapped[int | None] = mapped_column(Integer)
    q1_ms: Mapped[int | None] = mapped_column(Integer)
    q2_ms: Mapped[int | None] = mapped_column(Integer)
    q3_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[Session] = relationship()
    driver: Mapped[Driver] = relationship()
    team: Mapped[Team] = relationship()


class RaceResult(Base):
    __tablename__ = "race_results"
    __table_args__ = (UniqueConstraint("session_id", "driver_id", name="uq_race_results_session_driver"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    grid_position: Mapped[int | None] = mapped_column(Integer)
    finish_position: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    points: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    laps_completed: Mapped[int | None] = mapped_column(Integer)
    total_time_ms: Mapped[int | None] = mapped_column(BigInteger)
    fastest_lap_rank: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[Session] = relationship()
    driver: Mapped[Driver] = relationship()
    team: Mapped[Team] = relationship()


class DriverStanding(Base):
    __tablename__ = "driver_standings"
    __table_args__ = (UniqueConstraint("season", "round", "driver_id", name="uq_driver_standings_season_round_driver"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    points: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    driver: Mapped[Driver] = relationship()
    team: Mapped[Team | None] = relationship()


class ConstructorStanding(Base):
    __tablename__ = "constructor_standings"
    __table_args__ = (UniqueConstraint("season", "round", "team_id", name="uq_constructor_standings_season_round_team"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    points: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    team: Mapped[Team] = relationship()


class Telemetry(Base):
    """One representative lap of car telemetry per driver per race session
    (that driver's fastest R-session lap only — see docs/phase2-plan.md for
    the row-count/scope reasoning). Powers the animated 3D car marker and
    the Telemetry Viewer's speed/throttle/brake/gear/DRS traces.
    """

    __tablename__ = "telemetry"
    __table_args__ = (
        UniqueConstraint(
            "session_id", "driver_id", "lap_number", "point_index",
            name="uq_telemetry_session_driver_lap_point",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    lap_number: Mapped[int] = mapped_column(Integer, nullable=False)
    point_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 0..N-1, ordered by distance along the lap
    distance_m: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    time_ms: Mapped[int] = mapped_column(Integer, nullable=False)  # elapsed time from lap start, for playback
    speed_kph: Mapped[float | None] = mapped_column(Numeric(5, 1))
    throttle_pct: Mapped[int | None] = mapped_column(Integer)
    brake: Mapped[bool | None] = mapped_column(Boolean)
    gear: Mapped[int | None] = mapped_column(Integer)
    drs: Mapped[int | None] = mapped_column(Integer)
    # Same coordinate frame as circuits.track_outline_center_*/scale.
    x: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    y: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    z: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[Session] = relationship()
    driver: Mapped[Driver] = relationship()
