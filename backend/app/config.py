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


def _normalize_url(url: str) -> str:
    """Pin the psycopg (v3) driver for Postgres URLs.

    CloudNativePG (and most tooling) hands out plain ``postgresql://…`` / ``postgres://…``
    URLs, but SQLAlchemy needs an explicit driver; we ship psycopg 3. SQLite and any URL
    that already names a driver are left untouched.
    """
    for prefix in ("postgresql+", "postgres+"):
        if url.startswith(prefix):
            return url
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    # SQLAlchemy URL. SQLite by default; set to a postgresql:// URL (e.g. the CloudNativePG
    # `<cluster>-app` secret's `uri`) to run on Postgres — the driver is pinned automatically.
    database_url: str = _default_database_url()

    # Run `alembic upgrade head` on startup. True for local/single-container runs; set false
    # in multi-replica k8s where a dedicated migration Job owns schema changes (avoids races).
    run_migrations_on_startup: bool = True

    # In-process TTL (seconds) for cached GitHub/LeetCode streak lookups.
    streak_cache_ttl: int = 300

    # Origins allowed to call the API from a browser (the Vite dev server by default).
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Directory holding the built frontend bundle; served at "/" when present.
    static_dir: Path = _BACKEND_ROOT / "app" / "static"

    @property
    def sqlalchemy_url(self) -> str:
        """The database URL with a concrete SQLAlchemy driver pinned."""
        return _normalize_url(self.database_url)


settings = Settings()
