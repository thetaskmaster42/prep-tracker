"""Task request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    task_date: str
    planned_min: int
    done: bool
    notes: str
    created_at: datetime


class TaskListOut(BaseModel):
    date: str
    tasks: list[TaskOut]
