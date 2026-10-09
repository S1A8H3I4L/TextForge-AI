"""Application settings, loaded from environment variables / .env file."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]  # textforge-ai/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "TextForge AI"
    # SQLite by default so the project runs with zero setup; use PostgreSQL in Docker/production.
    database_url: str = f"sqlite:///{ROOT_DIR / 'textforge.db'}"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    data_dir: Path = ROOT_DIR / "data"
    artifacts_dir: Path = ROOT_DIR / "artifacts"
    dataset_path: Path = ROOT_DIR / "data" / "shakespeare.txt"
    dataset_url: str = (
        "https://storage.googleapis.com/download.tensorflow.org/data/shakespeare.txt"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
