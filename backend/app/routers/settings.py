"""Get/set the configured GitHub and LeetCode usernames."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.settings import SettingsIn, SettingsOut
from app.services.settings import read_settings, write_settings

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    return read_settings(db)


@router.put("/settings", response_model=SettingsOut)
def update_settings(patch: SettingsIn, db: Session = Depends(get_db)):
    return write_settings(db, patch.model_dump(exclude_unset=True))
