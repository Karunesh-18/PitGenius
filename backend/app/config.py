import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str
    cors_origins: list[str]
    archive_database_url: str | None = None


def get_settings() -> Settings:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Copy backend/.env.example to backend/.env and fill it in.")
    cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    return Settings(
        database_url=database_url,
        cors_origins=cors_origins,
        archive_database_url=os.environ.get("ARCHIVE_DATABASE_URL") or None,
    )
