"""Task CRUD and the category list."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import CATEGORIES
from app.db.base import get_db
from app.db.models import Task
from app.schemas.task import TaskIn, TaskListOut, TaskOut, TaskPatch

router = APIRouter(tags=["tasks"])


@router.get("/categories", response_model=list[str])
def get_categories():
    return CATEGORIES


@router.get("/tasks", response_model=TaskListOut)
def list_tasks(day: str | None = None, db: Session = Depends(get_db)):
    """Tasks for a given day (YYYY-MM-DD). Defaults to today."""
    day = day or date.today().isoformat()
    tasks = db.execute(
        select(Task).where(Task.task_date == day).order_by(Task.done, Task.id)
    ).scalars().all()
    return {"date": day, "tasks": tasks}


@router.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(task: TaskIn, db: Session = Depends(get_db)):
    if task.category not in CATEGORIES:
        raise HTTPException(400, f"category must be one of {CATEGORIES}")
    task_date = task.task_date or date.today().isoformat()
    try:
        date.fromisoformat(task_date)
    except ValueError:
        raise HTTPException(400, "task_date must be YYYY-MM-DD")

    row = Task(
        title=task.title.strip(),
        category=task.category,
        task_date=task_date,
        planned_min=task.planned_min,
        notes=task.notes,
    )
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, patch: TaskPatch, db: Session = Depends(get_db)):
    fields = patch.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(400, "nothing to update")
    if "category" in fields and fields["category"] not in CATEGORIES:
        raise HTTPException(400, f"category must be one of {CATEGORIES}")

    row = db.get(Task, task_id)
    if row is None:
        raise HTTPException(404, "task not found")
    for key, value in fields.items():
        setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    row = db.get(Task, task_id)
    if row is None:
        raise HTTPException(404, "task not found")
    db.delete(row)
