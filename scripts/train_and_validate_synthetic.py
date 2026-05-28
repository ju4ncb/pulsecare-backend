from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal, init_db
from app.ai.training import train_risk_classifier, load_trained_model, load_supervised_dataset, MODEL_ARTIFACT_PATH
from app.ai.training import TrainingResult
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

from scripts.seed_synthetic_data import seed_synthetic_data

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(__file__).resolve().parent


def write_markdown(report_path: Path, training: TrainingResult, full_eval: dict):
    md = []
    md.append(f"# Entrenamiento y validación - {datetime.now(UTC).isoformat()}\n")

    md.append("## Resultado de entrenamiento (test split)")
    md.append(f"- Muestras totales usadas: {training.sample_count}")
    md.append(f"- Accuracy: {training.accuracy:.4f}")
    md.append(f"- Precision: {training.precision:.4f}")
    md.append(f"- Recall: {training.recall:.4f}")
    md.append(f"- F1: {training.f1:.4f}")
    md.append("\n### Matriz de confusión (train test split)")
    md.append("```")
    md.append(json.dumps(training.confusion_matrix, indent=2))
    md.append("```")
    md.append("\n### Classification report (train test split)")
    md.append("```")
    md.append(json.dumps(training.classification_report, indent=2))
    md.append("```")

    md.append("\n## Validación sobre dataset etiquetado completo")
    md.append(f"- Muestras: {full_eval['sample_count']}")
    md.append(f"- Accuracy: {full_eval['accuracy']:.4f}")
    md.append(f"- Precision: {full_eval['precision']:.4f}")
    md.append(f"- Recall: {full_eval['recall']:.4f}")
    md.append(f"- F1: {full_eval['f1']:.4f}")
    md.append("\n### Matriz de confusión (validación full)")
    md.append("```")
    md.append(json.dumps(full_eval['confusion_matrix'], indent=2))
    md.append("```")
    md.append("\n### Classification report (validación full)")
    md.append("```")
    md.append(json.dumps(full_eval['classification_report'], indent=2))
    md.append("```")

    md.append(f"\nModelo guardado en: `{training.model_path}`")

    report_path.write_text("\n".join(md), encoding="utf-8")


def run(count: int, seed: int, out: Path) -> Path:
    init_db()

    # seed synthetic labeled data
    seed_synthetic_data(count=count, seed=seed)

    db = SessionLocal()
    try:
        # train model (this also saves the model to artifacts)
        training = train_risk_classifier(db)

        # validation on full labeled dataset
        features, labels = load_supervised_dataset(db)
        model = load_trained_model()
        y_pred = model.predict(features)

        full_eval = {
            "sample_count": len(features),
            "accuracy": float(accuracy_score(labels, y_pred)),
            "precision": float(precision_score(labels, y_pred, average="weighted", zero_division=0)),
            "recall": float(recall_score(labels, y_pred, average="weighted", zero_division=0)),
            "f1": float(f1_score(labels, y_pred, average="weighted", zero_division=0)),
            "confusion_matrix": confusion_matrix(labels, y_pred).tolist(),
            "classification_report": classification_report(labels, y_pred, output_dict=True, zero_division=0),
        }

        # write markdown
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        out_name = out or (OUT_DIR / f"train_validation_report_{timestamp}.md")
        write_markdown(Path(out_name), training, full_eval)
        return Path(out_name)

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and validate model using synthetic data and save markdown report")
    parser.add_argument("--count", type=int, default=90)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default=None, help="Output markdown path (optional)")
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else None
    report = run(count=args.count, seed=args.seed, out=out_path)
    print(f"Report written to: {report}")
