from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.core.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="PulseCare Backend", version="0.1.0", lifespan=lifespan)

app.include_router(auth_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "PulseCare Backend is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
