# MÓDULO PARA USO FUTURO, NO IMPLEMENTADO AÚN

from app.ai.feature_engineering import to_tensorflow_vector
from app.models.wellbeing import ModelInputSnapshot


def prepare_tensorflow_input(snapshot: ModelInputSnapshot) -> list[float]:
    return to_tensorflow_vector(snapshot)


def load_tensorflow_model(model_path: str | None = None):
    try:
        import tensorflow as tf  # type: ignore
    except ImportError as exc:
        raise RuntimeError("TensorFlow no está instalado en este entorno") from exc

    if model_path is None:
        return None

    return tf.keras.models.load_model(model_path)