"""Application configuration, read from environment variables.

Twelve-factor style: nothing is hard-coded, everything comes from the
environment so the same image runs in dev, staging and production.
"""

import os


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    app_name: str = os.getenv("APP_NAME", "Task Board")
    environment: str = os.getenv("ENVIRONMENT", "development")
    version: str = os.getenv("APP_VERSION", "dev")
    # Falls back to a local SQLite file so the test suite and a bare
    # `uvicorn app.main:app` run with no database server present.
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./local.db")
    db_connect_retries: int = int(os.getenv("DB_CONNECT_RETRIES", "30"))
    db_connect_delay: float = float(os.getenv("DB_CONNECT_DELAY", "2"))
    metrics_enabled: bool = _bool("METRICS_ENABLED", True)
    log_level: str = os.getenv("LOG_LEVEL", "info")

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


settings = Settings()
