"""Regresión para BUG-05 (JWT_SECRET por defecto sin ninguna salvaguarda) y A3 (CORS
definido en config.py pero nunca conectado a main.py)."""

import pytest

from app.core.config import Settings


def test_settings_rejects_default_secret_in_production():
    with pytest.raises(RuntimeError):
        Settings(environment="production", jwt_secret="change-me-in-prod")


def test_settings_allows_default_secret_outside_production():
    settings = Settings(environment="development", jwt_secret="change-me-in-prod")
    assert settings.jwt_secret == "change-me-in-prod"


def test_settings_allows_custom_secret_in_production():
    settings = Settings(environment="production", jwt_secret="a-real-production-secret")
    assert settings.environment == "production"


def test_cors_origin_list_parses_comma_separated_origins():
    settings = Settings(cors_origins="http://a.test, http://b.test")
    assert settings.cors_origin_list == ["http://a.test", "http://b.test"]


def test_app_cors_allows_the_configured_origins(client):
    """La app real (main.py) debe reflejar exactamente lo que expone `cors_origin_list`,
    no una lista hardcodeada que ignore la configuración."""
    from app.core.config import get_settings

    for origin in get_settings().cors_origin_list:
        resp = client.get("/", headers={"Origin": origin})
        assert resp.headers.get("access-control-allow-origin") == origin
