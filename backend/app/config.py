"""Application settings, read from the environment via pydantic-settings."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _default_database_url() -> str:
    """Default DB URL.

    Prefers the legacy ``PREP_TRACKER_DB`` filesystem path (kept for back-compat with
    existing Docker/k8s deployments) and otherwise points at a SQLite file next to the
    backend package.
    """
    legacy_path = os.environ.get("PREP_TRACKER_DB")
    if legacy_path:
        return f"sqlite:///{legacy_path}"
    return f"sqlite:///{_BACKEND_ROOT / 'prep_tracker.db'}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    # SQLAlchemy URL. SQLite by default; set to a postgresql+psycopg URL to scale out.
    database_url: str = _default_database_url()

    # In-process TTL (seconds) for cached GitHub/LeetCode streak lookups.
    streak_cache_ttl: int = 300

    # Origins allowed to call the API from a browser (the Vite dev server by default).
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Directory holding the built frontend bundle; served at "/" when present.
    static_dir: Path = _BACKEND_ROOT / "app" / "static"


settings = Settings()
