from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal, init_db
from app.services.deletion_service import delete_user_with_dependents, delete_wellbeing_entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete a user or a wellbeing entry without FK errors")
    parser.add_argument("--user-id", type=int, help="User id to delete with dependents")
    parser.add_argument("--entry-id", type=int, help="Wellbeing entry id to delete")
    args = parser.parse_args()

    if args.user_id is None and args.entry_id is None:
        parser.error("provide --user-id and/or --entry-id")

    init_db()
    session = SessionLocal()
    try:
        deleted_anything = False

        if args.entry_id is not None:
            if delete_wellbeing_entry(session, args.entry_id):
                print(f"Se elimino el registro de bienestar {args.entry_id}")
                deleted_anything = True
            else:
                print(f"No existe el registro de bienestar {args.entry_id}")

        if args.user_id is not None:
            if delete_user_with_dependents(session, args.user_id):
                print(f"Se elimino el usuario {args.user_id} junto con sus dependencias")
                deleted_anything = True
            else:
                print(f"No existe el usuario {args.user_id}")

        session.commit()
        return 0 if deleted_anything else 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())