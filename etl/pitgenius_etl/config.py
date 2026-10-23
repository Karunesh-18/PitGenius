import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str
    fastf1_cache_dir: str
    jolpica_base_url: str


def get_settings() -> Settings:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Copy etl/.env.example to etl/.env and fill it in.")
    return Settings(
        database_url=database_url,
        fastf1_cache_dir=os.environ.get("FASTF1_CACHE_DIR", ".fastf1_cache"),
        jolpica_base_url=os.environ.get("JOLPICA_BASE_URL", "https://api.jolpi.ca/ergast/f1"),
    )
