from typing import Dict, List
from pydantic import BaseModel


class TrainingResultRead(BaseModel):
    sample_count: int
    accuracy: float
    precision: float
    recall: float
    f1: float
    confusion_matrix: List[List[int]]
    classification_report: Dict


class PredictionRead(BaseModel):
    predicted_label: int
    predicted_label_name: str
    probabilities: Dict[int, float]


class TrainingRunRead(BaseModel):
    id: int
    status: str
    sample_count: int | None
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1: float | None
    confusion_matrix_json: str | None
    classification_report_json: str | None
    model_path: str | None
    artifact_size_bytes: int | None
    error_message: str | None


class ArtifactInspectionRead(BaseModel):
    model_path: str
    exists: bool
    size_bytes: int | None = None
    modified_at: str | None = None
    latest_run: TrainingRunRead | None = None
