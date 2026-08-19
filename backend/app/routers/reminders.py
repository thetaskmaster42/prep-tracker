"""Reminder CRUD. Reminders are stored here; they fire client-side while the tab is open."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import Reminder
from app.schemas.reminder import ReminderIn, ReminderOut

router = APIRouter(tags=["reminders"])


@router.get("/reminders", response_model=list[ReminderOut])
def list_reminders(db: Session = Depends(get_db)):
    return db.execute(select(Reminder).order_by(Reminder.remind_time)).scalars().all()


@router.post("/reminders", response_model=ReminderOut, status_code=201)
def create_reminder(rem: ReminderIn, db: Session = Depends(get_db)):
    hh, mm = rem.remind_time.split(":")
    if not (0 <= int(hh) <= 23 and 0 <= int(mm) <= 59):
        raise HTTPException(400, "remind_time must be a valid HH:MM")
    if rem.days:
        try:
            nums = [int(x) for x in rem.days.split(",")]
            assert all(0 <= n <= 6 for n in nums)
        except (ValueError, AssertionError):
            raise HTTPException(400, "days must be comma-separated 0-6 (Mon=0)")

    row = Reminder(title=rem.title.strip(), remind_time=rem.remind_time, days=rem.days)
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


@router.patch("/reminders/{rem_id}/toggle", response_model=ReminderOut)
def toggle_reminder(rem_id: int, db: Session = Depends(get_db)):
    row = db.get(Reminder, rem_id)
    if row is None:
        raise HTTPException(404, "reminder not found")
    row.enabled = 1 - row.enabled
    db.flush()
    db.refresh(row)
    return row


@router.delete("/reminders/{rem_id}", status_code=204)
def delete_reminder(rem_id: int, db: Session = Depends(get_db)):
    row = db.get(Reminder, rem_id)
    if row is None:
        raise HTTPException(404, "reminder not found")
    db.delete(row)
