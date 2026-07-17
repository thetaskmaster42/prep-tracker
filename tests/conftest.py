import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Must be set before `app` is imported anywhere, since app.py reads it at
# module load time to decide where the SQLite file lives.
_tmp_dir = tempfile.TemporaryDirectory()
os.environ["PREP_TRACKER_DB"] = str(Path(_tmp_dir.name) / "test.db")

import pytest
from fastapi.testclient import TestClient

import app as app_module


@pytest.fixture()
def client():
    return TestClient(app_module.app)


@pytest.fixture(autouse=True)
def clean_state():
    with app_module.db() as conn:
        conn.executescript("DELETE FROM tasks; DELETE FROM reminders; DELETE FROM settings;")
    app_module._streak_cache.clear()
    yield
