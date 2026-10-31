"""Regression tests: the default JWT_SECRET must be rejected in production, and the CORS
origins defined in config.py must actually be wired into main.py."""

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
    """The real app (main.py) must reflect exactly what `cors_origin_list` exposes,
    not a hardcoded list that ignores the configuration."""
    from app.core.config import get_settings

    for origin in get_settings().cors_origin_list:
        resp = client.get("/", headers={"Origin": origin})
        assert resp.headers.get("access-control-allow-origin") == origin
