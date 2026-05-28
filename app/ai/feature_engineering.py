# MÓDULO PARA USO FUTURO, NO IMPLEMENTADO AÚN

from app.models.wellbeing import ModelInputSnapshot, WellbeingEntry


def build_model_input_snapshot(entry: WellbeingEntry) -> ModelInputSnapshot:
    return ModelInputSnapshot(
        entry_id=entry.id,
        mood_inverse=float(6 - entry.mood_score),
        sleep_deficit=float(max(0.0, 8.0 - entry.sleep_hours)),
        academic_pressure=float(entry.academic_load),
        energy_risk=float(6 - entry.energy_fatigue),
        registration_gap=float(6 - entry.registration_regular),
        personal_delta=float(entry.recent_change_vs_average),
        trend_7d=float(entry.trend_7d),
        trend_14d=float(entry.trend_14d),
    )


def to_feature_vector(snapshot: ModelInputSnapshot) -> list[float]:
    return [
        snapshot.mood_inverse,
        snapshot.sleep_deficit,
        snapshot.academic_pressure,
        snapshot.energy_risk,
        snapshot.registration_gap,
        snapshot.personal_delta,
        snapshot.trend_7d,
        snapshot.trend_14d,
    ]


def to_tensorflow_vector(snapshot: ModelInputSnapshot) -> list[float]:
    return to_feature_vector(snapshot)