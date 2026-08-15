# Prep Tracker

A local daily work tracker with scheduled reminders, streaks, and GitHub/LeetCode activity
charts — built for interview-prep discipline. No accounts, no cloud: your data lives in one
SQLite file.

Modular monorepo:

- **`backend/`** — FastAPI + SQLAlchemy 2.0 REST API (`/api/v1`), Alembic migrations, SQLite
  by default (swap to Postgres via `DATABASE_URL`).
- **`apps/web/`** — React + TypeScript + Vite single-page app that talks to the API.

## Features

- **Streak scoreboard** — current streak, best streak, and a 12-week heatmap. A day counts
  toward the streak when it has at least one *completed* task.
- **Daily work log** — tasks with category (LeetCode, Project, Course, Behavioral, Writing,
  Applications, Other), planned minutes, and notes. Browse any day with the date arrows.
- **Reminders** — set a time and optional weekdays. Fires a desktop notification (with your
  permission) and an in-page toast while the page is open.
- **GitHub / LeetCode activity charts** — a 30-day contribution/submission heatmap for each,
  GitHub-calendar style: hover or focus a square for a tooltip with the exact count and date.

## Local development

Two processes: the API and the Vite dev server (which proxies `/api` to the API).

```bash
# terminal 1 — backend (http://127.0.0.1:8000)
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload

# terminal 2 — frontend (http://127.0.0.1:5173)
cd apps/web
npm install
npm run dev
```

Open http://127.0.0.1:5173. The interactive API docs live at http://127.0.0.1:8000/docs.

The database URL comes from `DATABASE_URL` (default: a local SQLite file next to the
backend). The legacy `PREP_TRACKER_DB` path env var is still honored as a fallback.

## Tests

```bash
cd backend && uv run pytest -v          # API + streak logic
cd apps/web && npm run test             # component + scheduler tests (Vitest)
```

Backend tests run against a temporary SQLite file and mock the outbound GitHub/LeetCode
calls, so they never touch your real data or the network.

## Running in Docker / Kubernetes

The image is a single deployable: the frontend is built and the backend serves it alongside
the API.

```bash
docker compose up --build            # http://localhost:8000
```

The image exposes `/healthz` for liveness/readiness checks and runs `alembic upgrade head`
on startup. Kubernetes manifests (Deployment, PVC, Service) are in [`k8s/`](k8s/):

```bash
kubectl apply -f k8s/
```

**Note:** this app uses a single SQLite file, so the Deployment is pinned to `replicas: 1` —
don't scale it out, since multiple pods writing to the same file over shared storage will
corrupt it. To scale, point `DATABASE_URL` at Postgres first.

### Migrating an existing SQLite database

If you have a `prep_tracker.db` from the pre-migration (single-file) version, mark it as
current before starting so Alembic doesn't try to recreate its tables:

```bash
cd backend && DATABASE_URL=sqlite:////path/to/prep_tracker.db uv run alembic stamp head
```

## CI/CD

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push/PR to `main`:

1. **test** — backend `uv sync --frozen` + `uv run pytest -v`.
2. **web** — frontend `npm ci`, typecheck, Vitest, and production build.
3. **docker** — after both pass, builds the multi-arch image with Buildx. On pushes to
   `main` it also pushes to `ghcr.io/thetaskmaster42/prep-tracker`, tagged with the branch,
   short commit SHA, and `latest`. It authenticates with the automatic `GITHUB_TOKEN`.

## API (`/api/v1`)

| Method | Path                              | Purpose                                         |
| ------ | --------------------------------- | ----------------------------------------------- |
| GET    | /api/v1/categories                | Task categories                                 |
| GET    | /api/v1/tasks?day=YYYY-MM-DD      | Tasks for a day (default today)                 |
| POST   | /api/v1/tasks                     | Create a task                                   |
| PATCH  | /api/v1/tasks/{id}                | Update fields / toggle done                     |
| DELETE | /api/v1/tasks/{id}                | Delete a task                                   |
| GET    | /api/v1/reminders                 | List reminders                                  |
| POST   | /api/v1/reminders                 | Create a reminder                               |
| PATCH  | /api/v1/reminders/{id}/toggle     | Enable/disable a reminder                       |
| DELETE | /api/v1/reminders/{id}            | Delete a reminder                               |
| GET    | /api/v1/stats                     | Streaks, today totals, heatmap                  |
| GET    | /api/v1/settings                  | Get configured GitHub/LeetCode usernames        |
| PUT    | /api/v1/settings                  | Set GitHub/LeetCode usernames                   |
| GET    | /api/v1/github-streak             | Current GitHub contribution streak              |
| GET    | /api/v1/github-activity?days=30   | Daily GitHub contribution counts for the window |
| GET    | /api/v1/leetcode-streak           | Current LeetCode submission streak              |
| GET    | /api/v1/leetcode-activity?days=30 | Daily LeetCode submission counts for the window |
| GET    | /healthz                          | Liveness/readiness check (unversioned)          |

## Notes & ideas for extending it

- Reminders fire client-side, so the tab must be open. A natural v2: a small scheduler in the
  backend plus Web Push so reminders fire with the tab closed.
- The GitHub/LeetCode streak lookups use unofficial public APIs (no auth token required) and
  are cached in-process for 5 minutes per username.
- Other easy extensions: weekly hours-by-category chart, CSV export, edit-in-place for tasks,
  recurring task templates.
