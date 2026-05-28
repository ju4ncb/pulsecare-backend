from contextlib import asynccontextmanager
from html import escape

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import joinedload

from app.api.auth import router as auth_router
from app.api.wellbeing import router as wellbeing_router
from app.api.ai import router as ai_router
from app.core.database import init_db
from app.core.security import get_password_hash


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="PulseCare Backend", version="0.1.0", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(wellbeing_router, prefix="/api")
app.include_router(ai_router, prefix="/api")


@app.get("/")
def root() -> HTMLResponse:
    return HTMLResponse(
        """
        <h1>Bienvenido a PulseCare</h1>
        <p>Esta es la API backend para la aplicación de bienestar personal PulseCare.</p>
        <ul>
            <li><a href="/insert-initial-data">Insertar datos iniciales</a></li>
            <li><a href="/manage-synthetic-data">Gestionar datos sintéticos</a></li>
        </ul>
        """
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/insert-initial-data")
def insert_initial_data() -> HTMLResponse:
    from app.core.database import SessionLocal
    from app.models.user import Role, User

    admin_email = "admin@pulsecare.com"
    admin_password = "adminpassword"

    db = SessionLocal()
    try:
        # Insertar roles iniciales si no existen
        if db.query(Role).count() == 0:
            student_role = Role(name="Estudiante")
            admin_role = Role(name="Admin")
            db.add_all([student_role, admin_role])
            db.commit()
        else:
            admin_role = db.query(Role).filter(Role.name == "Admin").first()
            if admin_role is None:
                admin_role = Role(name="Admin")
                db.add(admin_role)
                db.commit()
                db.refresh(admin_role)

        admin_user = db.query(User).filter(User.email == admin_email).first()
        if admin_user is None:
            admin_role = db.query(Role).filter(Role.name == "Admin").first()
            if admin_role is None:
                admin_role = Role(name="Admin")
                db.add(admin_role)
                db.commit()
                db.refresh(admin_role)

            admin_user = User(
                id_role=admin_role.id,
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                is_active=True,
            )
            db.add(admin_user)
            db.commit()

        return HTMLResponse(
            """
                <h1>Datos iniciales insertados</h1>
                <p>Se han verificado los roles iniciales y el usuario administrador.</p>
                <p>Usuario creado o confirmado: <strong>admin@pulsecare.com</strong></p>
                <a href="/">Volver al inicio</a>
            """
        )
    finally:
        db.close()


def _render_synthetic_entries_page(entries: list[object], message: str | None = None) -> HTMLResponse:
    items = ""
    for entry in entries:
        items += (
            "<li>"
            f"ID: {escape(str(entry['id']))} | usuario: {escape(str(entry['user_id']))} | "
            f"ánimo: {escape(str(entry['mood_score']))} | sueño: {escape(str(entry['sleep_hours']))} h | "
            f"carga: {escape(str(entry['academic_load']))} | riesgo: {escape(str(entry['risk_level']))}"
            "</li>"
        )

    if not items:
        items = "<li>No hay datos sintéticos para mostrar.</li>"

    message_block = f"<p><strong>{escape(message)}</strong></p>" if message else ""

    return HTMLResponse(
        f"""
        <h1>Gestión de Datos Sintéticos</h1>
        {message_block}
        <h2>Lista de datos sintéticos</h2>
        <p>A continuación se muestra una lista de los registros de bienestar marcados como sintéticos en la base de datos:</p>
        <ul>
            {items}
        </ul>
        <p>Utilice los siguientes enlaces para gestionar los datos sintéticos en la base de datos:</p>
        <a href="/seed-synthetic-data">Insertar datos sintéticos</a><br>
        <a href="/delete-synthetic-data">Eliminar datos sintéticos</a><br>
        <a href="/">Volver al inicio</a>
        """
    )


@app.get("/manage-synthetic-data")
def manage_synthetic_data() -> HTMLResponse:
    from app.core.database import SessionLocal
    from app.models.wellbeing import WellbeingEntry

    db = SessionLocal()
    try:
        synthetic_entries = (
            db.query(WellbeingEntry)
            .options(joinedload(WellbeingEntry.risk_label))
            .filter(WellbeingEntry.is_synthetic.is_(True))
            .order_by(WellbeingEntry.id.asc())
            .all()
        )
        synthetic_entries = [
            {
                "id": entry.id,
                "user_id": entry.user_id,
                "mood_score": entry.mood_score,
                "sleep_hours": entry.sleep_hours,
                "academic_load": entry.academic_load,
                "risk_level": entry.risk_label.risk_level if entry.risk_label else "N/A",
            }
            for entry in synthetic_entries
        ]
    finally:
        db.close()

    return _render_synthetic_entries_page(synthetic_entries)


@app.get("/seed-synthetic-data")
def seed_synthetic_data(count: int = 90, seed: int = 42) -> HTMLResponse:
    from app.models.wellbeing import WellbeingEntry
    from app.core.database import SessionLocal
    from scripts.seed_synthetic_data import seed_synthetic_data as seed_records

    seed_records(count=count, seed=seed)

    db = SessionLocal()
    try:
        synthetic_entries = (
            db.query(WellbeingEntry)
            .options(joinedload(WellbeingEntry.risk_label))
            .filter(WellbeingEntry.is_synthetic.is_(True))
            .order_by(WellbeingEntry.id.asc())
            .all()
        )
        synthetic_entries = [
            {
                "id": entry.id,
                "user_id": entry.user_id,
                "mood_score": entry.mood_score,
                "sleep_hours": entry.sleep_hours,
                "academic_load": entry.academic_load,
                "risk_level": entry.risk_label.risk_level if entry.risk_label else "N/A",
            }
            for entry in synthetic_entries
        ]
    finally:
        db.close()

    return _render_synthetic_entries_page(
        synthetic_entries,
        message=f"Se insertaron {count} registros sintéticos usando seed {seed}.",
    )


@app.get("/delete-synthetic-data")
def delete_synthetic_data() -> HTMLResponse:
    from app.models.wellbeing import WellbeingEntry
    from app.core.database import SessionLocal
    from scripts.delete_synthetic_data import delete_synthetic_data as delete_records

    delete_records()

    db = SessionLocal()
    try:
        synthetic_entries = (
            db.query(WellbeingEntry)
            .options(joinedload(WellbeingEntry.risk_label))
            .filter(WellbeingEntry.is_synthetic.is_(True))
            .order_by(WellbeingEntry.id.asc())
            .all()
        )
        synthetic_entries = [
            {
                "id": entry.id,
                "user_id": entry.user_id,
                "mood_score": entry.mood_score,
                "sleep_hours": entry.sleep_hours,
                "academic_load": entry.academic_load,
                "risk_level": entry.risk_label.risk_level if entry.risk_label else "N/A",
            }
            for entry in synthetic_entries
        ]
    finally:
        db.close()

    return _render_synthetic_entries_page(
        synthetic_entries,
        message="Se eliminaron los datos sintéticos de la base de datos.",
    )