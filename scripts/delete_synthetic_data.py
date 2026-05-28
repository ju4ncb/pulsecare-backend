from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal, init_db
from app.models.user import User
from app.models.wellbeing import WellbeingEntry


SYNTHETIC_EMAIL = "synthetic.data@pulsecare.local"


def delete_synthetic_data() -> None:
    init_db()
    session = SessionLocal()
    try:
        entries = session.query(WellbeingEntry).filter(WellbeingEntry.is_synthetic.is_(True)).all()
        deleted_entries = len(entries)

        for entry in entries:
            session.delete(entry)

        synthetic_user = session.query(User).filter(User.email == SYNTHETIC_EMAIL).first()
        deleted_user = False
        if synthetic_user is not None:
            session.delete(synthetic_user)
            deleted_user = True

        session.commit()
        print(f"Se eliminaron {deleted_entries} registros sinteticos")
        if deleted_user:
            print(f"Se elimino el usuario sintetico {SYNTHETIC_EMAIL}")
    finally:
        session.close()


if __name__ == "__main__":
    delete_synthetic_data()