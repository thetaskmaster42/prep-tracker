import json as json_module
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text

from app.db.base import SessionLocal
from app.services import streaks as streaks_module

API = "/api/v1"


def iso(d: date) -> str:
    return d.isoformat()


def exec_sql(sql: str) -> None:
    """Run a raw statement against the test DB (used to set up streak scenarios)."""
    with SessionLocal() as session:
        session.execute(text(sql))
        session.commit()


# ---------------------------------------------------------------- health / categories

def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_categories(client):
    resp = client.get(f"{API}/categories")
    assert resp.status_code == 200
    assert "LeetCode" in resp.json()


# ---------------------------------------------------------------- tasks

def test_create_and_list_task(client):
    resp = client.post(f"{API}/tasks", json={"title": "2 mediums", "category": "LeetCode", "planned_min": 45})
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "2 mediums"
    assert body["category"] == "LeetCode"
    assert body["done"] is False

    today = date.today().isoformat()
    resp = client.get(f"{API}/tasks?day={today}")
    assert resp.status_code == 200
    assert resp.json()["date"] == today
    assert len(resp.json()["tasks"]) == 1


def test_create_task_rejects_bad_category(client):
    resp = client.post(f"{API}/tasks", json={"title": "x", "category": "Not-A-Category"})
    assert resp.status_code == 400


def test_create_task_rejects_bad_date(client):
    resp = client.post(f"{API}/tasks", json={"title": "x", "task_date": "not-a-date"})
    assert resp.status_code == 400


def test_patch_task_toggle_done(client):
    created = client.post(f"{API}/tasks", json={"title": "x"}).json()
    resp = client.patch(f"{API}/tasks/{created['id']}", json={"done": True})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_patch_task_requires_fields(client):
    created = client.post(f"{API}/tasks", json={"title": "x"}).json()
    resp = client.patch(f"{API}/tasks/{created['id']}", json={})
    assert resp.status_code == 400


def test_patch_missing_task_404(client):
    resp = client.patch(f"{API}/tasks/999999", json={"done": True})
    assert resp.status_code == 404


def test_delete_task(client):
    created = client.post(f"{API}/tasks", json={"title": "x"}).json()
    resp = client.delete(f"{API}/tasks/{created['id']}")
    assert resp.status_code == 204
    resp = client.delete(f"{API}/tasks/{created['id']}")
    assert resp.status_code == 404


# ---------------------------------------------------------------- reminders

def test_create_list_toggle_delete_reminder(client):
    resp = client.post(f"{API}/reminders", json={"title": "LeetCode hour", "remind_time": "19:00", "days": "0,2,4"})
    assert resp.status_code == 201
    rem = resp.json()
    assert rem["enabled"] == 1

    resp = client.get(f"{API}/reminders")
    assert len(resp.json()) == 1

    resp = client.patch(f"{API}/reminders/{rem['id']}/toggle")
    assert resp.json()["enabled"] == 0

    resp = client.delete(f"{API}/reminders/{rem['id']}")
    assert resp.status_code == 204


def test_reminder_rejects_bad_time_format(client):
    resp = client.post(f"{API}/reminders", json={"title": "x", "remind_time": "7pm"})
    assert resp.status_code == 422  # fails the HH:MM pattern before reaching the handler


def test_reminder_rejects_out_of_range_time(client):
    resp = client.post(f"{API}/reminders", json={"title": "x", "remind_time": "25:99"})
    assert resp.status_code == 400  # matches HH:MM pattern but fails the handler's range check


def test_reminder_rejects_bad_days(client):
    resp = client.post(f"{API}/reminders", json={"title": "x", "remind_time": "09:00", "days": "9"})
    assert resp.status_code == 400


def test_toggle_missing_reminder_404(client):
    resp = client.patch(f"{API}/reminders/999999/toggle")
    assert resp.status_code == 404


# ---------------------------------------------------------------- stats / streak

def test_stats_empty(client):
    resp = client.get(f"{API}/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["streak"] == 0
    assert body["best_streak"] == 0
    assert len(body["heatmap"]) == 84


def test_stats_streak_counts_consecutive_done_days(client):
    today = date.today()
    # done tasks for today, yesterday, and the day before -> streak of 3
    for offset in (0, 1, 2):
        client.post(f"{API}/tasks", json={"title": f"t{offset}", "task_date": iso(today - timedelta(days=offset))})
    exec_sql("UPDATE tasks SET done = 1")

    resp = client.get(f"{API}/stats")
    body = resp.json()
    assert body["streak"] == 3
    assert body["best_streak"] == 3
    assert body["today"]["done"] == 1
    assert body["today"]["total"] == 1


def test_stats_streak_survives_missing_today(client):
    """A morning visit before finishing anything shouldn't zero out yesterday's streak."""
    yesterday = date.today() - timedelta(days=1)
    client.post(f"{API}/tasks", json={"title": "t", "task_date": iso(yesterday)})
    exec_sql("UPDATE tasks SET done = 1")

    resp = client.get(f"{API}/stats")
    assert resp.json()["streak"] == 1


def test_stats_streak_broken_by_gap(client):
    today = date.today()
    client.post(f"{API}/tasks", json={"title": "t", "task_date": iso(today)})
    client.post(f"{API}/tasks", json={"title": "t2", "task_date": iso(today - timedelta(days=2))})
    exec_sql("UPDATE tasks SET done = 1")

    resp = client.get(f"{API}/stats")
    assert resp.json()["streak"] == 1


# ---------------------------------------------------------------- settings

def test_settings_default_unset(client):
    resp = client.get(f"{API}/settings")
    assert resp.json() == {"github_username": None, "leetcode_username": None}


def test_settings_put_and_get(client):
    resp = client.put(f"{API}/settings", json={"github_username": "octocat", "leetcode_username": "coder"})
    assert resp.status_code == 200
    assert resp.json() == {"github_username": "octocat", "leetcode_username": "coder"}

    resp = client.get(f"{API}/settings")
    assert resp.json() == {"github_username": "octocat", "leetcode_username": "coder"}


def test_settings_put_empty_string_clears_value(client):
    client.put(f"{API}/settings", json={"github_username": "octocat"})
    client.put(f"{API}/settings", json={"github_username": ""})
    resp = client.get(f"{API}/settings")
    assert resp.json()["github_username"] is None


def test_settings_put_partial_leaves_other_field(client):
    client.put(f"{API}/settings", json={"github_username": "octocat", "leetcode_username": "coder"})
    client.put(f"{API}/settings", json={"github_username": "new-name"})
    resp = client.get(f"{API}/settings")
    assert resp.json() == {"github_username": "new-name", "leetcode_username": "coder"}


# ---------------------------------------------------------------- external streaks

def test_github_streak_unconfigured(client):
    resp = client.get(f"{API}/github-streak")
    assert resp.status_code == 200
    assert resp.json() == {"configured": False}


def test_leetcode_streak_unconfigured(client):
    resp = client.get(f"{API}/leetcode-streak")
    assert resp.status_code == 200
    assert resp.json() == {"configured": False}


def test_github_streak_configured(client, monkeypatch):
    async def fake_fetch(username):
        assert username == "octocat"
        return {"username": username, "streak": 7}

    monkeypatch.setattr(streaks_module, "fetch_github_streak", fake_fetch)
    client.put(f"{API}/settings", json={"github_username": "octocat"})

    resp = client.get(f"{API}/github-streak")
    assert resp.status_code == 200
    assert resp.json() == {"configured": True, "username": "octocat", "streak": 7}


def test_leetcode_streak_configured(client, monkeypatch):
    async def fake_fetch(username):
        return {"username": username, "streak": 12, "total_active_days": 300}

    monkeypatch.setattr(streaks_module, "fetch_leetcode_streak", fake_fetch)
    client.put(f"{API}/settings", json={"leetcode_username": "coder"})

    resp = client.get(f"{API}/leetcode-streak")
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is True
    assert body["streak"] == 12
    assert body["total_active_days"] == 300


def test_github_streak_propagates_upstream_failure(client, monkeypatch):
    from fastapi import HTTPException

    async def fake_fetch(username):
        raise HTTPException(404, f"GitHub user '{username}' not found")

    monkeypatch.setattr(streaks_module, "fetch_github_streak", fake_fetch)
    client.put(f"{API}/settings", json={"github_username": "nobody"})

    resp = client.get(f"{API}/github-streak")
    assert resp.status_code == 404


def test_github_activity_unconfigured(client):
    resp = client.get(f"{API}/github-activity")
    assert resp.status_code == 200
    assert resp.json() == {"configured": False}


def test_github_activity_configured(client, monkeypatch):
    async def fake_fetch(username, days=30):
        assert username == "octocat"
        assert days == 30
        return {
            "username": username,
            "days": [{"date": "2026-07-01", "count": 3, "level": 2}],
            "total": 3,
        }

    monkeypatch.setattr(streaks_module, "fetch_github_activity", fake_fetch)
    client.put(f"{API}/settings", json={"github_username": "octocat"})

    resp = client.get(f"{API}/github-activity")
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is True
    assert body["total"] == 3
    assert body["days"] == [{"date": "2026-07-01", "count": 3, "level": 2}]


def test_github_activity_rejects_out_of_range_days(client):
    resp = client.get(f"{API}/github-activity?days=200")
    assert resp.status_code == 400


def test_fetch_github_activity_shapes_30_day_window(monkeypatch):
    import asyncio

    async def fake_contributions(username):
        today = date.today()
        return {
            (today - timedelta(days=1)).isoformat(): {"count": 2, "level": 1},
            (today - timedelta(days=40)).isoformat(): {"count": 9, "level": 4},  # out of window
        }

    monkeypatch.setattr(streaks_module, "_fetch_github_contributions", fake_contributions)

    result = asyncio.run(streaks_module.fetch_github_activity("octocat", days=30))
    assert len(result["days"]) == 30
    assert result["days"][-1]["date"] == date.today().isoformat()
    assert result["days"][-2]["count"] == 2
    assert result["days"][-2]["level"] == 1
    assert result["total"] == 2  # the 40-day-old entry must not leak into a 30-day window


# ---------------------------------------------------------------- leetcode activity

def test_leetcode_activity_unconfigured(client):
    resp = client.get(f"{API}/leetcode-activity")
    assert resp.status_code == 200
    assert resp.json() == {"configured": False}


def test_leetcode_activity_configured(client, monkeypatch):
    async def fake_fetch(username, days=30):
        assert username == "coder"
        assert days == 30
        return {
            "username": username,
            "days": [{"date": "2026-07-01", "count": 5, "level": 3}],
            "total": 5,
        }

    monkeypatch.setattr(streaks_module, "fetch_leetcode_activity", fake_fetch)
    client.put(f"{API}/settings", json={"leetcode_username": "coder"})

    resp = client.get(f"{API}/leetcode-activity")
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is True
    assert body["total"] == 5
    assert body["days"] == [{"date": "2026-07-01", "count": 5, "level": 3}]


def test_leetcode_activity_rejects_out_of_range_days(client):
    resp = client.get(f"{API}/leetcode-activity?days=0")
    assert resp.status_code == 400


def test_leetcode_level_buckets():
    assert streaks_module._leetcode_level(0) == 0
    assert streaks_module._leetcode_level(1) == 1
    assert streaks_module._leetcode_level(3) == 2
    assert streaks_module._leetcode_level(6) == 3
    assert streaks_module._leetcode_level(7) == 4
    assert streaks_module._leetcode_level(50) == 4


def test_fetch_leetcode_activity_shapes_30_day_window(monkeypatch):
    import asyncio

    async def fake_submissions(username):
        today = date.today()
        return {
            (today - timedelta(days=1)).isoformat(): 4,
            (today - timedelta(days=40)).isoformat(): 9,  # out of window
        }

    monkeypatch.setattr(streaks_module, "_fetch_leetcode_submissions", fake_submissions)

    result = asyncio.run(streaks_module.fetch_leetcode_activity("coder", days=30))
    assert len(result["days"]) == 30
    assert result["days"][-1]["date"] == date.today().isoformat()
    assert result["days"][-2]["count"] == 4
    assert result["days"][-2]["level"] == 3
    assert result["total"] == 4  # the 40-day-old entry must not leak into a 30-day window


def test_fetch_leetcode_submissions_parses_calendar_and_merges_years(monkeypatch):
    import asyncio

    class FakeResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class FakeAsyncClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json, headers):
            year = json["variables"]["year"]
            ts = int(datetime(year, 6, 1, tzinfo=timezone.utc).timestamp())
            calendar = json_module.dumps({str(ts): 2})
            return FakeResponse(200, {
                "data": {"matchedUser": {"userCalendar": {"submissionCalendar": calendar}}}
            })

    monkeypatch.setattr(streaks_module.httpx, "AsyncClient", FakeAsyncClient)

    result = asyncio.run(streaks_module._fetch_leetcode_submissions("coder"))
    today = date.today()
    assert result.get(date(today.year, 6, 1).isoformat()) == 2
    assert result.get(date(today.year - 1, 6, 1).isoformat()) == 2


def test_fetch_leetcode_streak_ignores_stale_api_streak_field(monkeypatch):
    """LeetCode's own userCalendar.streak can report a nonzero streak for a run
    that ended weeks ago (observed on real profiles) — the streak must be derived
    from the submission calendar instead, so a gap before today means streak 0."""
    import asyncio

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"data": {"matchedUser": {"userCalendar": {"totalActiveDays": 17}}}}

    class FakeAsyncClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **kw):
            return FakeResponse()

    monkeypatch.setattr(streaks_module.httpx, "AsyncClient", FakeAsyncClient)

    async def fake_submissions(username):
        stale_day = date.today() - timedelta(days=21)
        return {stale_day.isoformat(): 4}  # a real streak, but weeks in the past

    monkeypatch.setattr(streaks_module, "_fetch_leetcode_submissions", fake_submissions)

    result = asyncio.run(streaks_module.fetch_leetcode_streak("votrubac"))
    assert result["streak"] == 0
    assert result["total_active_days"] == 17


def test_fetch_leetcode_streak_counts_consecutive_days_ending_yesterday(monkeypatch):
    import asyncio

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"data": {"matchedUser": {"userCalendar": {"totalActiveDays": 5}}}}

    class FakeAsyncClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **kw):
            return FakeResponse()

    monkeypatch.setattr(streaks_module.httpx, "AsyncClient", FakeAsyncClient)

    async def fake_submissions(username):
        today = date.today()
        return {
            (today - timedelta(days=1)).isoformat(): 2,
            (today - timedelta(days=2)).isoformat(): 1,
        }

    monkeypatch.setattr(streaks_module, "_fetch_leetcode_submissions", fake_submissions)

    result = asyncio.run(streaks_module.fetch_leetcode_streak("coder"))
    assert result["streak"] == 2


def test_fetch_leetcode_submissions_raises_404_for_missing_user(monkeypatch):
    import asyncio

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"data": {"matchedUser": None}}

    class FakeAsyncClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **kw):
            return FakeResponse()

    monkeypatch.setattr(streaks_module.httpx, "AsyncClient", FakeAsyncClient)

    from fastapi import HTTPException
    try:
        asyncio.run(streaks_module._fetch_leetcode_submissions("nobody"))
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 404
