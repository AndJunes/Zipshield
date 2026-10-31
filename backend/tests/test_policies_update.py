"""Policy update regression tests: `update_policy` must enforce the state-machine guard,
validate date ordering, and leave an audit trail (`PolicyEvent`)."""

from datetime import date, timedelta

from tests.conftest import auth_headers, make_agent, make_client, make_policy, make_supervisor, make_user


def _agent_and_policy(db_session, **policy_overrides):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    policy = make_policy(db_session, owner, **policy_overrides)
    user = make_user(db_session, role="agent", ref_id=agent.id)
    return user, policy


def test_update_in_force_policy_succeeds_and_records_event(client, db_session):
    user, policy = _agent_and_policy(db_session)

    resp = client.patch(
        f"/policies/{policy.id}", json={"name": "Renamed policy"}, headers=auth_headers(user)
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed policy"

    resp = client.get(f"/policies/{policy.id}/events", headers=auth_headers(user))
    assert resp.status_code == 200
    assert any(e["event_type"] == "updated" for e in resp.json())


def test_cannot_update_a_cancelled_policy(client, db_session):
    user, policy = _agent_and_policy(db_session, status="cancelled")

    resp = client.patch(
        f"/policies/{policy.id}", json={"name": "should not apply"}, headers=auth_headers(user)
    )
    assert resp.status_code == 409
    db_session.refresh(policy)
    assert policy.name != "should not apply"


def test_cannot_update_an_expired_policy(client, db_session):
    user, policy = _agent_and_policy(db_session, status="expired")

    resp = client.patch(
        f"/policies/{policy.id}", json={"coverage": "anything"}, headers=auth_headers(user)
    )
    assert resp.status_code == 409


def test_expiration_date_before_effective_date_is_rejected(client, db_session):
    user, policy = _agent_and_policy(db_session)
    too_early = str(policy.effective_date - timedelta(days=1))

    resp = client.patch(
        f"/policies/{policy.id}", json={"expiration_date": too_early}, headers=auth_headers(user)
    )
    assert resp.status_code == 409
    db_session.refresh(policy)
    assert str(policy.expiration_date) != too_early


def test_expiration_date_equal_to_effective_date_is_allowed(client, db_session):
    """Edge case: the same day is valid; only EARLIER dates are rejected."""
    user, policy = _agent_and_policy(db_session)
    same_day = str(policy.effective_date)

    resp = client.patch(
        f"/policies/{policy.id}", json={"expiration_date": same_day}, headers=auth_headers(user)
    )
    assert resp.status_code == 200
