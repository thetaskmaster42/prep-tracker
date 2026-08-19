# Prep Tracker — backend

FastAPI + SQLAlchemy 2.0 backend. See the [repo README](../README.md) for the full picture.

```bash
uv sync                                   # install deps
uv run alembic upgrade head               # create / migrate the database
uv run uvicorn app.main:app --reload      # dev server -> http://127.0.0.1:8000
uv run pytest -v                          # tests
```

The database URL comes from `DATABASE_URL` (default: a local SQLite file). The legacy
`PREP_TRACKER_DB` path env var is still honored as a fallback so older deployments keep
working. Point `DATABASE_URL` at Postgres to scale past a single replica — a plain
`postgresql://user:pass@host:5432/db` URL works (the psycopg driver is pinned automatically):

```bash
DATABASE_URL=postgresql://prep:prep@localhost:5432/prep_tracker uv run alembic upgrade head
```

`RUN_MIGRATIONS_ON_STARTUP=false` disables the startup migration (used in multi-replica k8s,
where a Job runs `alembic upgrade head` instead).
