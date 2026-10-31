"""Claim creation regression tests: create_claim must verify the referenced policy
belongs to the claiming user, and date_of_loss must reject future dates."""

from datetime import date, timedelta

from tests.conftest import auth_headers, make_agent, make_client, make_policy, make_supervisor, make_user


def _base_payload(user_id: str, policy_id: int, date_of_loss: str) -> dict:
    return {
        "user_id": user_id,
        "object": "car",
        "conversation": "I crashed the car",
        "image_urls": [],
        "policy_id": policy_id,
        "date_of_loss": date_of_loss,
    }


def test_create_claim_with_own_policy_succeeds(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    policy = make_policy(db_session, owner)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    payload = _base_payload(owner.user_id, policy.id, str(date.today()))
    resp = client.post("/claims", json=payload, headers=auth_headers(user))
    assert resp.status_code == 201


def test_create_claim_rejects_policy_of_another_user(client, db_session):
    """The policy exists and is in force, but belongs to ANOTHER client."""
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    stranger = make_client(db_session, agent)
    policy_of_owner = make_policy(db_session, owner)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    payload = _base_payload(stranger.user_id, policy_of_owner.id, str(date.today()))
    resp = client.post("/claims", json=payload, headers=auth_headers(user))
    assert resp.status_code == 409


def test_create_claim_rejects_nonexistent_policy(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    payload = _base_payload(owner.user_id, 999999, str(date.today()))
    resp = client.post("/claims", json=payload, headers=auth_headers(user))
    assert resp.status_code == 404


def test_create_claim_rejects_future_date_of_loss(client, db_session):
    """A loss cannot have happened 'tomorrow'."""
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    policy = make_policy(db_session, owner)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    tomorrow = str(date.today() + timedelta(days=1))
    payload = _base_payload(owner.user_id, policy.id, tomorrow)
    resp = client.post("/claims", json=payload, headers=auth_headers(user))
    assert resp.status_code == 422


def test_create_claim_accepts_date_of_loss_today(client, db_session):
    """Edge case: today is still valid (the limit is 'not in the future')."""
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    policy = make_policy(db_session, owner)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    payload = _base_payload(owner.user_id, policy.id, str(date.today()))
    resp = client.post("/claims", json=payload, headers=auth_headers(user))
    assert resp.status_code == 201
