from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import Settings


def make_session_factory(settings: Settings) -> sessionmaker[Session]:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    return sessionmaker(bind=engine)
