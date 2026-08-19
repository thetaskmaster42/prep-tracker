"""FastAPI application factory.

Wires the versioned API routers, health probe, CORS, and (in production) serving of the
built frontend bundle. Database migrations run on startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db.migrate import run_migrations
from app.routers import health, reminders, settings as settings_router, stats, streaks, tasks

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # In multi-replica k8s a dedicated migration Job owns schema changes, so startup
    # migrations are disabled there (settings.run_migrations_on_startup=false) to avoid
    # replicas racing on `alembic upgrade`.
    if settings.run_migrations_on_startup:
        run_migrations()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Prep Tracker", version="0.2.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for module in (tasks, reminders, stats, settings_router, streaks):
        app.include_router(module.router, prefix=API_PREFIX)
    app.include_router(health.router)  # /healthz stays at the root for probes

    # Serve the built frontend when it's present (production image). In dev the Vite
    # server owns the frontend and proxies the API, so this mount is simply absent.
    if settings.static_dir.exists():
        app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="frontend")

    return app


app = create_app()
