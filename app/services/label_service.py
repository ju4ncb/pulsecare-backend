from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.wellbeing import RiskLabel, WellbeingEntry
from app.schemas.label import RiskLabelCreate


def create_risk_label(db: Session, entry_id: int, payload: RiskLabelCreate) -> RiskLabel:
    entry = db.query(WellbeingEntry).filter(WellbeingEntry.id == entry_id).first()
    if entry is None:
        raise ValueError("Registro no encontrado")

    existing_label = db.query(RiskLabel).filter(RiskLabel.entry_id == entry_id).first()
    if existing_label is not None:
        existing_label.risk_level = payload.risk_level
        existing_label.label_source = payload.label_source
        existing_label.label_note = payload.label_note
        db.commit()
        db.refresh(existing_label)
        return existing_label

    label = RiskLabel(entry_id=entry_id, **payload.model_dump())
    db.add(label)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("No se pudo guardar la etiqueta") from exc

    db.refresh(label)
    return label