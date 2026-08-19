"""Settings request/response schemas."""

from typing import Optional

from pydantic import BaseModel


class SettingsIn(BaseModel):
    github_username: Optional[str] = None
    leetcode_username: Optional[str] = None


class SettingsOut(BaseModel):
    github_username: Optional[str] = None
    leetcode_username: Optional[str] = None
