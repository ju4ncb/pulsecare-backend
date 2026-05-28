from __future__ import annotations

import argparse
import random
from datetime import UTC, datetime, timedelta
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ai.feature_engineering import build_model_input_snapshot
from app.core.database import SessionLocal, init_db
from app.core.security import get_password_hash
from app.models.user import Role, User
from app.models.wellbeing import RiskLabel, WellbeingEntry


SYNTHETIC_EMAIL = "syntheticdata@pulsecare.com"


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def ensure_roles(session) -> tuple[Role, Role]:
    student_role = session.query(Role).filter(Role.id == 1).first()
    admin_role = session.query(Role).filter(Role.id == 2).first()

    if student_role is None:
        student_role = Role(id=1, name="Estudiante")
        session.add(student_role)

    if admin_role is None:
        admin_role = Role(id=2, name="Admin")
        session.add(admin_role)

    session.commit()
    return student_role, admin_role


def ensure_synthetic_user(session, student_role: Role) -> User:
    user = session.query(User).filter(User.email == SYNTHETIC_EMAIL).first()
    if user is not None:
        return user

    user = User(
        email=SYNTHETIC_EMAIL,
        name="Synthetic User",
        hashed_password=get_password_hash("synthetic-password"),
        id_role=student_role.id,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def generate_phase_values(phase: int, rng: random.Random) -> dict[str, float]:
    if phase == 0:
        return {
            "mood_score": clamp(rng.gauss(5.0, 0.6), 1, 5),
            "sleep_hours": clamp(rng.gauss(8.0, 0.7), 0, 24),
            "academic_load": clamp(rng.gauss(2.0, 0.5), 1, 5),
            "energy_fatigue": clamp(rng.gauss(5.0, 0.5), 1, 5),
            "registration_regular": clamp(rng.gauss(5.0, 0.3), 1, 5),
            "recent_change_vs_average": clamp(rng.gauss(0.8, 0.4), -5, 5),
            "trend_7d": clamp(rng.gauss(0.6, 0.3), -5, 5),
            "trend_14d": clamp(rng.gauss(0.5, 0.3), -5, 5),
            "risk_level": 0,
        }

    if phase == 1:
        return {
            "mood_score": clamp(rng.gauss(3.2, 0.6), 1, 5),
            "sleep_hours": clamp(rng.gauss(6.5, 0.8), 0, 24),
            "academic_load": clamp(rng.gauss(3.5, 0.6), 1, 5),
            "energy_fatigue": clamp(rng.gauss(3.2, 0.6), 1, 5),
            "registration_regular": clamp(rng.gauss(3.5, 0.5), 1, 5),
            "recent_change_vs_average": clamp(rng.gauss(-0.3, 0.4), -5, 5),
            "trend_7d": clamp(rng.gauss(-0.2, 0.4), -5, 5),
            "trend_14d": clamp(rng.gauss(-0.3, 0.4), -5, 5),
            "risk_level": 1,
        }

    return {
        "mood_score": clamp(rng.gauss(2.0, 0.7), 1, 5),
        "sleep_hours": clamp(rng.gauss(5.0, 1.0), 0, 24),
        "academic_load": clamp(rng.gauss(4.5, 0.4), 1, 5),
        "energy_fatigue": clamp(rng.gauss(2.0, 0.6), 1, 5),
        "registration_regular": clamp(rng.gauss(2.0, 0.6), 1, 5),
        "recent_change_vs_average": clamp(rng.gauss(-1.2, 0.5), -5, 5),
        "trend_7d": clamp(rng.gauss(-1.0, 0.5), -5, 5),
        "trend_14d": clamp(rng.gauss(-1.1, 0.5), -5, 5),
        "risk_level": 2,
    }


def seed_synthetic_data(count: int, seed: int) -> None:
    init_db()
    rng = random.Random(seed)

    session = SessionLocal()
    try:
        student_role, _ = ensure_roles(session)
        user = ensure_synthetic_user(session, student_role)

        start_date = datetime.now(UTC) - timedelta(days=count - 1)

        for index in range(count):
            phase = index % 3
            values = generate_phase_values(phase, rng)
            recorded_at = start_date + timedelta(days=index)

            entry = WellbeingEntry(
                user_id=user.id,
                mood_score=int(round(values["mood_score"])),
                sleep_hours=float(round(values["sleep_hours"], 1)),
                academic_load=int(round(values["academic_load"])),
                energy_fatigue=int(round(values["energy_fatigue"])),
                registration_regular=int(round(values["registration_regular"])),
                recent_change_vs_average=float(round(values["recent_change_vs_average"], 2)),
                trend_7d=float(round(values["trend_7d"], 2)),
                trend_14d=float(round(values["trend_14d"], 2)),
                is_synthetic=True,
                recorded_at=recorded_at,
            )
            session.add(entry)
            session.flush()

            snapshot = build_model_input_snapshot(entry)
            session.add(snapshot)

            label = RiskLabel(
                entry_id=entry.id,
                risk_level=int(values["risk_level"]),
                label_source="synthetic_seed",
                label_note="Generado por script de datos sinteticos",
            )
            session.add(label)

        session.commit()
        print(f"Se insertaron {count} registros sinteticos para {user.email}")
    finally:
        session.close()


def generate_synthetic_payloads(count: int, seed: int) -> list[dict]:
    """Generate synthetic payload dicts without inserting into the DB.

    These payloads match the WellbeingEntryImport schema expected by the
    `/api/wellbeing/entries/import` endpoint.
    """
    init_db()
    rng = random.Random(seed)
    payloads: list[dict] = []

    # use same synthetic user email to maintain consistency
    session = SessionLocal()
    try:
        student_role, _ = ensure_roles(session)
        user = ensure_synthetic_user(session, student_role)

        start_date = datetime.now(UTC) - timedelta(days=count - 1)

        for index in range(count):
            phase = index % 3
            values = generate_phase_values(phase, rng)
            recorded_at = start_date + timedelta(days=index)

            payloads.append(
                {
                    "user_id": user.id,
                    "mood_score": int(round(values["mood_score"])),
                    "sleep_hours": float(round(values["sleep_hours"], 1)),
                    "academic_load": int(round(values["academic_load"])),
                    "energy_fatigue": int(round(values["energy_fatigue"])),
                    "registration_regular": int(round(values["registration_regular"])),
                    "recent_change_vs_average": float(round(values["recent_change_vs_average"], 2)),
                    "trend_7d": float(round(values["trend_7d"], 2)),
                    "trend_14d": float(round(values["trend_14d"], 2)),
                    "is_synthetic": True,
                    "recorded_at": recorded_at,
                    "risk_level": int(values["risk_level"]),
                    "label_source": "synthetic_seed",
                    "label_note": "Generado por script de datos sinteticos",
                }
            )

    finally:
        session.close()

    return payloads


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Insert synthetic wellbeing data")
    parser.add_argument("--count", type=int, default=90, help="Cantidad de registros sinteticos a generar")
    parser.add_argument("--seed", type=int, default=42, help="Semilla para reproducibilidad")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    seed_synthetic_data(args.count, args.seed)