"""Database engine, session factory and startup readiness check."""

import logging
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

log = logging.getLogger(__name__)

connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,  # drop dead connections instead of erroring on them
    pool_recycle=1800,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """FastAPI dependency: one session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def wait_for_db() -> None:
    """Block until the database answers.

    Containers start in parallel. Even with a compose healthcheck this
    retry loop is what stops the app crash-looping on a slow database.
    """
    last_error: Exception | None = None
    for attempt in range(1, settings.db_connect_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            log.info("Database reachable after %s attempt(s)", attempt)
            return
        except OperationalError as exc:  # pragma: no cover - timing dependent
            last_error = exc
            log.warning("Database not ready (attempt %s), retrying...", attempt)
            time.sleep(settings.db_connect_delay)
    raise RuntimeError(f"Database unreachable: {last_error}")


def init_db() -> None:
    from app import models  # noqa: F401  (registers tables on Base)

    Base.metadata.create_all(bind=engine)
