"""Local task streak, today's totals, and the 12-week completion heatmap."""

from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.streaks import current_streak


def compute_stats(db: Session) -> dict:
    today = date.today()

    # Days that have at least one completed task.
    rows = db.execute(
        text(
            "SELECT task_date, COUNT(*) AS done_count, SUM(planned_min) AS minutes "
            "FROM tasks WHERE done = 1 GROUP BY task_date"
        )
    ).mappings().all()
    done_days = {r["task_date"]: dict(r) for r in rows}

    today_row = db.execute(
        text(
            "SELECT COUNT(*) AS total, "
            "SUM(done) AS done, "
            "SUM(CASE WHEN done = 1 THEN planned_min ELSE 0 END) AS minutes_done "
            "FROM tasks WHERE task_date = :day"
        ),
        {"day": today.isoformat()},
    ).mappings().one()

    streak = current_streak(lambda d: d.isoformat() in done_days, today)

    # Heatmap: last 84 days (12 weeks), oldest first.
    heatmap = []
    for i in range(83, -1, -1):
        d = today - timedelta(days=i)
        info = done_days.get(d.isoformat())
        heatmap.append({"date": d.isoformat(), "count": info["done_count"] if info else 0})

    # Best streak across the last year.
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
