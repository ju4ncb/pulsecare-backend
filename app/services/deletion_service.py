from sqlalchemy.orm import Session

from app.models.user import User
from app.models.wellbeing import ModelInputSnapshot, RiskLabel, WellbeingEntry


def delete_wellbeing_entry(db: Session, entry_id: int) -> bool:
    entry = db.query(WellbeingEntry).filter(WellbeingEntry.id == entry_id).first()
    if entry is None:
        return False

    snapshot = db.query(ModelInputSnapshot).filter(ModelInputSnapshot.entry_id == entry_id).first()
    if snapshot is not None:
        db.delete(snapshot)

    label = db.query(RiskLabel).filter(RiskLabel.entry_id == entry_id).first()
    if label is not None:
        db.delete(label)

    db.delete(entry)
    return True


def delete_user_with_dependents(db: Session, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return False

    entries = db.query(WellbeingEntry).filter(WellbeingEntry.user_id == user_id).all()
    for entry in entries:
        snapshot = db.query(ModelInputSnapshot).filter(ModelInputSnapshot.entry_id == entry.id).first()
        if snapshot is not None:
            db.delete(snapshot)

        label = db.query(RiskLabel).filter(RiskLabel.entry_id == entry.id).first()
        if label is not None:
            db.delete(label)

        db.delete(entry)

    db.delete(user)
    return True