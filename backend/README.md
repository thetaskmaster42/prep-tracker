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
working. Point `DATABASE_URL` at Postgres (`postgresql+psycopg://…`) to scale past a
single replica.
