"""
Prep Tracker — a local daily work tracker with reminders.
Run:  uvicorn app:app --reload
Then open http://127.0.0.1:8000
Data lives in prep_tracker.db (SQLite) next to this file.
"""

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

DB_PATH = Path(os.environ.get("PREP_TRACKER_DB", str(Path(__file__).parent / "prep_tracker.db")))
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Prep Tracker")


# ---------------------------------------------------------------- database

@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                category    TEXT NOT NULL DEFAULT 'Other',
                task_date   TEXT NOT NULL,              -- YYYY-MM-DD
                planned_min INTEGER NOT NULL DEFAULT 0, -- planned minutes
                done        INTEGER NOT NULL DEFAULT 0,
                notes       TEXT NOT NULL DEFAULT '',
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                remind_time TEXT NOT NULL,              -- HH:MM (24h)
                days        TEXT NOT NULL DEFAULT '',   -- '' = every day, else '0,1,2' Mon=0
                enabled     INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_date ON tasks (task_date);
            """
        )


init_db()


# ---------------------------------------------------------------- models

CATEGORIES = ["LeetCode", "Project", "Course", "Behavioral", "Writing", "Applications", "Other"]


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: str = "Other"
    task_date: Optional[str] = None  # defaults to today
    planned_min: int = Field(default=0, ge=0, le=1440)
    notes: str = ""


class TaskPatch(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    task_date: Optional[str] = None
    planned_min: Optional[int] = Field(default=None, ge=0, le=1440)
    done: Optional[bool] = None
    notes: Optional[str] = None


class ReminderIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    remind_time: str = Field(pattern=r"^\d{2}:\d{2}$")  # HH:MM
    days: str = ""  # comma-separated weekday numbers, Mon=0; empty = daily


def row_to_task(r: sqlite3.Row) -> dict:
    d = dict(r)
    d["done"] = bool(d["done"])
    return d


# ---------------------------------------------------------------- tasks

@app.get("/api/categories")
def get_categories():
    return CATEGORIES


@app.get("/api/tasks")
def list_tasks(day: Optional[str] = None):
    """Tasks for a given day (YYYY-MM-DD). Defaults to today."""
    day = day or date.today().isoformat()
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE task_date = ? ORDER BY done, id", (day,)
        ).fetchall()
    return {"date": day, "tasks": [row_to_task(r) for r in rows]}


@app.post("/api/tasks", status_code=201)
def create_task(task: TaskIn):
    if task.category not in CATEGORIES:
        raise HTTPException(400, f"category must be one of {CATEGORIES}")
    task_date = task.task_date or date.today().isoformat()
    try:
        date.fromisoformat(task_date)
    except ValueError:
        raise HTTPException(400, "task_date must be YYYY-MM-DD")
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, category, task_date, planned_min, notes) VALUES (?,?,?,?,?)",
            (task.title.strip(), task.category, task_date, task.planned_min, task.notes),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_task(row)


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, patch: TaskPatch):
    fields = patch.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(400, "nothing to update")
    if "category" in fields and fields["category"] not in CATEGORIES:
        raise HTTPException(400, f"category must be one of {CATEGORIES}")
    if "done" in fields:
        fields["done"] = int(fields["done"])
    sets = ", ".join(f"{k} = ?" for k in fields)
    with db() as conn:
        cur = conn.execute(
            f"UPDATE tasks SET {sets} WHERE id = ?", (*fields.values(), task_id)
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "task not found")
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row_to_task(row)


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with db() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "task not found")


# ---------------------------------------------------------------- reminders

@app.get("/api/reminders")
def list_reminders():
    with db() as conn:
        rows = conn.execute("SELECT * FROM reminders ORDER BY remind_time").fetchall()
    return [dict(r) for r in rows]


@app.post("/api/reminders", status_code=201)
def create_reminder(rem: ReminderIn):
    hh, mm = rem.remind_time.split(":")
    if not (0 <= int(hh) <= 23 and 0 <= int(mm) <= 59):
        raise HTTPException(400, "remind_time must be a valid HH:MM")
    if rem.days:
        try:
            nums = [int(x) for x in rem.days.split(",")]
            assert all(0 <= n <= 6 for n in nums)
        except (ValueError, AssertionError):
            raise HTTPException(400, "days must be comma-separated 0-6 (Mon=0)")
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO reminders (title, remind_time, days) VALUES (?,?,?)",
            (rem.title.strip(), rem.remind_time, rem.days),
        )
        row = conn.execute("SELECT * FROM reminders WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


@app.patch("/api/reminders/{rem_id}/toggle")
def toggle_reminder(rem_id: int):
    with db() as conn:
        cur = conn.execute(
            "UPDATE reminders SET enabled = 1 - enabled WHERE id = ?", (rem_id,)
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "reminder not found")
        row = conn.execute("SELECT * FROM reminders WHERE id = ?", (rem_id,)).fetchone()
    return dict(row)


@app.delete("/api/reminders/{rem_id}", status_code=204)
def delete_reminder(rem_id: int):
    with db() as conn:
        cur = conn.execute("DELETE FROM reminders WHERE id = ?", (rem_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "reminder not found")


# ---------------------------------------------------------------- stats

@app.get("/api/stats")
def stats():
    """Current streak, today's totals, and a 12-week completion heatmap."""
    today = date.today()
    with db() as conn:
        # days that have at least one completed task
        rows = conn.execute(
            "SELECT task_date, COUNT(*) AS done_count, SUM(planned_min) AS minutes "
            "FROM tasks WHERE done = 1 GROUP BY task_date"
        ).fetchall()
        done_days = {r["task_date"]: dict(r) for r in rows}

        today_row = conn.execute(
            "SELECT COUNT(*) AS total, "
            "SUM(done) AS done, "
            "SUM(CASE WHEN done = 1 THEN planned_min ELSE 0 END) AS minutes_done "
            "FROM tasks WHERE task_date = ?",
            (today.isoformat(),),
        ).fetchone()

    # streak: consecutive days ending today (or yesterday, so a morning
    # visit before finishing anything doesn't show a broken streak)
    streak = 0
    cursor = today
    if today.isoformat() not in done_days:
        cursor = today - timedelta(days=1)
    while cursor.isoformat() in done_days:
        streak += 1
        cursor -= timedelta(days=1)

    # heatmap: last 84 days (12 weeks), oldest first
    heatmap = []
    for i in range(83, -1, -1):
        d = today - timedelta(days=i)
        info = done_days.get(d.isoformat())
        heatmap.append(
            {"date": d.isoformat(), "count": info["done_count"] if info else 0}
        )

    best = 0
    run = 0
    d = today - timedelta(days=365)
    while d <= today:
        if d.isoformat() in done_days:
            run += 1
            best = max(best, run)
        else:
            run = 0
        d += timedelta(days=1)

    return {
        "streak": streak,
        "best_streak": best,
        "today": {
            "total": today_row["total"] or 0,
            "done": today_row["done"] or 0,
            "minutes_done": today_row["minutes_done"] or 0,
        },
        "heatmap": heatmap,
    }


# ---------------------------------------------------------------- settings

class SettingsIn(BaseModel):
    github_username: Optional[str] = None
    leetcode_username: Optional[str] = None


def read_settings() -> dict:
    with db() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    values = {r["key"]: r["value"] for r in rows}
    return {
        "github_username": values.get("github_username") or None,
        "leetcode_username": values.get("leetcode_username") or None,
    }


@app.get("/api/settings")
def get_settings():
    return read_settings()


@app.put("/api/settings")
def update_settings(patch: SettingsIn):
    fields = patch.model_dump(exclude_unset=True)
    with db() as conn:
        for key, value in fields.items():
            value = (value or "").strip()
            if value:
                conn.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, value),
                )
            else:
                conn.execute("DELETE FROM settings WHERE key = ?", (key,))
    return read_settings()


# ---------------------------------------------------------------- external streaks
#
# GitHub and LeetCode don't expose an official "current streak" endpoint, so
# these use community/public APIs (no auth token required) and derive the
# streak the same way /api/stats does for our own tasks. Results are cached
# briefly in-process since these are third-party services we don't want to
# hammer on every page load.

_STREAK_CACHE_TTL = 300  # seconds
_streak_cache: dict[str, tuple[float, dict]] = {}


def _cache_get(key: str) -> Optional[dict]:
    hit = _streak_cache.get(key)
    if hit and time.time() - hit[0] < _STREAK_CACHE_TTL:
        return hit[1]
    return None


def _cache_set(key: str, value: dict) -> None:
    _streak_cache[key] = (time.time(), value)


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
                contributions[day["date"]] = {"count": day["count"], "level": day.get("level", 0)}

    if not contributions:
        raise HTTPException(502, "couldn't reach GitHub contributions API")

    _cache_set(f"gh-raw:{username}", contributions)
    return contributions


async def fetch_github_streak(username: str) -> dict:
    cached = _cache_get(f"gh:{username}")
    if cached is not None:
        return cached

    contributions = await _fetch_github_contributions(username)
    today = date.today()
    streak = 0
    cursor = today
    if contributions.get(today.isoformat(), {}).get("count", 0) == 0:
        cursor = today - timedelta(days=1)
    while contributions.get(cursor.isoformat(), {}).get("count", 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)

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
        daily.append({"date": d.isoformat(), "count": info.get("count", 0), "level": info.get("level", 0)})
    return {"username": username, "days": daily, "total": sum(d["count"] for d in daily)}


async def fetch_leetcode_streak(username: str) -> dict:
    # LeetCode's own userCalendar.streak field is *not* "consecutive days ending
    # today/yesterday" — it can report a nonzero streak for a run that ended weeks
    # ago (verified against real profiles). So the streak is derived here from the
    # submission calendar the same way /api/stats derives it for our own tasks and
    # fetch_github_streak derives it for GitHub; only total_active_days (a simple
    # cumulative counter) is trusted straight from LeetCode.
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
    today = date.today()
    streak = 0
    cursor = today
    if submissions.get(today.isoformat(), 0) == 0:
        cursor = today - timedelta(days=1)
    while submissions.get(cursor.isoformat(), 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)

    result = {
        "username": username,
        "streak": streak,
        "total_active_days": total_active_days,
    }
    _cache_set(f"lc:{username}", result)
    return result


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


@app.get("/api/github-streak")
async def github_streak():
    username = read_settings()["github_username"]
    if not username:
        return {"configured": False}
    try:
        result = await fetch_github_streak(username)
    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(502, "GitHub streak lookup failed")
    return {"configured": True, **result}


@app.get("/api/github-activity")
async def github_activity(days: int = 30):
    if not (1 <= days <= 90):
        raise HTTPException(400, "days must be between 1 and 90")
    username = read_settings()["github_username"]
    if not username:
        return {"configured": False}
    try:
        result = await fetch_github_activity(username, days=days)
    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(502, "GitHub activity lookup failed")
    return {"configured": True, **result}


@app.get("/api/leetcode-streak")
async def leetcode_streak():
    username = read_settings()["leetcode_username"]
    if not username:
        return {"configured": False}
    try:
        result = await fetch_leetcode_streak(username)
    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(502, "LeetCode streak lookup failed")
    return {"configured": True, **result}


@app.get("/api/leetcode-activity")
async def leetcode_activity(days: int = 30):
    if not (1 <= days <= 90):
        raise HTTPException(400, "days must be between 1 and 90")
    username = read_settings()["leetcode_username"]
    if not username:
        return {"configured": False}
    try:
        result = await fetch_leetcode_activity(username, days=days)
    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(502, "LeetCode activity lookup failed")
    return {"configured": True, **result}


# ---------------------------------------------------------------- health

@app.get("/healthz")
def healthz():
    return {"status": "ok"}


# ---------------------------------------------------------------- frontend

@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
