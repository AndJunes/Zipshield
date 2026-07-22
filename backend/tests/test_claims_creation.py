"""Regresión para BUG-08 (create_claim no verificaba que la póliza citada perteneciera
al usuario reclamante) y A2 (date_of_loss aceptaba fechas futuras)."""

from datetime import date, timedelta

from tests.conftest import auth_headers, make_agent, make_client, make_policy, make_supervisor, make_user


def _base_payload(user_id: str, policy_id: int, date_of_loss: str) -> dict:
    return {
        "user_id": user_id,
        "object": "car",
        "conversation": "Choqué el auto",
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
    """BUG-08: la póliza existe y está vigente, pero pertenece a OTRO cliente."""
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
    """A2: una pérdida no puede haber ocurrido 'mañana'."""
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
    """Caso límite: hoy mismo sigue siendo válido (el límite es 'no en el futuro')."""
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    policy = make_policy(db_session, owner)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    payload = _base_payload(owner.user_id, policy.id, str(date.today()))
    resp = client.post("/claims", json=payload, headers=auth_headers(user))
    assert resp.status_code == 201
