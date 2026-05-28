from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WellbeingEntryBase(BaseModel):
    # Fields that are stored and/or derived for the model snapshot
    mood_score: int = Field(ge=1, le=5)
    sleep_hours: float = Field(ge=0, le=24)
    academic_load: int = Field(ge=1, le=5)
    energy_fatigue: int = Field(ge=1, le=5)
    registration_regular: int = Field(ge=1, le=5)
    recent_change_vs_average: float = Field(ge=-5, le=5)
    trend_7d: float = Field(ge=-5, le=5)
    trend_14d: float = Field(ge=-5, le=5)


# Input payload expected from the frontend when creating a wellbeing entry.
# The backend computes `registration_regular`, `recent_change_vs_average`,
# `trend_7d` and `trend_14d` automatically, so they are not part of the
# client payload.
class WellbeingEntryCreate(BaseModel):
    mood_score: int = Field(ge=1, le=5)
    sleep_hours: float = Field(ge=0, le=24)
    academic_load: int = Field(ge=1, le=5)
    energy_fatigue: int = Field(ge=1, le=5)
    is_synthetic: bool = False
    recorded_at: datetime | None = None


class WellbeingEntryRead(WellbeingEntryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    is_synthetic: bool
    recorded_at: datetime


class ModelInputSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entry_id: int
    mood_inverse: float
    sleep_deficit: float
    academic_pressure: float
    energy_risk: float
    registration_gap: float
    personal_delta: float
    trend_7d: float
    trend_14d: float
    created_at: datetime