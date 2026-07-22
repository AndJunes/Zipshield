"""Regresión para la parte de BUG-06 sobre supervisores: GET /supervisors/{id} no exigía
ningún rol (un agente que ve 0 supervisores en el listado podía leer el detalle de
cualquiera igual), y PATCH exigía rol pero no pertenencia (un supervisor podía editar a
un supervisor par)."""

from tests.conftest import auth_headers, make_supervisor, make_user


def test_supervisor_can_read_and_patch_own_record(client, db_session):
    supervisor = make_supervisor(db_session)
    sup_user = make_user(db_session, role="supervisor", ref_id=supervisor.id)

    resp = client.get(f"/supervisors/{supervisor.id}", headers=auth_headers(sup_user))
    assert resp.status_code == 200

    resp = client.patch(
        f"/supervisors/{supervisor.id}", json={"city": "Puebla"}, headers=auth_headers(sup_user)
    )
    assert resp.status_code == 200
    assert resp.json()["city"] == "Puebla"


def test_agent_cannot_read_any_supervisor(client, db_session):
    supervisor = make_supervisor(db_session)
    agent_user = make_user(db_session, role="agent", ref_id=1)

    resp = client.get(f"/supervisors/{supervisor.id}", headers=auth_headers(agent_user))
    assert resp.status_code == 403


def test_supervisor_cannot_read_a_peer_supervisor(client, db_session):
    supervisor_a = make_supervisor(db_session)
    supervisor_b = make_supervisor(db_session)
    user_a = make_user(db_session, role="supervisor", ref_id=supervisor_a.id)

    resp = client.get(f"/supervisors/{supervisor_b.id}", headers=auth_headers(user_a))
    assert resp.status_code == 404


def test_supervisor_cannot_patch_a_peer_supervisor(client, db_session):
    supervisor_a = make_supervisor(db_session)
    supervisor_b = make_supervisor(db_session)
    user_a = make_user(db_session, role="supervisor", ref_id=supervisor_a.id)

    resp = client.patch(
        f"/supervisors/{supervisor_b.id}",
        json={"contribution": "50000.00"},
        headers=auth_headers(user_a),
    )
    assert resp.status_code == 404
    db_session.refresh(supervisor_b)
    assert supervisor_b.contribution == 0


def test_admin_can_read_and_patch_any_supervisor(client, db_session):
    supervisor = make_supervisor(db_session)
    admin_user = make_user(db_session, role="admin")

    resp = client.get(f"/supervisors/{supervisor.id}", headers=auth_headers(admin_user))
    assert resp.status_code == 200

    resp = client.patch(
        f"/supervisors/{supervisor.id}", json={"city": "Tijuana"}, headers=auth_headers(admin_user)
    )
    assert resp.status_code == 200
