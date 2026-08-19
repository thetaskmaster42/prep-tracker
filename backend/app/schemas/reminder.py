"""Reminder request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReminderIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    remind_time: str = Field(pattern=r"^\d{2}:\d{2}$")  # HH:MM
    days: str = ""  # comma-separated weekday numbers, Mon=0; empty = daily


class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    remind_time: str
    days: str
    enabled: int
    created_at: datetime
