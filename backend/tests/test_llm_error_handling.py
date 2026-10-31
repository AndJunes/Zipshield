"""Regression tests: a malformed 200 response from the LLM provider must produce the
documented 502, not a raw 500 (uncaught KeyError/JSONDecodeError), and the `client.chat()`
*retry* inside `_review` must not swallow a network/credential error and degrade it to
"invalid model output" instead of propagating it."""

import json

import pytest

from app.core.config import get_settings
from app.llm import service as llm_service
from app.llm.client import OpenRouterClient
from tests.conftest import (
    auth_headers,
    make_agent,
    make_claim,
    make_client,
    make_supervisor,
    make_user,
)


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
    """Simulates: first response is unparseable JSON -> triggers the strict-mode retry
    -> that retry fails on network/credentials (RuntimeError)."""

    def __init__(self):
        self.calls = 0

    def chat(self, system, user_text, image_urls, response_format=None):
        self.calls += 1
        if self.calls == 1:
            return "this is not json"
        raise RuntimeError("OpenRouter failed after 4 attempts: Connection refused")


def test_review_propagates_runtime_error_from_the_retry_call_instead_of_degrading():
    fake_client = _FakeClientFirstBadThenNetworkError()

    with pytest.raises(RuntimeError):
        llm_service._review(
            "car",
            "I crashed the car",
            ["http://img.test/1.jpg"],
            history={},
            requirements=[],
            client=fake_client,
        )
    assert fake_client.calls == 2  # the strict-mode retry was attempted before failing


def test_malformed_llm_response_ends_as_failed_never_a_500(client, db_session, monkeypatch):
    """Full path through the real analyze_claim with a fake transport: a malformed 200
    from the provider must end as analysis_status="failed", never as a raw 500."""
    from tests.test_claims_analysis import _SharedSession

    monkeypatch.setattr("app.claims.service.SessionLocal", lambda: _SharedSession(db_session))
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
    assert resp.status_code == 202

    db_session.refresh(claim)
    assert claim.analysis_status == "failed"
    assert claim.claim_status == "not_enough_information"  # the claim is left untouched
