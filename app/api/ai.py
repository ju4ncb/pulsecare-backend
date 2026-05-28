from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from app.ai import create_training_run, inspect_artifact, load_trained_model, predict_risk_probability, train_and_store_run, train_risk_classifier
from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.wellbeing import WellbeingEntry
from app.models.training_run import TrainingRun
from app.services.wellbeing_service import build_and_store_model_input
from app.schemas.ai import ArtifactInspectionRead, PredictionRead, TrainingResultRead, TrainingRunRead
from app.core.security import is_admin

router = APIRouter(prefix="/ai", tags=["ai"])


def _serialize_training_run(run: TrainingRun) -> TrainingRunRead:
    return TrainingRunRead(
        id=run.id,
        status=run.status,
        sample_count=run.sample_count,
        accuracy=run.accuracy,
        precision=run.precision,
        recall=run.recall,
        f1=run.f1,
        confusion_matrix_json=run.confusion_matrix_json,
        classification_report_json=run.classification_report_json,
        model_path=run.model_path,
        artifact_size_bytes=run.artifact_size_bytes,
        error_message=run.error_message,
    )


def _predict_entry(entry_id: int, db: Session, current_user: User) -> PredictionRead:
    entry = db.query(WellbeingEntry).filter(WellbeingEntry.id == entry_id).first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado")

    if entry.user_id != current_user.id and not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para consultar esta predicción")

    if entry.model_input is None:
        entry = build_and_store_model_input(db, entry)

    try:
        model = load_trained_model()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    probs = predict_risk_probability(entry.model_input, model)
    names = {0: "low", 1: "medium", 2: "high"}
    predicted = int(max(range(len(probs)), key=lambda i: probs[i]))
    prob_map = {i: float(p) for i, p in enumerate(probs)}

    return PredictionRead(predicted_label=predicted, predicted_label_name=names.get(predicted, "unknown"), probabilities=prob_map)

@router.post("/train", response_model=TrainingResultRead)
def train_model(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required to train model")

    result = train_risk_classifier(db)
    return TrainingResultRead(
        sample_count=result.sample_count,
        accuracy=result.accuracy,
        precision=result.precision,
        recall=result.recall,
        f1=result.f1,
        confusion_matrix=result.confusion_matrix,
        classification_report=result.classification_report,
    )


@router.post("/train/async", response_model=TrainingRunRead, status_code=status.HTTP_202_ACCEPTED)
def train_model_async(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required to train model")

    run = create_training_run(db)

    def _run_training(run_id: int) -> None:
        from app.core.database import SessionLocal

        local_db = SessionLocal()
        try:
            db_run = local_db.query(TrainingRun).filter(TrainingRun.id == run_id).first()
            if db_run is None:
                return
            train_and_store_run(local_db, db_run)
        finally:
            local_db.close()

    background_tasks.add_task(_run_training, run.id)
    return _serialize_training_run(run)


@router.get("/train/{run_id}", response_model=TrainingRunRead)
def get_training_run(run_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required to inspect training run")

    run = db.query(TrainingRun).filter(TrainingRun.id == run_id).first()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrenamiento no encontrado")

    return _serialize_training_run(run)


@router.get("/train", response_model=List[TrainingRunRead])
def list_training_runs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[TrainingRunRead]:
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required to inspect training runs")

    runs = db.query(TrainingRun).order_by(TrainingRun.id.desc()).all()
    return [_serialize_training_run(r) for r in runs]


@router.get("/predict/{entry_id}", response_model=PredictionRead)
def predict(entry_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _predict_entry(entry_id, db, current_user)


@router.post("/predict/{entry_id}", response_model=PredictionRead)
def predict_post(entry_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _predict_entry(entry_id, db, current_user)


@router.get("/validate", response_model=TrainingResultRead)
def validate_model(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required to validate model")

    # perform evaluation of the trained model on the supervised dataset
    from app.ai.training import load_supervised_dataset
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

    features, labels = load_supervised_dataset(db)
    if len(features) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No labeled data available for validation")

    try:
        model = load_trained_model()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    y_pred = model.predict(features)

    metrics = TrainingResultRead(
        sample_count=len(features),
        accuracy=float(accuracy_score(labels, y_pred)),
        precision=float(precision_score(labels, y_pred, average="weighted", zero_division=0)),
        recall=float(recall_score(labels, y_pred, average="weighted", zero_division=0)),
        f1=float(f1_score(labels, y_pred, average="weighted", zero_division=0)),
        confusion_matrix=confusion_matrix(labels, y_pred).tolist(),
        classification_report=classification_report(labels, y_pred, output_dict=True, zero_division=0),
    )

    return metrics


@router.get("/artifact", response_model=ArtifactInspectionRead)
def inspect_training_artifact(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required to inspect artifact")

    latest_run = db.query(TrainingRun).order_by(TrainingRun.id.desc()).first()
    artifact_info = inspect_artifact()
    latest_run_payload = None
    if latest_run is not None:
        latest_run_payload = _serialize_training_run(latest_run)

    return ArtifactInspectionRead(
        model_path=str(artifact_info["model_path"]),
        exists=bool(artifact_info["exists"]),
        size_bytes=artifact_info.get("size_bytes"),
        modified_at=artifact_info.get("modified_at"),
        latest_run=latest_run_payload,
    )