from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pickle
import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.exceptions import NotFittedError
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from app.ai.feature_engineering import to_feature_vector
from app.models.training_run import TrainingRun
from app.models.wellbeing import ModelInputSnapshot, RiskLabel

# Variables de entrada para el modelo, en el mismo orden que to_feature_vector
FEATURE_NAMES = [
    "mood_inverse",
    "sleep_deficit",
    "academic_pressure",
    "energy_risk",
    "registration_gap",
    "personal_delta",
    "trend_7d",
    "trend_14d",
]

# Rutas para almacenamiento de artefactos de entrenamiento
ARTIFACT_DIR = Path("artifacts")
MODEL_ARTIFACT_PATH = ARTIFACT_DIR / "risk_model.pkl"


@dataclass(slots=True)
class TrainingResult:
    model_path: Path # Ruta donde se guardó el modelo entrenado
    sample_count: int # Cantidad total de muestras utilizadas para el entrenamiento
    accuracy: float # Precisión global del modelo en el conjunto de prueba
    precision: float # Precisión ponderada del modelo en el conjunto de prueba
    recall: float # Recall ponderado del modelo en el conjunto de prueba
    f1: float # F1-score ponderado del modelo en el conjunto de prueba
    confusion_matrix: list[list[int]] # Matriz de confusión del modelo en el conjunto de prueba, representada como una lista de listas para facilitar la serialización
    classification_report: dict[str, dict[str, float] | dict[str, int] | dict[str, str]] # Reporte de clasificación del modelo en el conjunto de prueba, representado como un diccionario para facilitar la serialización


def create_training_run(db: Session) -> TrainingRun:
    run = TrainingRun(status="queued")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


# Cargar los snapshots de entrada del modelo junto con sus etiquetas de riesgo correspondientes, ordenados por fecha de creación para preservar la secuencia temporal
def load_supervised_dataset(db: Session) -> tuple[list[list[float]], list[int]]:
    rows = (
        db.query(ModelInputSnapshot, RiskLabel)
            .join(RiskLabel, RiskLabel.entry_id == ModelInputSnapshot.entry_id)
            .order_by(ModelInputSnapshot.id.asc())
            .all()
    )

    features: list[list[float]] = []
    labels: list[int] = []

    for snapshot, label in rows:
        features.append(to_feature_vector(snapshot))
        labels.append(int(label.risk_level))

    return features, labels

# Función para entrenar un clasificador de riesgo utilizando los datos etiquetados disponibles en la base de datos, y guardar el modelo entrenado en disco
def train_risk_classifier(db: Session, model_path: Path = MODEL_ARTIFACT_PATH) -> TrainingResult:
    features, labels = load_supervised_dataset(db)
    if len(features) < 6:
        raise ValueError("Se requieren al menos 6 registros etiquetados para entrenar el modelo")

    if len(set(labels)) < 2:
        raise ValueError("Se necesitan al menos dos clases distintas para entrenar el modelo")

    # Para evitar errores de estratificación cuando alguna clase tiene muy pocas muestras, solo se estratifica si todas las clases tienen al menos 2 muestras
    stratify_labels = labels if min(labels.count(label) for label in set(labels)) >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=stratify_labels,
    )

    # Se usó GradientBoostingClassifier por su buen desempeño en datasets pequeños y su capacidad para manejar relaciones no lineales, además de ser menos propenso a sobreajustar que otros modelos más complejos
    model = GradientBoostingClassifier(random_state=42)
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)

    # Se calculan las métricas de evaluación del modelo en el conjunto de prueba, y se guardan junto con la ruta del modelo entrenado en un objeto TrainingResult que se devuelve al finalizar el entrenamiento
    metrics = TrainingResult(
        model_path=model_path,
        sample_count=len(features),
        accuracy=accuracy_score(y_test, y_pred),
        precision=precision_score(y_test, y_pred, average="weighted", zero_division=0),
        recall=recall_score(y_test, y_pred, average="weighted", zero_division=0),
        f1=f1_score(y_test, y_pred, average="weighted", zero_division=0),
        confusion_matrix=confusion_matrix(y_test, y_pred).tolist(),
        classification_report=classification_report(y_test, y_pred, output_dict=True, zero_division=0),
    )

    # Se guarda el modelo entrenado en disco utilizando pickle, asegurándose de crear el directorio de artefactos si no existe
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("wb") as model_file:
        pickle.dump(model, model_file)

    return metrics


def train_and_store_run(db: Session, run: TrainingRun, model_path: Path = MODEL_ARTIFACT_PATH) -> TrainingRun:
    run.status = "running"
    run.started_at = datetime.now(UTC)
    db.commit()

    try:
        result = train_risk_classifier(db, model_path=model_path)
        run.status = "succeeded"
        run.sample_count = result.sample_count
        run.accuracy = result.accuracy
        run.precision = result.precision
        run.recall = result.recall
        run.f1 = result.f1
        run.confusion_matrix_json = json.dumps(result.confusion_matrix)
        run.classification_report_json = json.dumps(result.classification_report)
        run.model_path = str(result.model_path)
        run.artifact_size_bytes = result.model_path.stat().st_size if result.model_path.exists() else None
        run.finished_at = datetime.now(UTC)
        run.error_message = None
        db.commit()
        db.refresh(run)
        return run
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        run.finished_at = datetime.now(UTC)
        db.commit()
        db.refresh(run)
        raise

# Función para cargar el modelo entrenado desde disco, verificando que el archivo exista y que el artefacto cargado sea un modelo válido con capacidad de predicción
def load_trained_model(model_path: Path = MODEL_ARTIFACT_PATH) -> GradientBoostingClassifier:
    if not model_path.exists():
        raise FileNotFoundError(f"No se encontró el modelo entrenado en {model_path}")

    with model_path.open("rb") as model_file:
        model = pickle.load(model_file)

    if not hasattr(model, "predict"):
        raise NotFittedError("El artefacto cargado no es un modelo válido")

    return model

# Función para predecir la probabilidad de riesgo utilizando el modelo entrenado, dado un snapshot de entrada del modelo. Devuelve una lista de probabilidades para cada clase de riesgo.
def predict_risk_probability(snapshot: ModelInputSnapshot, model: GradientBoostingClassifier | None = None) -> list[float]:
    model = model or load_trained_model()
    return model.predict_proba([to_feature_vector(snapshot)])[0].tolist()


def inspect_artifact(model_path: Path = MODEL_ARTIFACT_PATH) -> dict[str, object]:
    info: dict[str, object] = {
        "model_path": str(model_path),
        "exists": model_path.exists(),
    }
    if model_path.exists():
        stat_result = model_path.stat()
        info.update(
            {
                "size_bytes": stat_result.st_size,
                "modified_at": datetime.fromtimestamp(stat_result.st_mtime, tz=UTC).isoformat(),
            }
        )
    return info