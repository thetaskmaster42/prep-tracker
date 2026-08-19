# ---- stage 1: build the React frontend ----
FROM node:20-slim AS web
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
# Build into a local ./dist (the repo's vite outDir points into the backend, which
# doesn't exist in this stage) and copy it into the backend image below.
RUN npm run build -- --outDir dist --emptyOutDir

# ---- stage 2: python backend serving the built bundle ----
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
# DATABASE_URL is supplied at runtime (Postgres via the CloudNativePG secret in k8s, or
# docker-compose). With none set the app falls back to a local SQLite file.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Install deps first so dependency-only changes don't bust the layer cache.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/ ./
COPY --from=web /web/dist ./app/static

ENV PATH="/app/.venv/bin:$PATH"

RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

# By default the app runs `alembic upgrade head` on startup (single-container runs). In
# multi-replica k8s this is disabled (RUN_MIGRATIONS_ON_STARTUP=false) and the migrate Job
# owns schema changes. The same image runs that Job via `alembic upgrade head`.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
