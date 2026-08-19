import os
import tempfile
from pathlib import Path

# Must be set before any app module is imported, since config reads it at import time
# to decide where the database lives. CI can inject DATABASE_URL to run the suite against
# a real Postgres (dialect-drift guard); otherwise we default to a throwaway SQLite file.
_tmp_dir = tempfile.TemporaryDirectory()
os.environ.setdefault("DATABASE_URL", f"sqlite:///{Path(_tmp_dir.name) / 'test.db'}")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.base import Base, SessionLocal, engine
from app.db import models  # noqa: F401  (registers tables on Base.metadata)
from app.main import app as fastapi_app
from app.services import streaks as streaks_module

# The client fixture doesn't run lifespan (no `with`), so create the schema directly.
Base.metadata.create_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(fastapi_app)


@pytest.fixture(autouse=True)
def clean_state():
    with SessionLocal() as session:
        for table in ("tasks", "reminders", "settings"):
            session.execute(text(f"DELETE FROM {table}"))
        session.commit()
    streaks_module._streak_cache.clear()
    yield
