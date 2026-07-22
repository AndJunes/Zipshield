"""Regresión para BUG-16: una respuesta 200 malformada del proveedor LLM producía un 500
crudo (KeyError/JSONDecodeError sin capturar) en vez del 502 documentado, y el *reintento*
de `client.chat()` dentro de `_review` podía tragarse un error de red/credenciales y
degradarlo a "salida del modelo inválida" en vez de propagarlo."""

import json

import pytest

from app.llm import service as llm_service
from app.llm.client import OpenRouterClient
from app.core.config import get_settings

from tests.conftest import auth_headers, make_agent, make_claim, make_client, make_supervisor, make_user


class _FakeResponse:
    def __init__(self, status_code: int, json_body=None, text: str = ""):
        self.status_code = status_code
        self._json_body = json_body
        self.text = text

    def json(self):
        if self._json_body is None:
            raise json.JSONDecodeError("Expecting value", "", 0)
        return self._json_body


def test_client_raises_runtime_error_on_malformed_200_missing_choices(monkeypatch):
    client = OpenRouterClient()
    client.api_key = "test-key"
    client.max_retries = 1

    monkeypatch.setattr(
        "app.llm.client.httpx.post",
        lambda *a, **k: _FakeResponse(200, json_body={"moderation": "blocked"}),
    )

    with pytest.raises(RuntimeError):
        client.chat("system", "user", [])


def test_client_raises_runtime_error_on_malformed_200_invalid_json(monkeypatch):
    client = OpenRouterClient()
    client.api_key = "test-key"
    client.max_retries = 1

    monkeypatch.setattr(
        "app.llm.client.httpx.post",
        lambda *a, **k: _FakeResponse(200, json_body=None, text="not json"),
    )

    with pytest.raises(RuntimeError):
        client.chat("system", "user", [])


class _FakeClientFirstBadThenNetworkError:
    """Simula: primera respuesta con JSON no parseable -> dispara el reintento en modo
    estricto -> ese reintento falla por red/credenciales (RuntimeError)."""

    def __init__(self):
        self.calls = 0

    def chat(self, system, user_text, image_urls, response_format=None):
        self.calls += 1
        if self.calls == 1:
            return "esto no es json"
        raise RuntimeError("OpenRouter falló tras 4 intentos: Connection refused")


def test_review_propagates_runtime_error_from_the_retry_call_instead_of_degrading():
    fake_client = _FakeClientFirstBadThenNetworkError()

    with pytest.raises(RuntimeError):
        llm_service._review(
            "car", "Choqué el auto", ["http://img.test/1.jpg"],
            history={}, requirements=[], client=fake_client,
        )
    assert fake_client.calls == 2  # sí se intentó el modo estricto antes de fallar


def test_analyze_claim_endpoint_returns_502_not_500_on_malformed_llm_response(client, db_session, monkeypatch):
    monkeypatch.setattr(get_settings(), "openrouter_api_key", "test-key")
    monkeypatch.setattr(
        "app.llm.client.httpx.post",
        lambda *a, **k: _FakeResponse(200, json_body={"unexpected": "shape"}),
    )

    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    claim = make_claim(db_session, owner, image_urls=["http://img.test/1.jpg"])
    user = make_user(db_session, role="agent", ref_id=agent.id)

    resp = client.post(f"/claims/{claim.id}/analyze", headers=auth_headers(user))
    assert resp.status_code == 502

    db_session.refresh(claim)
    assert claim.claim_status == "not_enough_information"  # el reclamo queda intacto
