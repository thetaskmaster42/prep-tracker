"""Stats response schemas."""

from pydantic import BaseModel


class TodayOut(BaseModel):
    total: int
    done: int
    minutes_done: int


class HeatCell(BaseModel):
    date: str
    count: int


class StatsOut(BaseModel):
    streak: int
    best_streak: int
    today: TodayOut
    heatmap: list[HeatCell]
