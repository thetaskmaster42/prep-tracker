"""Run Alembic migrations programmatically (used on app startup)."""

from pathlib import Path

from alembic import command
from alembic.config import Config

from app.config import settings

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


def run_migrations() -> None:
    """Upgrade the configured database to the latest Alembic revision."""
    cfg = Config(str(_BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", settings.sqlalchemy_url)
    command.upgrade(cfg, "head")
