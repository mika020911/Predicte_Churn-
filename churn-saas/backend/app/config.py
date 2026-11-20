
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]  


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    ml_src_dir: Path = ROOT_DIR / "ml" / "src"  # dossier du code ML
    cors_origins: str = "http://localhost:3000"

    frontend_url: str = "http://localhost:3000"

    # Taille maximale d'un fichier d'import (CSV ou XLSX), en mégaoctets.
    max_upload_size_mb: int = 20

    smtp_host: str = "smtp-relay.brevo.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "ChurnSight"

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")



settings = Settings()