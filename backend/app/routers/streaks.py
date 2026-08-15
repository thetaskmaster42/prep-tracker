"""External GitHub/LeetCode streak and activity endpoints.

The service functions are referenced through the ``streaks`` module (not imported by name)
so tests can monkeypatch them.
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services import streaks
from app.services.settings import read_settings

router = APIRouter(tags=["external-streaks"])


def _validate_days(days: int) -> None:
    if not (1 <= days <= 90):
        raise HTTPException(400, "days must be between 1 and 90")


@router.get("/github-streak")
async def github_streak(db: Session = Depends(get_db)):
    username = read_settings(db)["github_username"]
    if not username:
        return {"configured": False}
    try:
        result = await streaks.fetch_github_streak(username)
    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(502, "GitHub streak lookup failed")
    return {"configured": True, **result}


@router.get("/github-activity")
async def github_activity(days: int = 30, db: Session = Depends(get_db)):
    _validate_days(days)
    username = read_settings(db)["github_username"]
    if not username:
        return {"configured": False}
    try:
        result = await streaks.fetch_github_activity(username, days=days)
    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(502, "GitHub activity lookup failed")
    return {"configured": True, **result}


@router.get("/leetcode-streak")
async def leetcode_streak(db: Session = Depends(get_db)):
    username = read_settings(db)["leetcode_username"]
    if not username:
        return {"configured": False}
    try:
        result = await streaks.fetch_leetcode_streak(username)
    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(502, "LeetCode streak lookup failed")
    return {"configured": True, **result}


@router.get("/leetcode-activity")
async def leetcode_activity(days: int = 30, db: Session = Depends(get_db)):
    _validate_days(days)
    username = read_settings(db)["leetcode_username"]
    if not username:
        return {"configured": False}
    try:
        result = await streaks.fetch_leetcode_activity(username, days=days)
    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(502, "LeetCode activity lookup failed")
    return {"configured": True, **result}
