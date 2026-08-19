"""Engine, session factory, and the request-scoped session dependency."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


_url = settings.sqlalchemy_url
_is_sqlite = _url.startswith("sqlite")

# SQLite needs check_same_thread disabled so the connection can be reused across
# FastAPI's threadpool workers; other backends take no special connect args.
_engine_kwargs: dict = {
    "future": True,
    # Verify a pooled connection is alive before use — cheap insurance against
    # Postgres connections dropped by the server, a proxy, or a failover.
    "pool_pre_ping": True,
}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update(pool_size=5, max_overflow=5, pool_recycle=1800)

engine = create_engine(_url, **_engine_kwargs)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False, future=True
)


def get_db() -> Iterator[Session]:
    """Yield a session, commit on success, roll back on error, always close."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
