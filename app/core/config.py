from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Blog Application"
    API_VERSION: str = "/api/v1"
    APP_VERSION: str = "1.0.0"
    # Database
    DATABASE_URL: str

    DEBUG: bool = False
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: list[str] = []

    # Trusted hosts (separate from CORS origins)
    ALLOWED_HOSTS: list[str] = []

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure SECRET_KEY has minimum length for security."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def validate_origins(cls, v: list[str]) -> list[str]:
        """Ensure ALLOWED_ORIGINS does not mix '*' with specific origins."""
        if "*" in v and len(v) > 1:
            raise ValueError("ALLOWED_ORIGINS cannot mix '*' with specific origins")
        return v

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
