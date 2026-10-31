"""The analyze endpoint queues the AI review and reports it via analysis_status:
202 + "pending" right away, then "done" or "failed" on the claim."""

import pytest

from tests.conftest import (
    auth_headers,
    make_agent,
    make_claim,
    make_client,
    make_supervisor,
    make_user,
)


class _SharedSession:
    """Hands the background task the test's savepoint session, so whatever it
    commits stays inside the test transaction; close() is a no-op because the
    fixture still owns the session."""

    def __init__(self, session):
        self._session = session

    def __getattr__(self, name):
        return getattr(self._session, name)

    def close(self):
        pass


@pytest.fixture
def shared_background_session(db_session, monkeypatch):
    monkeypatch.setattr("app.claims.service.SessionLocal", lambda: _SharedSession(db_session))


def _actor_and_claim(db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    claim = make_claim(db_session, owner, image_urls=["http://img.test/1.jpg"])
    user = make_user(db_session, role="agent", ref_id=agent.id)
    return user, claim


def test_analyze_answers_pending_and_persists_the_result(
    client, db_session, monkeypatch, shared_background_session
):
    monkeypatch.setattr(
        "app.llm.service.analyze_claim",
        lambda db, claim: {"claim_status": "supported", "severity": "low"},
    )
    user, claim = _actor_and_claim(db_session)

    resp = client.post(f"/claims/{claim.id}/analyze", headers=auth_headers(user))
    assert resp.status_code == 202
    assert resp.json()["analysis_status"] == "pending"

    after = client.get(f"/claims/{claim.id}", headers=auth_headers(user)).json()
    assert after["analysis_status"] == "done"
    assert after["claim_status"] == "supported"
    assert after["severity"] == "low"


def test_a_failed_analysis_marks_the_claim_and_leaves_it_untouched(
    client, db_session, monkeypatch, shared_background_session
):
    def _boom(db, claim):
        raise RuntimeError("OpenRouter failed after 4 attempts: connection refused")

    monkeypatch.setattr("app.llm.service.analyze_claim", _boom)
    user, claim = _actor_and_claim(db_session)

    resp = client.post(f"/claims/{claim.id}/analyze", headers=auth_headers(user))
    assert resp.status_code == 202

    after = client.get(f"/claims/{claim.id}", headers=auth_headers(user)).json()
    assert after["analysis_status"] == "failed"
    assert after["claim_status"] == "not_enough_information"


def test_a_second_analyze_while_one_is_pending_is_rejected(client, db_session):
    user, claim = _actor_and_claim(db_session)
    claim.analysis_status = "pending"
    db_session.commit()

    resp = client.post(f"/claims/{claim.id}/analyze", headers=auth_headers(user))
    assert resp.status_code == 409


def test_a_failed_analysis_can_be_retried(
    client, db_session, monkeypatch, shared_background_session
):
    monkeypatch.setattr(
        "app.llm.service.analyze_claim", lambda db, claim: {"claim_status": "supported"}
    )
    user, claim = _actor_and_claim(db_session)
    claim.analysis_status = "failed"
    db_session.commit()

    resp = client.post(f"/claims/{claim.id}/analyze", headers=auth_headers(user))
    assert resp.status_code == 202
    after = client.get(f"/claims/{claim.id}", headers=auth_headers(user)).json()
    assert after["analysis_status"] == "done"


def test_demo_mode_serves_a_canned_analysis_in_one_round_trip(client, db_session, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "demo_mode", True)
    user, claim = _actor_and_claim(db_session)

    resp = client.post(f"/claims/{claim.id}/analyze", headers=auth_headers(user))
    assert resp.status_code == 202
    body = resp.json()
    assert body["analysis_status"] == "done"
    assert body["claim_status"] == "supported"
    assert "Demo mode" in body["claim_status_justification"]
