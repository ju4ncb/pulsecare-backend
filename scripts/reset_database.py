from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine, init_db
from app.core.security import get_password_hash
from app.models import training_run as _training_run  # noqa: F401
from app.models import user as _user  # noqa: F401
from app.models import wellbeing as _wellbeing  # noqa: F401
from app.models.user import Role, User


DEFAULT_ADMIN_EMAIL = "admin@pulsecare.com"
DEFAULT_ADMIN_PASSWORD = "adminpassword"


def _sqlite_path() -> Path | None:
    if not settings.database_url.startswith("sqlite"):
        return None

    if settings.db_path.startswith("/"):
        return Path(settings.db_path)

    return (PROJECT_ROOT / settings.db_path).resolve()


def reset_database(admin_email: str = DEFAULT_ADMIN_EMAIL, admin_password: str = DEFAULT_ADMIN_PASSWORD) -> None:
    db_path = _sqlite_path()
    if db_path is not None and db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            engine.dispose()
            Base.metadata.drop_all(bind=engine)

    init_db()

    session = SessionLocal()
    try:
        estudiante_role = Role(name="Estudiante")
        admin_role = Role(name="Admin")
        session.add_all([estudiante_role, admin_role])
        session.flush()

        admin_user = User(
            id_role=admin_role.id,
            email=admin_email.strip().lower(),
            hashed_password=get_password_hash(admin_password),
            is_active=True,
        )
        session.add(admin_user)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset SQLite database and create the initial admin user")
    parser.add_argument("--admin-email", default=DEFAULT_ADMIN_EMAIL, help="Email for the initial admin user")
    parser.add_argument("--admin-password", default=DEFAULT_ADMIN_PASSWORD, help="Password for the initial admin user")
    args = parser.parse_args()

    reset_database(admin_email=args.admin_email, admin_password=args.admin_password)
    print(f"Base de datos reiniciada y usuario inicial creado: {args.admin_email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())