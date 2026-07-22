"""Regresión para A4 (PolicyStatus no incluía 'pending_info', que sí existe en
ALLOWED_TRANSITIONS) y A5 (quote_policy con un client_id inexistente caía en silencio a
risk_factor=1.0 en vez de fallar)."""

from app.policies.schemas import PolicyStatus
from app.policies.service import ALLOWED_TRANSITIONS
from tests.conftest import auth_headers, make_agent, make_client, make_supervisor, make_user


def test_policy_status_enum_matches_every_state_in_the_transition_table():
    """Ningún estado que aparece en ALLOWED_TRANSITIONS (como clave o como destino)
    debería quedar fuera del enum público — si no, es alcanzable en la BD pero
    irrepresentable/no validable en la API."""
    states_in_machine = set(ALLOWED_TRANSITIONS.keys())
    for targets in ALLOWED_TRANSITIONS.values():
        states_in_machine |= targets
    enum_values = {s.value for s in PolicyStatus}
    assert states_in_machine <= enum_values


def test_quote_with_nonexistent_client_id_returns_404(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    resp = client.post(
        "/policies/quote",
        json={"type": "car", "sum_insured": "18000.00", "client_id": 999999},
        headers=auth_headers(user),
    )
    assert resp.status_code == 404


def test_quote_with_valid_client_id_succeeds(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    resp = client.post(
        "/policies/quote",
        json={"type": "car", "sum_insured": "18000.00", "client_id": owner.id},
        headers=auth_headers(user),
    )
    assert resp.status_code == 200


def test_quote_without_client_id_still_works(client, db_session):
    """client_id es opcional — sin él, se cotiza con risk_factor=1.0 por diseño."""
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    resp = client.post(
        "/policies/quote",
        json={"type": "car", "sum_insured": "18000.00"},
        headers=auth_headers(user),
    )
    assert resp.status_code == 200
