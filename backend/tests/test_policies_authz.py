"""Authorization regression tests for policies: /policies must be authorized — an
authenticated user must not see/edit/cancel arbitrary policies in the system."""

from tests.conftest import auth_headers, make_agent, make_client, make_policy, make_supervisor, make_user


def test_agent_can_list_and_read_own_client_policy(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    own_client = make_client(db_session, agent)
    policy = make_policy(db_session, own_client)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    resp = client.get("/policies", headers=auth_headers(user))
    assert resp.status_code == 200
    assert [p["id"] for p in resp.json()] == [policy.id]

    resp = client.get(f"/policies/{policy.id}", headers=auth_headers(user))
    assert resp.status_code == 200


def test_agent_cannot_list_another_agents_policy(client, db_session):
    supervisor = make_supervisor(db_session)
    agent_a = make_agent(db_session, supervisor)
    agent_b = make_agent(db_session, supervisor)
    client_of_b = make_client(db_session, agent_b)
    make_policy(db_session, client_of_b)
    user_a = make_user(db_session, role="agent", ref_id=agent_a.id)

    resp = client.get("/policies", headers=auth_headers(user_a))
    assert resp.status_code == 200
    assert resp.json() == []


def test_agent_cannot_read_another_agents_policy(client, db_session):
    supervisor = make_supervisor(db_session)
    agent_a = make_agent(db_session, supervisor)
    agent_b = make_agent(db_session, supervisor)
    client_of_b = make_client(db_session, agent_b)
    policy_of_b = make_policy(db_session, client_of_b)
    user_a = make_user(db_session, role="agent", ref_id=agent_a.id)

    resp = client.get(f"/policies/{policy_of_b.id}", headers=auth_headers(user_a))
    assert resp.status_code == 404


def test_agent_cannot_patch_another_agents_policy(client, db_session):
    supervisor = make_supervisor(db_session)
    agent_a = make_agent(db_session, supervisor)
    agent_b = make_agent(db_session, supervisor)
    client_of_b = make_client(db_session, agent_b)
    policy_of_b = make_policy(db_session, client_of_b)
    user_a = make_user(db_session, role="agent", ref_id=agent_a.id)

    resp = client.patch(
        f"/policies/{policy_of_b.id}",
        json={"expiration_date": "2020-01-01"},
        headers=auth_headers(user_a),
    )
    assert resp.status_code == 404


def test_agent_cannot_cancel_another_agents_policy(client, db_session):
    supervisor = make_supervisor(db_session)
    agent_a = make_agent(db_session, supervisor)
    agent_b = make_agent(db_session, supervisor)
    client_of_b = make_client(db_session, agent_b)
    policy_of_b = make_policy(db_session, client_of_b)
    user_a = make_user(db_session, role="agent", ref_id=agent_a.id)

    resp = client.delete(f"/policies/{policy_of_b.id}", headers=auth_headers(user_a))
    assert resp.status_code == 404
    db_session.refresh(policy_of_b)
    assert policy_of_b.status == "in_force"


def test_supervisor_can_read_policy_of_their_team(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    team_client = make_client(db_session, agent)
    policy = make_policy(db_session, team_client)
    sup_user = make_user(db_session, role="supervisor", ref_id=supervisor.id)

    resp = client.get(f"/policies/{policy.id}", headers=auth_headers(sup_user))
    assert resp.status_code == 200


def test_supervisor_cannot_read_policy_outside_their_team(client, db_session):
    supervisor_a = make_supervisor(db_session)
    supervisor_b = make_supervisor(db_session)
    agent_b = make_agent(db_session, supervisor_b)
    client_of_b_team = make_client(db_session, agent_b)
    policy_of_b_team = make_policy(db_session, client_of_b_team)
    sup_user_a = make_user(db_session, role="supervisor", ref_id=supervisor_a.id)

    resp = client.get(f"/policies/{policy_of_b_team.id}", headers=auth_headers(sup_user_a))
    assert resp.status_code == 404


def test_admin_can_read_and_patch_any_policy(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    some_client = make_client(db_session, agent)
    policy = make_policy(db_session, some_client)
    admin_user = make_user(db_session, role="admin")

    resp = client.get(f"/policies/{policy.id}", headers=auth_headers(admin_user))
    assert resp.status_code == 200

    resp = client.patch(
        f"/policies/{policy.id}", json={"name": "Renamed"}, headers=auth_headers(admin_user)
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"


def test_agent_cannot_read_events_of_another_agents_policy(client, db_session):
    supervisor = make_supervisor(db_session)
    agent_a = make_agent(db_session, supervisor)
    agent_b = make_agent(db_session, supervisor)
    client_of_b = make_client(db_session, agent_b)
    policy_of_b = make_policy(db_session, client_of_b)
    user_a = make_user(db_session, role="agent", ref_id=agent_a.id)

    resp = client.get(f"/policies/{policy_of_b.id}/events", headers=auth_headers(user_a))
    assert resp.status_code == 404
