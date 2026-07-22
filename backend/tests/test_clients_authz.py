"""Regresión para BUG-04: GET/PATCH/DELETE /clients/{id} sin scoping por rol (IDOR).

Antes del fix, `_get_client_orm` no comparaba nada contra `current_user` — cualquier
usuario autenticado podía leer/editar/desactivar el cliente de cualquier agente.
"""

from tests.conftest import auth_headers, make_agent, make_client, make_supervisor, make_user


def test_agent_can_read_and_update_own_client(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    own_client = make_client(db_session, agent)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    resp = client.get(f"/clients/{own_client.id}", headers=auth_headers(user))
    assert resp.status_code == 200
    assert resp.json()["id"] == own_client.id

    resp = client.patch(
        f"/clients/{own_client.id}", json={"city": "CDMX"}, headers=auth_headers(user)
    )
    assert resp.status_code == 200
    assert resp.json()["city"] == "CDMX"


def test_agent_cannot_read_another_agents_client(client, db_session):
    supervisor = make_supervisor(db_session)
    agent_a = make_agent(db_session, supervisor)
    agent_b = make_agent(db_session, supervisor)
    client_of_b = make_client(db_session, agent_b)
    user_a = make_user(db_session, role="agent", ref_id=agent_a.id)

    resp = client.get(f"/clients/{client_of_b.id}", headers=auth_headers(user_a))
    assert resp.status_code == 404


def test_agent_cannot_patch_another_agents_client(client, db_session):
    supervisor = make_supervisor(db_session)
    agent_a = make_agent(db_session, supervisor)
    agent_b = make_agent(db_session, supervisor)
    client_of_b = make_client(db_session, agent_b)
    user_a = make_user(db_session, role="agent", ref_id=agent_a.id)

    resp = client.patch(
        f"/clients/{client_of_b.id}", json={"status": "inactive"}, headers=auth_headers(user_a)
    )
    assert resp.status_code == 404
    db_session.refresh(client_of_b)
    assert client_of_b.status == "active"


def test_agent_cannot_delete_another_agents_client(client, db_session):
    supervisor = make_supervisor(db_session)
    agent_a = make_agent(db_session, supervisor)
    agent_b = make_agent(db_session, supervisor)
    client_of_b = make_client(db_session, agent_b)
    user_a = make_user(db_session, role="agent", ref_id=agent_a.id)

    resp = client.delete(f"/clients/{client_of_b.id}", headers=auth_headers(user_a))
    assert resp.status_code == 404
    db_session.refresh(client_of_b)
    assert client_of_b.status == "active"


def test_supervisor_can_access_client_of_their_team(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    team_client = make_client(db_session, agent)
    sup_user = make_user(db_session, role="supervisor", ref_id=supervisor.id)

    resp = client.get(f"/clients/{team_client.id}", headers=auth_headers(sup_user))
    assert resp.status_code == 200


def test_supervisor_cannot_access_client_outside_their_team(client, db_session):
    supervisor_a = make_supervisor(db_session)
    supervisor_b = make_supervisor(db_session)
    agent_b = make_agent(db_session, supervisor_b)
    client_of_b_team = make_client(db_session, agent_b)
    sup_user_a = make_user(db_session, role="supervisor", ref_id=supervisor_a.id)

    resp = client.get(f"/clients/{client_of_b_team.id}", headers=auth_headers(sup_user_a))
    assert resp.status_code == 404


def test_admin_can_access_any_client(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    some_client = make_client(db_session, agent)
    admin_user = make_user(db_session, role="admin")

    resp = client.get(f"/clients/{some_client.id}", headers=auth_headers(admin_user))
    assert resp.status_code == 200


def test_client_update_can_no_longer_reassign_agent(client, db_session):
    """BUG-04, parte 2: `agent_id` ya no es un campo editable vía PATCH genérico."""
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    other_agent = make_agent(db_session, supervisor)
    own_client = make_client(db_session, agent)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    resp = client.patch(
        f"/clients/{own_client.id}",
        json={"agent_id": other_agent.id},
        headers=auth_headers(user),
    )
    assert resp.status_code == 200  # el campo desconocido se ignora, no rompe la petición
    db_session.refresh(own_client)
    assert own_client.agent_id == agent.id  # nunca se reasignó
