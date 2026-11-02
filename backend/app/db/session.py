from collections.abc import Generator
import logging

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()


def normalize_database_url(raw_url: str) -> str:
    url = raw_url.strip()
    if url.startswith("mysql://"):
        return "mysql+pymysql://" + url[len("mysql://"):]
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


def create_db_engine(raw_url: str):
    url = normalize_database_url(raw_url)
    connect_args = {}
    engine_kwargs = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    else:
        # MySQL & PostgreSQL resilient connection pooling
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 3600

    return create_engine(url, connect_args=connect_args, **engine_kwargs)


effective_url = normalize_database_url(settings.database_url)
engine = create_db_engine(effective_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
logger = logging.getLogger(__name__)


def database_target() -> str:
    url = make_url(effective_url)
    if url.drivername == "sqlite" and url.database and url.database != ":memory:":
        from pathlib import Path

        return str(Path(url.database).resolve())
    return url.render_as_string(hide_password=True)


logger.info("database configured target=%s", database_target())


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
