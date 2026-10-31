from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: Literal["development", "test", "production"] = "development"
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
        # Fail fast on anything that must never reach production: the defaults are
        # public (they live in this repo), so a token signed or a guard salted with
        # them protects nothing.
        if self.environment != "production":
            return
        defaults = {name: field.default for name, field in type(self).model_fields.items()}
        problems = [
            f"{name.upper()} is still its development default"
            for name in ("jwt_secret", "guard_salt", "database_url")
            if getattr(self, name) == defaults[name]
        ]
        if len(self.jwt_secret.encode()) < 32:
            problems.append("JWT_SECRET is shorter than the 32 bytes RFC 7518 requires for HS256")
        if problems:
            raise RuntimeError("Refusing to start in production: " + "; ".join(problems))


@lru_cache
def get_settings() -> Settings:
    return Settings()
