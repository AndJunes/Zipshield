"""Regresión para BUG-03 (PATCH /agents/{id} sin ningún control de rol) y la parte de
BUG-06 sobre GET /agents/{id} (sin scoping por rol, a pesar de que `list_agents` ya lo
aplicaba vía `_filter_by_role`)."""

from tests.conftest import auth_headers, make_agent, make_supervisor, make_user


def test_agent_can_read_own_record(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    resp = client.get(f"/agents/{agent.id}", headers=auth_headers(user))
    assert resp.status_code == 200


def test_agent_cannot_read_another_agents_record(client, db_session):
    supervisor = make_supervisor(db_session)
    agent_a = make_agent(db_session, supervisor)
    agent_b = make_agent(db_session, supervisor)
    user_a = make_user(db_session, role="agent", ref_id=agent_a.id)

    resp = client.get(f"/agents/{agent_b.id}", headers=auth_headers(user_a))
    assert resp.status_code == 404


def test_agent_cannot_patch_any_agent(client, db_session):
    """BUG-03: antes del fix, un agente podía editar contribution/losses/supervisor_id
    de cualquier otro agente porque el PATCH no exigía ningún rol."""
    supervisor = make_supervisor(db_session)
    agent_a = make_agent(db_session, supervisor)
    agent_b = make_agent(db_session, supervisor)
    user_a = make_user(db_session, role="agent", ref_id=agent_a.id)

    resp = client.patch(
        f"/agents/{agent_b.id}", json={"contribution": "999999.00"}, headers=auth_headers(user_a)
    )
    assert resp.status_code == 403
    db_session.refresh(agent_b)
    assert agent_b.contribution == 0


def test_supervisor_can_patch_agent_on_their_team(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    sup_user = make_user(db_session, role="supervisor", ref_id=supervisor.id)

    resp = client.patch(
        f"/agents/{agent.id}", json={"city": "Monterrey"}, headers=auth_headers(sup_user)
    )
    assert resp.status_code == 200
    assert resp.json()["city"] == "Monterrey"


def test_supervisor_cannot_patch_agent_outside_their_team(client, db_session):
    supervisor_a = make_supervisor(db_session)
    supervisor_b = make_supervisor(db_session)
    agent_of_b = make_agent(db_session, supervisor_b)
    sup_user_a = make_user(db_session, role="supervisor", ref_id=supervisor_a.id)

    resp = client.patch(
        f"/agents/{agent_of_b.id}", json={"status": "inactive"}, headers=auth_headers(sup_user_a)
    )
    assert resp.status_code == 404
    db_session.refresh(agent_of_b)
    assert agent_of_b.status == "active"


def test_admin_can_patch_any_agent(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    admin_user = make_user(db_session, role="admin")

    resp = client.patch(
        f"/agents/{agent.id}", json={"city": "Guadalajara"}, headers=auth_headers(admin_user)
    )
    assert resp.status_code == 200


def test_supervisor_cannot_delete_agent_outside_their_team(client, db_session):
    supervisor_a = make_supervisor(db_session)
    supervisor_b = make_supervisor(db_session)
    agent_of_b = make_agent(db_session, supervisor_b)
    sup_user_a = make_user(db_session, role="supervisor", ref_id=supervisor_a.id)

    resp = client.delete(f"/agents/{agent_of_b.id}", headers=auth_headers(sup_user_a))
    assert resp.status_code == 404
