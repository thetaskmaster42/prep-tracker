"""Streaks, today's totals, and the completion heatmap."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.stats import StatsOut
from app.services.stats import compute_stats

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    return compute_stats(db)
