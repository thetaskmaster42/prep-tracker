# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Prep Tracker: a local daily work tracker with reminders, streaks, and GitHub/LeetCode
activity charts, built for interview-prep discipline. A modular monorepo:

- **`backend/`** — FastAPI + SQLAlchemy 2.0 REST API under `/api/v1`, Alembic migrations,
  SQLite by default (Postgres via `DATABASE_URL`).
- **`apps/web/`** — React + TypeScript + Vite single-page frontend.

No accounts, no cloud — data lives in one SQLite file.

## Commands

### Backend (`cd backend`)

Dependencies are managed with [uv](https://docs.astral.sh/uv/) — always use `uv run`/`uv sync`.

```bash
uv sync                                   # install deps
uv run alembic upgrade head               # create / migrate the DB
uv run uvicorn app.main:app --reload      # dev server -> http://127.0.0.1:8000 (/docs for OpenAPI)
uv run pytest -v                          # full test suite (matches CI)
uv run pytest tests/test_app.py::test_stats_streak_counts_consecutive_done_days  # single test
```

`DATABASE_URL` selects the database (default: a SQLite file next to the backend). The legacy
`PREP_TRACKER_DB` path env var is honored as a fallback. `tests/conftest.py` points
`DATABASE_URL` at a temp SQLite file before importing the app.

### Frontend (`cd apps/web`)

```bash
npm install
npm run dev          # Vite dev server -> http://127.0.0.1:5173 (proxies /api to :8000)
npm run typecheck    # tsc --noEmit
npm run test         # Vitest
npm run build        # production build -> backend/app/static (served by the backend)
```

## Architecture

### Backend (`backend/app/`)

Organized as a small FastAPI package — extend the matching module rather than adding
top-level files:

- **`main.py`** — `create_app()`: CORS, includes the routers under `/api/v1`, mounts the built
  frontend at `/` when present, and runs `alembic upgrade head` in the lifespan on startup.
- **`config.py`** — `pydantic-settings` `Settings` (`database_url`, `streak_cache_ttl`,
  `cors_origins`, `static_dir`).
- **`db/`** — `base.py` (engine, `SessionLocal`, `Base`, the `get_db()` session dependency),
  `models.py` (`Task`, `Reminder`, `Setting`), `migrate.py` (programmatic Alembic upgrade).
  `get_db()` yields a session, commits on success, rolls back on error. Table/column names
  mirror the original schema so an existing `prep_tracker.db` works after `alembic stamp head`.
- **`schemas/`** — Pydantic request/response models (used as `response_model` for typed
  OpenAPI). The external-streak endpoints intentionally return plain dicts to preserve their
  `{"configured": false}` / `{"configured": true, ...}` union shape.
- **`routers/`** — one `APIRouter` per area (tasks, reminders, stats, settings, streaks) plus
  `health` (mounted at the root, outside `/api/v1`, for probes).
- **`services/`** — business logic. `streaks.py` holds the GitHub/LeetCode fetchers, the
  in-process TTL cache (`_streak_cache`), and the **single** `current_streak(has_activity,
  today)` helper; `stats.py` computes the local streak/heatmap. `settings.py` reads/writes
  the key/value settings table.

**Migrations**: Alembic under `backend/alembic/`. Schema changes = a new migration
(`uv run alembic revision --autogenerate -m "..."`, then review). `env.py` pulls the URL and
`Base.metadata` from the app so models and migrations don't drift. Tests create the schema
directly with `Base.metadata.create_all` (they don't run Alembic).

**SQLite/Postgres portability**: the app runs on both, so keep dialect-portable — models use
`func.now()` / `false()` for defaults (never `datetime('now')`), and raw SQL in
`services/stats.py` treats `done` as a boolean (`WHERE done`, `SUM(CASE WHEN done …)`, never
`done = 1`). `config._normalize_url` pins the psycopg driver so a plain `postgresql://…` URL
(e.g. the CloudNativePG secret) works. The CI `test-postgres` job runs the whole suite against
real Postgres to catch drift.

**Streak semantics**: a streak counts consecutive days *ending today or yesterday* — a day is
only required to have activity once today has happened. This rule lives in exactly one place
now, `services.streaks.current_streak`; the local, GitHub, and LeetCode streaks all pass it a
predicate. **External streaks are derived, not trusted from source**: LeetCode's own
`userCalendar.streak` can report a stale run, so both GitHub and LeetCode streaks are computed
in-app from the raw calendars; only `totalActiveDays` is taken as-is from LeetCode. These
calls hit unofficial public APIs (no auth) and are cached per username for 5 minutes.

**Deployment**: production runs on Postgres provisioned by the CloudNativePG operator
(`k8s/postgres-cluster.yaml`); the app reads `DATABASE_URL` from the operator-generated
`prep-tracker-db-app` secret and scales to `replicas: 2+` (no single-writer constraint).
Migrations are owned by a one-shot Job (`k8s/migrate-job.yaml`) so replicas don't race — the
app itself skips startup migrations there via `RUN_MIGRATIONS_ON_STARTUP=false`. Local dev and
tests still use SQLite; `docker compose` runs a prod-like app+Postgres stack.

### Frontend (`apps/web/src/`)

- **`api/`** — `client.ts` (typed `fetch` wrapper, baseURL `/api/v1`, throws `ApiError`) and
  `types.ts` (response types mirroring the backend schemas).
- **`hooks/queries.ts`** — TanStack Query hooks + mutations; task/reminder mutations invalidate
  the relevant queries (task writes also refresh `stats`). `useReminderScheduler` fires due
  reminders client-side (setInterval, weekday/`HH:MM` match, dedupe, desktop `Notification` +
  toast); `useMidnightRefresh` refetches on day rollover.
- **`components/`** — `Header` (scoreboard + local `Heatmap` + `SettingsPanel` + GitHub/LeetCode
  `ActivityStrip` cards), `WorkLog` (date nav + `TaskList` + `TaskForm`), `Reminders`, `Toast`.
- No custom charting library — the heatmaps are CSS-grid/flex cell grids, as before.

In dev the Vite server proxies `/api` and `/healthz` to the backend on :8000. In production the
backend serves the built bundle from `backend/app/static`.

## Testing conventions

- **Backend** (`backend/tests/`): `conftest.py` sets `DATABASE_URL` to a temp file before
  importing the app and creates the schema with `Base.metadata.create_all`; the autouse
  `clean_state` fixture wipes the three tables and clears the streak cache. External calls are
  never hit for real — monkeypatch the functions on `app.services.streaks` (the routers call
  them via the module so patches are seen), or monkeypatch `app.services.streaks.httpx.AsyncClient`
  for lower-level parsing tests.
- **Frontend**: Vitest + React Testing Library (jsdom). High-value coverage on the reminder
  scheduler and list rendering; mock the API client, never the network.

## CI/CD

`.github/workflows/ci.yml` runs on every push/PR to `main`: a `test` job (backend
`uv sync --frozen` + `pytest -v` on SQLite), a `test-postgres` job (same suite against a
Postgres service container, after `alembic upgrade head`), a `web` job (`npm ci`, typecheck,
Vitest, build), then a `docker` job (`needs: [test, test-postgres, web]`) that builds the
multi-arch (amd64+arm64) image with Buildx
and, only on pushes to `main`, pushes it to `ghcr.io/thetaskmaster42/prep-tracker` tagged with
branch, short SHA, and `latest`. The Dockerfile is multi-stage: a Node stage builds the
frontend, the Python stage serves it. `k8s/deployment.yaml` points at that image.
