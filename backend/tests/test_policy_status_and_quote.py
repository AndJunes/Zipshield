"""Regression tests: PolicyStatus must include every state in ALLOWED_TRANSITIONS (such
as 'pending_info'), and quote_policy with a nonexistent client_id must fail instead of
silently falling back to risk_factor=1.0."""

from app.policies.schemas import PolicyStatus
from app.policies.service import ALLOWED_TRANSITIONS
from tests.conftest import auth_headers, make_agent, make_client, make_supervisor, make_user


def test_policy_status_enum_matches_every_state_in_the_transition_table():
    """No state that appears in ALLOWED_TRANSITIONS (as a key or a target) should be
    missing from the public enum — otherwise it is reachable in the DB but
    unrepresentable/unvalidatable in the API."""
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
    """client_id is optional — without it, the quote uses risk_factor=1.0 by design."""
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    resp = client.post(
        "/policies/quote",
        json={"type": "car", "sum_insured": "18000.00"},
        headers=auth_headers(user),
    )
    assert resp.status_code == 200
