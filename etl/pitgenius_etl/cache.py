import os

import fastf1

from .config import Settings


def enable_fastf1_cache(settings: Settings) -> None:
    """Must be called once before any fastf1.get_session(...) call.

    Without this, FastF1 re-downloads timing/telemetry data from F1's
    servers on every run. With it, repeat ETL runs during development
    are near-instant after the first pull. The cache directory is
    gitignored and can grow to multiple GB across seasons.
    """
    os.makedirs(settings.fastf1_cache_dir, exist_ok=True)
    fastf1.Cache.enable_cache(settings.fastf1_cache_dir)
