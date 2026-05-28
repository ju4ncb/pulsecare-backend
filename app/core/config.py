from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _build_sqlite_url(db_path: str) -> str:
    normalized_path = db_path.lstrip("/")
    return f"sqlite:///{normalized_path}"


class Settings(BaseSettings):
    secret_key: str = "change-this-secret-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    db_path: str = "./pulsecare.db"
    database_url: str = "sqlite:///./pulsecare.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        self.database_url = _build_sqlite_url(self.db_path)
        return self


settings = Settings()
