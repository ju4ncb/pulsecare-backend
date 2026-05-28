from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.wellbeing import WellbeingEntry
from app.schemas.label import RiskLabelCreate, RiskLabelRead
from app.schemas.wellbeing import ModelInputSnapshotRead, WellbeingEntryCreate, WellbeingEntryRead
from app.services.label_service import create_risk_label
from app.services.wellbeing_service import build_and_store_model_input, create_wellbeing_entry

router = APIRouter(prefix="/wellbeing", tags=["wellbeing"])


@router.post("/entries", response_model=WellbeingEntryRead, status_code=status.HTTP_201_CREATED)
def register_wellbeing_entry(
    payload: WellbeingEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WellbeingEntry:
    return create_wellbeing_entry(db, current_user, payload)


@router.post("/entries/{entry_id}/model-input", response_model=ModelInputSnapshotRead, status_code=status.HTTP_201_CREATED)
def create_model_input_snapshot(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    entry = db.query(WellbeingEntry).filter(WellbeingEntry.id == entry_id, WellbeingEntry.user_id == current_user.id).first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado")

    if entry.model_input is not None:
        return entry.model_input

    return build_and_store_model_input(db, entry)


@router.get("/entries/{entry_id}", response_model=WellbeingEntryRead)
def read_wellbeing_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WellbeingEntry:
    entry = db.query(WellbeingEntry).filter(WellbeingEntry.id == entry_id, WellbeingEntry.user_id == current_user.id).first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado")
    return entry


@router.get("/entries", response_model=List[WellbeingEntryRead])
def list_wellbeing_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WellbeingEntry]:
    entries = (
        db.query(WellbeingEntry)
        .filter(WellbeingEntry.user_id == current_user.id)
        .order_by(WellbeingEntry.id.desc())
        .all()
    )
    return entries


@router.post("/entries/{entry_id}/label", response_model=RiskLabelRead, status_code=status.HTTP_201_CREATED)
def register_risk_label(
    entry_id: int,
    payload: RiskLabelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    entry = db.query(WellbeingEntry).filter(WellbeingEntry.id == entry_id, WellbeingEntry.user_id == current_user.id).first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado")

    try:
        return create_risk_label(db, entry_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc