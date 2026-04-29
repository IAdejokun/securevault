from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Security
    nonce_window_seconds: int = 30

    # Application
    app_env: str = "development"
    # Stored as a plain comma-separated string — parsed via the property below
    cors_origins_raw: str = "http://localhost:4200"

    # Anomaly detection
    anomaly_model_path: str = "models/isolation_forest.joblib"
    anomaly_score_threshold: int = 75

    @property
    def cors_origins(self) -> List[str]:
        """Split the comma-separated string into a list of origins."""
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()