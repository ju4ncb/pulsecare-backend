from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WellbeingEntry(Base):
    __tablename__ = "wellbeing_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True) # Relación con usuario, clave foránea
    mood_score: Mapped[int] = mapped_column(Integer, nullable=False) # Escala de 1 a 10, donde 1 es muy mal y 10 es excelente
    sleep_hours: Mapped[float] = mapped_column(Float, nullable=False) # Horas de sueño, valor decimal entre 0 y 24
    academic_load: Mapped[int] = mapped_column(Integer, nullable=False) # Carga académica percibida, escala de 1 a 10
    energy_fatigue: Mapped[int] = mapped_column(Integer, nullable=False) # Nivel de energía o fatiga, escala de 1 a 10
    registration_regular: Mapped[int] = mapped_column(Integer, nullable=False) # Regularidad en el registro de datos, escala de 1 a 10
    recent_change_vs_average: Mapped[float] = mapped_column(Float, nullable=False) # Cambio reciente en comparación con el promedio, valor decimal entre -5 y 5
    trend_7d: Mapped[float] = mapped_column(Float, nullable=False) # Tendencia en los últimos 7 días, valor decimal entre -5 y 5
    trend_14d: Mapped[float] = mapped_column(Float, nullable=False) # Tendencia en los últimos 14 días, valor decimal entre -5 y 5
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False) # Timestamp de registro

    user = relationship("User", back_populates="wellbeing_entries") # Relación con usuario, permite acceder a los datos del usuario desde la entrada de bienestar
    model_input = relationship("ModelInputSnapshot", back_populates="entry", uselist=False, cascade="all, delete-orphan") # Relación uno a uno con ModelInputSnapshot, permite acceder a los datos de entrada del modelo desde la entrada de bienestar
    risk_label = relationship("RiskLabel", back_populates="entry", uselist=False, cascade="all, delete-orphan") # Relación uno a uno con RiskLabel, permite acceder a la etiqueta de riesgo desde la entrada de bienestar


class ModelInputSnapshot(Base):
    __tablename__ = "model_input_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("wellbeing_entries.id"), unique=True, nullable=False, index=True) # Relación uno a uno con WellbeingEntry, clave foránea única
    mood_inverse: Mapped[float] = mapped_column(Float, nullable=False) # Inverso del estado de ánimo, calculado como 6 - mood_score para que valores más altos indiquen mayor riesgo
    sleep_deficit: Mapped[float] = mapped_column(Float, nullable=False) # Déficit de sueño, valor decimal
    academic_pressure: Mapped[float] = mapped_column(Float, nullable=False) # Presión académica, valor decimal
    energy_risk: Mapped[float] = mapped_column(Float, nullable=False) # Riesgo de energía, valor decimal
    registration_gap: Mapped[float] = mapped_column(Float, nullable=False) # Brecha en el registro, valor decimal
    personal_delta: Mapped[float] = mapped_column(Float, nullable=False) # Delta personal, valor decimal
    trend_7d: Mapped[float] = mapped_column(Float, nullable=False) # Tendencia en los últimos 7 días, valor decimal entre -5 y 5
    trend_14d: Mapped[float] = mapped_column(Float, nullable=False) # Tendencia en los últimos 14 días, valor decimal entre -5 y 5
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False) # Timestamp de creación

    entry = relationship("WellbeingEntry", back_populates="model_input") # Relación 1:1 con WellbeingEntry, permite acceder a los datos de la entrada de bienestar desde el snapshot de entrada del modelo


class RiskLabel(Base):
    __tablename__ = "risk_labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("wellbeing_entries.id"), unique=True, nullable=False, index=True) # Relación uno a uno con WellbeingEntry, clave foránea única
    risk_level: Mapped[int] = mapped_column(Integer, nullable=False) # Nivel de riesgo, escala de 1 a 10
    label_source: Mapped[str] = mapped_column(String(80), nullable=False) # Fuente de la etiqueta de riesgo, e.g. "manual", "modelo_v1", "modelo_v2"
    label_note: Mapped[str | None] = mapped_column(String(255), nullable=True) # Nota adicional sobre la etiqueta de riesgo
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False) # Timestamp de creación

    entry = relationship("WellbeingEntry", back_populates="risk_label")