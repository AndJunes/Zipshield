"""Regression tests: development defaults must be rejected in production, and the CORS
origins defined in config.py must actually be wired into main.py."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

_PROD_OVERRIDES = dict(
    environment="production",
    jwt_secret="a-real-production-secret-of-32-bytes-or-more",
    guard_salt="a-real-production-salt",
    database_url="postgresql+psycopg2://app:real-password@db.internal:5432/zipshield",
)


def _prod_settings(**overrides) -> Settings:
    return Settings(**{**_PROD_OVERRIDES, **overrides})


def test_production_accepts_real_secrets():
    assert _prod_settings().environment == "production"


def test_production_rejects_the_default_jwt_secret():
    with pytest.raises(RuntimeError):
        _prod_settings(jwt_secret="change-me-in-prod")


def test_production_rejects_a_short_jwt_secret():
    with pytest.raises(RuntimeError):
        _prod_settings(jwt_secret="too-short")


def test_production_rejects_the_default_guard_salt():
    with pytest.raises(RuntimeError):
        _prod_settings(guard_salt="mmer-guard-salt-2026")


def test_production_rejects_the_default_database_url():
    with pytest.raises(RuntimeError):
        _prod_settings(
            database_url="postgresql+psycopg2://zipshield:zipshield@localhost:5432/zipshield"
        )


def test_environment_only_accepts_known_values():
    with pytest.raises(ValidationError):
        Settings(environment="staging")


def test_development_allows_the_defaults():
    settings = Settings(environment="development", jwt_secret="change-me-in-prod")
    assert settings.jwt_secret == "change-me-in-prod"


def test_cors_origin_list_parses_comma_separated_origins():
    settings = Settings(cors_origins="http://a.test, http://b.test")
    assert settings.cors_origin_list == ["http://a.test", "http://b.test"]


def test_app_cors_allows_the_configured_origins(client):
    """The real app (main.py) must reflect exactly what `cors_origin_list` exposes,
    not a hardcoded list that ignores the configuration."""
    from app.core.config import get_settings

    for origin in get_settings().cors_origin_list:
        resp = client.get("/", headers={"Origin": origin})
        assert resp.headers.get("access-control-allow-origin") == origin
