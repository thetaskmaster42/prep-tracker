"""Liveness/readiness probe. Mounted at the root, outside the versioned API."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz():
    return {"status": "ok"}
