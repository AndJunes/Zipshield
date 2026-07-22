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

    # --- LLM: análisis automático de claims (OpenRouter, modelo con visión) ---
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
        # BUG-05: el placeholder de JWT_SECRET no debe poder llegar a producción sin que
        # nadie lo note — falla rápido en vez de firmar tokens con un secreto público.
        if self.environment == "production" and self.jwt_secret == "change-me-in-prod":
            raise RuntimeError(
                "JWT_SECRET sigue en su valor por defecto en un entorno de producción. "
                "Configura un secreto real (variable de entorno JWT_SECRET) antes de arrancar."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
