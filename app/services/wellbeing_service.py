from sqlalchemy.orm import Session

from app.ai.feature_engineering import build_model_input_snapshot
from app.models.user import User
from app.models.wellbeing import ModelInputSnapshot, WellbeingEntry
from app.schemas.wellbeing import WellbeingEntryCreate


def create_wellbeing_entry(db: Session, user: User, payload: WellbeingEntryCreate) -> WellbeingEntry:
    entry = WellbeingEntry(user_id=user.id, **payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def build_and_store_model_input(db: Session, entry: WellbeingEntry) -> ModelInputSnapshot:
    snapshot = build_model_input_snapshot(entry)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot