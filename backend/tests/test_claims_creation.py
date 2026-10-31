"""Claim creation rules: the claimant is derived from the policy on the server,
the policy must be inside the actor's scope, and date_of_loss can't be in the
future."""

from datetime import date, timedelta

from tests.conftest import (
    auth_headers,
    make_agent,
    make_client,
    make_policy,
    make_supervisor,
    make_user,
)


def _payload(policy_id: int, date_of_loss: str) -> dict:
    return {
        "object": "car",
        "conversation": "I crashed the car",
        "image_urls": [],
        "policy_id": policy_id,
        "date_of_loss": date_of_loss,
    }


def _book(db_session):
    """A supervisor -> agent -> client -> policy chain."""
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    policy = make_policy(db_session, owner)
    return supervisor, agent, owner, policy


def test_agent_creates_a_claim_for_their_own_client(client, db_session):
    _, agent, owner, policy = _book(db_session)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    resp = client.post(
        "/claims", json=_payload(policy.id, str(date.today())), headers=auth_headers(user)
    )
    assert resp.status_code == 201
    assert resp.json()["user_id"] == owner.user_id


def test_claimant_comes_from_the_policy_not_the_body(client, db_session):
    """A user_id smuggled into the body is ignored; the server derives it."""
    _, agent, owner, policy = _book(db_session)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    payload = _payload(policy.id, str(date.today())) | {"user_id": "user_somebody_else"}
    resp = client.post("/claims", json=payload, headers=auth_headers(user))
    assert resp.status_code == 201
    assert resp.json()["user_id"] == owner.user_id


def test_agent_cannot_file_on_another_agents_policy(client, db_session):
    """Out-of-scope policies look nonexistent, even with a matching user_id in the body."""
    supervisor, agent, owner, policy = _book(db_session)
    other_agent = make_agent(db_session, supervisor)
    outsider = make_user(db_session, role="agent", ref_id=other_agent.id)

    payload = _payload(policy.id, str(date.today())) | {"user_id": owner.user_id}
    resp = client.post("/claims", json=payload, headers=auth_headers(outsider))
    assert resp.status_code == 404


def test_supervisor_scope_covers_their_agents_only(client, db_session):
    supervisor, agent, owner, policy = _book(db_session)
    same_branch = make_user(db_session, role="supervisor", ref_id=supervisor.id)
    other_branch = make_user(
        db_session, role="supervisor", ref_id=make_supervisor(db_session).id
    )

    ok = client.post(
        "/claims", json=_payload(policy.id, str(date.today())), headers=auth_headers(same_branch)
    )
    assert ok.status_code == 201

    denied = client.post(
        "/claims", json=_payload(policy.id, str(date.today())), headers=auth_headers(other_branch)
    )
    assert denied.status_code == 404


def test_admin_can_file_for_any_client(client, db_session):
    *_, policy = _book(db_session)
    admin = make_user(db_session, role="admin")

    resp = client.post(
        "/claims", json=_payload(policy.id, str(date.today())), headers=auth_headers(admin)
    )
    assert resp.status_code == 201


def test_nonexistent_policy_is_a_404(client, db_session):
    _, agent, _, _ = _book(db_session)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    resp = client.post(
        "/claims", json=_payload(999999, str(date.today())), headers=auth_headers(user)
    )
    assert resp.status_code == 404


def test_policy_id_is_required(client, db_session):
    _, agent, _, _ = _book(db_session)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    payload = _payload(1, str(date.today()))
    del payload["policy_id"]
    resp = client.post("/claims", json=payload, headers=auth_headers(user))
    assert resp.status_code == 422


def test_future_date_of_loss_is_rejected(client, db_session):
    """A loss cannot have happened 'tomorrow'."""
    _, agent, _, policy = _book(db_session)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    tomorrow = str(date.today() + timedelta(days=1))
    resp = client.post("/claims", json=_payload(policy.id, tomorrow), headers=auth_headers(user))
    assert resp.status_code == 422


def test_date_of_loss_today_is_valid(client, db_session):
    """Edge case: today is still valid (the limit is 'not in the future')."""
    _, agent, _, policy = _book(db_session)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    resp = client.post(
        "/claims", json=_payload(policy.id, str(date.today())), headers=auth_headers(user)
    )
    assert resp.status_code == 201


def test_patch_cannot_repoint_a_claim_at_an_out_of_scope_policy(client, db_session):
    supervisor, agent, owner, policy = _book(db_session)
    user = make_user(db_session, role="agent", ref_id=agent.id)
    created = client.post(
        "/claims", json=_payload(policy.id, str(date.today())), headers=auth_headers(user)
    )
    claim_id = created.json()["id"]

    other_supervisor = make_supervisor(db_session)
    other_agent = make_agent(db_session, other_supervisor)
    foreign_policy = make_policy(db_session, make_client(db_session, other_agent))

    resp = client.patch(
        f"/claims/{claim_id}", json={"policy_id": foreign_policy.id}, headers=auth_headers(user)
    )
    assert resp.status_code == 404


def test_patch_cannot_repoint_a_claim_at_another_clients_policy(client, db_session):
    supervisor, agent, owner, policy = _book(db_session)
    neighbor_policy = make_policy(db_session, make_client(db_session, agent))
    user = make_user(db_session, role="agent", ref_id=agent.id)
    created = client.post(
        "/claims", json=_payload(policy.id, str(date.today())), headers=auth_headers(user)
    )
    claim_id = created.json()["id"]

    resp = client.patch(
        f"/claims/{claim_id}", json={"policy_id": neighbor_policy.id}, headers=auth_headers(user)
    )
    assert resp.status_code == 409
