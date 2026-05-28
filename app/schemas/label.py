from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RiskLabelCreate(BaseModel):
    risk_level: int = Field(ge=0, le=2)
    label_source: str = Field(min_length=3, max_length=80)
    label_note: str | None = Field(default=None, max_length=255)


class RiskLabelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entry_id: int
    risk_level: int
    label_source: str
    label_note: str | None
    created_at: datetime