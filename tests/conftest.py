import os
import tempfile

import pytest

# Point the app at a throwaway SQLite file BEFORE importing it, so tests
# never touch a real database.
_TMP_DIR = tempfile.mkdtemp(prefix="taskboard-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_TMP_DIR, 'test.db')}"
os.environ["METRICS_ENABLED"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
