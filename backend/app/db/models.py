"""SQLAlchemy ORM models.

Column semantics mirror the original schema, but defaults use dialect-portable constructs
(``func.now()``, ``false()``) so the same models run on SQLite and Postgres.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(
        String, nullable=False, default="Other", server_default="Other"
    )
    task_date: Mapped[str] = mapped_column(String, nullable=False)  # YYYY-MM-DD
    planned_min: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    done: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("idx_tasks_date", "task_date"),)


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    remind_time: Mapped[str] = mapped_column(String, nullable=False)  # HH:MM (24h)
    # '' = every day, else comma-separated weekday numbers with Mon=0 (e.g. '0,2,4').
    days: Mapped[str] = mapped_column(String, nullable=False, default="", server_default="")
    # Kept as an integer (0/1) rather than Boolean so the API response stays 1/0.
    enabled: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
