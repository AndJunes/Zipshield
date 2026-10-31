from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: str = "development"
    database_url: str = "postgresql+psycopg2://zipshield:zipshield@localhost:5432/zipshield"
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 24 * 60
    cors_origins: str = "http://localhost:4200,http://localhost:58376"

    # --- LLM: automated claim analysis (OpenRouter, vision model) ---
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.5-flash-lite"
    openrouter_url: str = "https://openrouter.ai/api/v1/chat/completions"
    guard_salt: str = "mmer-guard-salt-2026"
    llm_max_tokens: int = 900
    llm_temperature: float = 0.0
    llm_request_timeout: int = 120
    llm_max_retries: int = 4
    llm_use_json_schema: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def model_post_init(self, __context) -> None:
        # The JWT_SECRET placeholder must never reach production unnoticed —
        # fail fast instead of signing tokens with a public secret.
        if self.environment == "production" and self.jwt_secret == "change-me-in-prod":
            raise RuntimeError(
                "JWT_SECRET is still set to its default value in a production environment. "
                "Set a real secret (JWT_SECRET environment variable) before starting."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
