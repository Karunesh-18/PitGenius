import time
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings

_settings = get_settings()
# Neon: always-on fallback (holds 2023). Archive: full multi-season store on the GPU server.
neon_engine = create_engine(_settings.database_url, pool_pre_ping=True)
engine = neon_engine
_archive_engine = (
    create_engine(_settings.archive_database_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
    if _settings.archive_database_url
    else None
)

_PROBE_TTL = 30.0
_probe = {"at": 0.0, "up": False}


def archive_up() -> bool:
    """Cached reachability check so a dead SSH tunnel costs one probe per 30 s, not one per request."""
    if _archive_engine is None:
        return False
    now = time.monotonic()
    if now - _probe["at"] > _PROBE_TTL:
        try:
            with _archive_engine.connect() as c:
                c.execute(text("select 1"))
            _probe["up"] = True
        except Exception:
            _probe["up"] = False
        _probe["at"] = now
    return _probe["up"]


_neon_factory = sessionmaker(bind=neon_engine)
_archive_factory = sessionmaker(bind=_archive_engine) if _archive_engine else None
SessionLocal = _neon_factory


def get_db() -> Generator[Session, None, None]:
    db = _archive_factory() if _archive_factory and archive_up() else _neon_factory()
    try:
        yield db
    finally:
        db.close()
