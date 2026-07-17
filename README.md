# Prep Tracker

A local daily work tracker with scheduled reminders, built for interview-prep discipline.
FastAPI + SQLite backend, single-page vanilla JS frontend. No accounts, no cloud — your
data lives in one SQLite file next to the app.

## Features

- **Streak scoreboard** — current streak, best streak, and a 12-week heatmap. A day counts
  toward the streak when it has at least one *completed* task.
- **Daily work log** — tasks with category (LeetCode, Project, Course, Behavioral, Writing,
  Applications, Other), planned minutes, and notes. Browse any day with the date arrows.
- **Reminders** — set a time and optional weekdays (e.g. LeetCode at 19:00 on weekdays).
  Fires a desktop notification (with your permission) and an in-page toast while the
  page is open.
- **GitHub / LeetCode activity charts** — a 30-day contribution/submission heatmap for
  each, GitHub-calendar style: hover or focus a square for a tooltip with the exact
  count and date.

## Setup

Dependencies are managed with [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run uvicorn app:app --reload
```

Open http://127.0.0.1:8000 — the database (`prep_tracker.db`) is created automatically
on first run. Set `PREP_TRACKER_DB=/path/to/file.db` to point it elsewhere (used by the
Docker image to keep the DB on a mounted volume).

## Tests

```bash
uv run pytest
```

Tests run against a temporary SQLite file (see `tests/conftest.py`) and mock the
outbound GitHub/LeetCode calls, so they don't touch your real data or the network.

## Running in Docker / Kubernetes

Build and run locally with Docker Compose (persists the DB in a named volume):

```bash
docker compose up --build
```

Or build the image directly:

```bash
docker build -t prep-tracker .
docker run -p 8000:8000 -v prep-tracker-data:/data prep-tracker
```

The image exposes `/healthz` for liveness/readiness checks. Kubernetes manifests
(Deployment, PVC, Service) are in [`k8s/`](k8s/):

```bash
kubectl apply -f k8s/
```

**Note:** this app uses a single SQLite file, so the Deployment is pinned to
`replicas: 1` — don't scale it out, since multiple pods writing to the same file over
shared storage will corrupt it. If you outgrow that, swap SQLite for Postgres first.

## CI/CD

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push/PR to `main`:

1. **test** — `uv sync --frozen` + `uv run pytest`.
2. **docker** — builds the image with Buildx (validates the Dockerfile on PRs too).
   On pushes to `main`, after tests pass, it also pushes to
   `ghcr.io/thetaskmaster42/prep-tracker`, tagged with the branch, short commit SHA,
   and `latest`. No secrets to configure — it authenticates with the automatic
   `GITHUB_TOKEN`. `k8s/deployment.yaml` already points at that image.

   The GHCR package may start **private**; if `kubectl` can't pull it, flip its
   visibility to public (or add an `imagePullSecret`) from the package settings on
   GitHub.

## API

| Method | Path                           | Purpose                                         |
| ------ | ------------------------------ | ----------------------------------------------- |
| GET    | /api/tasks?day=YYYY-MM-DD      | Tasks for a day (default today)                 |
| POST   | /api/tasks                     | Create a task                                   |
| PATCH  | /api/tasks/{id}                | Update fields / toggle done                     |
| DELETE | /api/tasks/{id}                | Delete a task                                   |
| GET    | /api/reminders                 | List reminders                                  |
| POST   | /api/reminders                 | Create a reminder                               |
| PATCH  | /api/reminders/{id}/toggle     | Enable/disable a reminder                       |
| DELETE | /api/reminders/{id}            | Delete a reminder                               |
| GET    | /api/stats                     | Streaks, today totals, heatmap                  |
| GET    | /api/settings                  | Get configured GitHub/LeetCode usernames        |
| PUT    | /api/settings                  | Set GitHub/LeetCode usernames                   |
| GET    | /api/github-streak             | Current GitHub contribution streak              |
| GET    | /api/github-activity?days=30   | Daily GitHub contribution counts for the window |
| GET    | /api/leetcode-streak           | Current LeetCode submission streak              |
| GET    | /api/leetcode-activity?days=30 | Daily LeetCode submission counts for the window |
| GET    | /healthz                       | Liveness/readiness check                        |

## Notes & ideas for extending it

- Reminders fire client-side, so the tab must be open. A natural v2: a small
  `apscheduler` job in the backend plus OS-level notifications, or a Web Push service
  worker so reminders fire with the tab closed.
- The GitHub/LeetCode streak lookups use unofficial public APIs (no auth token
  required) and are cached in-process for 5 minutes per username.
- Other easy extensions: weekly hours-by-category chart, CSV export, edit-in-place
  for tasks, recurring task templates ("2 LeetCode mediums" auto-added daily).
