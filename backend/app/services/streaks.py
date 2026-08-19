"""External activity streaks (GitHub, LeetCode) and the shared streak walk.

GitHub and LeetCode don't expose an official "current streak" endpoint, so these use
community/public APIs (no auth token required) and derive the streak the same way
``services.stats`` does for our own tasks. Results are cached briefly in-process since
these are third-party services we don't want to hammer on every page load.
"""

import json
import time
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import HTTPException

from app.config import settings

_streak_cache: dict[str, tuple[float, dict]] = {}


def current_streak(has_activity: Callable[[date], bool], today: date) -> int:
    """Count consecutive active days ending today — or yesterday, so a morning visit
    before finishing anything doesn't show a broken streak.

    This is the single source of truth for the streak rule; the local-task, GitHub, and
    LeetCode streaks all call it with their own ``has_activity`` predicate.
    """
    cursor = today if has_activity(today) else today - timedelta(days=1)
    streak = 0
    while has_activity(cursor):
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _cache_get(key: str) -> Optional[dict]:
    hit = _streak_cache.get(key)
    if hit and time.time() - hit[0] < settings.streak_cache_ttl:
        return hit[1]
    return None


def _cache_set(key: str, value: dict) -> None:
    _streak_cache[key] = (time.time(), value)


# ---------------------------------------------------------------- GitHub

async def _fetch_github_contributions(username: str) -> dict[str, dict]:
    """date (YYYY-MM-DD) -> {"count": int, "level": 0-4}, current + previous year."""
    cached = _cache_get(f"gh-raw:{username}")
    if cached is not None:
        return cached

    today = date.today()
    contributions: dict[str, dict] = {}
    async with httpx.AsyncClient(timeout=8) as client:
        for year in {today.year, today.year - 1}:
            resp = await client.get(
                f"https://github-contributions-api.jogruber.de/v4/{username}",
                params={"y": year},
            )
            if resp.status_code == 404:
                raise HTTPException(404, f"GitHub user '{username}' not found")
            if resp.status_code != 200:
                continue
            for day in resp.json().get("contributions", []):
                contributions[day["date"]] = {
                    "count": day["count"],
                    "level": day.get("level", 0),
                }

    if not contributions:
        raise HTTPException(502, "couldn't reach GitHub contributions API")

    _cache_set(f"gh-raw:{username}", contributions)
    return contributions


async def fetch_github_streak(username: str) -> dict:
    cached = _cache_get(f"gh:{username}")
    if cached is not None:
        return cached

    contributions = await _fetch_github_contributions(username)
    streak = current_streak(
        lambda d: contributions.get(d.isoformat(), {}).get("count", 0) > 0,
        date.today(),
    )
    result = {"username": username, "streak": streak}
    _cache_set(f"gh:{username}", result)
    return result


async def fetch_github_activity(username: str, days: int = 30) -> dict:
    contributions = await _fetch_github_contributions(username)
    today = date.today()
    daily = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        info = contributions.get(d.isoformat(), {})
        daily.append(
            {"date": d.isoformat(), "count": info.get("count", 0), "level": info.get("level", 0)}
        )
    return {"username": username, "days": daily, "total": sum(d["count"] for d in daily)}


# ---------------------------------------------------------------- LeetCode

def _leetcode_level(count: int) -> int:
    """Bucket a day's submission count into the same 0-4 scale the GitHub cells use."""
    if count <= 0:
        return 0
    if count == 1:
        return 1
    if count <= 3:
        return 2
    if count <= 6:
        return 3
    return 4


async def fetch_leetcode_streak(username: str) -> dict:
    # LeetCode's own userCalendar.streak field is *not* "consecutive days ending
    # today/yesterday" — it can report a nonzero streak for a run that ended weeks
    # ago (verified against real profiles). So the streak is derived here from the
    # submission calendar the same way the local and GitHub streaks are; only
    # total_active_days (a simple cumulative counter) is trusted straight from LeetCode.
    cached = _cache_get(f"lc:{username}")
    if cached is not None:
        return cached

    query = """
    query userProfileCalendar($username: String!) {
      matchedUser(username: $username) {
        userCalendar {
          totalActiveDays
        }
      }
    }
    """
    async with httpx.AsyncClient(timeout=8) as client:
        resp = await client.post(
            "https://leetcode.com/graphql",
            json={"query": query, "variables": {"username": username}},
            headers={"Content-Type": "application/json", "Referer": "https://leetcode.com"},
        )
    if resp.status_code != 200:
        raise HTTPException(502, "couldn't reach LeetCode")

    matched = (resp.json().get("data") or {}).get("matchedUser")
    if not matched:
        raise HTTPException(404, f"LeetCode user '{username}' not found")

    total_active_days = matched["userCalendar"]["totalActiveDays"]

    submissions = await _fetch_leetcode_submissions(username)
    streak = current_streak(
        lambda d: submissions.get(d.isoformat(), 0) > 0,
        date.today(),
    )

    result = {
        "username": username,
        "streak": streak,
        "total_active_days": total_active_days,
    }
    _cache_set(f"lc:{username}", result)
    return result


async def _fetch_leetcode_submissions(username: str) -> dict[str, int]:
    """date (YYYY-MM-DD) -> submission count, current + previous year."""
    cached = _cache_get(f"lc-raw:{username}")
    if cached is not None:
        return cached

    query = """
    query userProfileCalendar($username: String!, $year: Int) {
      matchedUser(username: $username) {
        userCalendar(year: $year) {
          submissionCalendar
        }
      }
    }
    """
    today = date.today()
    submissions: dict[str, int] = {}
    found_user = False
    async with httpx.AsyncClient(timeout=8) as client:
        for year in {today.year, today.year - 1}:
            resp = await client.post(
                "https://leetcode.com/graphql",
                json={"query": query, "variables": {"username": username, "year": year}},
                headers={"Content-Type": "application/json", "Referer": "https://leetcode.com"},
            )
            if resp.status_code != 200:
                continue
            matched = (resp.json().get("data") or {}).get("matchedUser")
            if not matched:
                continue
            found_user = True
            raw = (matched.get("userCalendar") or {}).get("submissionCalendar")
            if not raw:
                continue
            for ts, count in json.loads(raw).items():
                d = datetime.fromtimestamp(int(ts), tz=timezone.utc).date().isoformat()
                submissions[d] = submissions.get(d, 0) + count

    if not found_user:
        raise HTTPException(404, f"LeetCode user '{username}' not found")

    _cache_set(f"lc-raw:{username}", submissions)
    return submissions


async def fetch_leetcode_activity(username: str, days: int = 30) -> dict:
    submissions = await _fetch_leetcode_submissions(username)
    today = date.today()
    daily = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        count = submissions.get(d.isoformat(), 0)
        daily.append({"date": d.isoformat(), "count": count, "level": _leetcode_level(count)})
    return {"username": username, "days": daily, "total": sum(d["count"] for d in daily)}
