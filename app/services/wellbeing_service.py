from datetime import datetime, timedelta
from statistics import mean
from typing import List

from sqlalchemy.orm import Session

from app.ai.feature_engineering import build_model_input_snapshot
from app.models.user import User
from app.models.wellbeing import ModelInputSnapshot, WellbeingEntry
from app.schemas.wellbeing import WellbeingEntryCreate
from app.core.database import Base


def _scale_registration(ratio: float) -> int:
    # Map a 0..1 ratio to 1..5 scale
    scaled = int(round(ratio * 4)) + 1
    return max(1, min(5, scaled))


def _compute_slope(values: List[float]) -> float:
    # Simple linear regression slope for x=0..n-1
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    mean_x = (n - 1) / 2
    mean_y = mean(values)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
    den = sum((x - mean_x) ** 2 for x in xs)
    if den == 0:
        return 0.0
    return num / den


def create_wellbeing_entry(db: Session, user: User, payload: WellbeingEntryCreate) -> WellbeingEntry:
    now = datetime.utcnow()
    created_at = payload.created_at or now

    # look back 30 days for registration regularity and average
    since_30 = created_at - timedelta(days=30)
    entries_30 = (
        db.query(WellbeingEntry)
        .filter(WellbeingEntry.user_id == user.id, WellbeingEntry.created_at >= since_30)
        .order_by(WellbeingEntry.created_at.asc())
        .all()
    )

    # days registered in last 30 days
    days = {e.created_at.date() for e in entries_30}
    days_registered = len(days)
    ratio = days_registered / 30.0
    registration_regular = _scale_registration(ratio)

    # recent change vs average (use mood_score as target for the delta)
    if entries_30:
        avg_mood = mean([e.mood_score for e in entries_30])
    else:
        avg_mood = payload.mood_score
    recent_change = float(payload.mood_score - avg_mood)

    # trend 7d and 14d: compute slope over mood_score
    def _fetch_values(days_back: int):
        since = created_at - timedelta(days=days_back)
        vals = [e.mood_score for e in db.query(WellbeingEntry).filter(WellbeingEntry.user_id == user.id, WellbeingEntry.created_at >= since).order_by(WellbeingEntry.created_at.asc()).all()]
        # include current value as the latest observation
        vals.append(payload.mood_score)
        return vals

    vals_7 = _fetch_values(7)
    vals_14 = _fetch_values(14)

    trend_7 = float(_compute_slope(vals_7))
    trend_14 = float(_compute_slope(vals_14))

    entry = WellbeingEntry(
        user_id=user.id,
        mood_score=payload.mood_score,
        sleep_hours=payload.sleep_hours,
        academic_load=payload.academic_load,
        energy_fatigue=payload.energy_fatigue,
        registration_regular=registration_regular,
        recent_change_vs_average=recent_change,
        trend_7d=trend_7,
        trend_14d=trend_14,
        is_synthetic=payload.is_synthetic,
        created_at=created_at,
    )

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


def create_wellbeing_entry_raw(db: Session, payload: dict) -> WellbeingEntry:
    # payload is a dict with all fields including user_id and derived fields
    entry = WellbeingEntry(
        user_id=payload.get("user_id"),
        mood_score=payload.get("mood_score"),
        sleep_hours=payload.get("sleep_hours"),
        academic_load=payload.get("academic_load"),
        energy_fatigue=payload.get("energy_fatigue"),
        registration_regular=payload.get("registration_regular"),
        recent_change_vs_average=payload.get("recent_change_vs_average"),
        trend_7d=payload.get("trend_7d"),
        trend_14d=payload.get("trend_14d"),
        is_synthetic=payload.get("is_synthetic", False),
        created_at=payload.get("created_at"),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry