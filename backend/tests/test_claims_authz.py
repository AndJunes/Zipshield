"""Regresión para BUG-02: `/claims/{id}` no verificaba propiedad (IDOR) y `PATCH`
permitía escribir directamente los 10 campos que solo la IA debería poder producir,
evadiendo el guardarraíl de `/analyze`."""

from tests.conftest import (
    auth_headers,
    make_agent,
    make_claim,
    make_client,
    make_supervisor,
    make_user,
)


def test_agent_can_read_and_patch_own_client_claim(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    own_client = make_client(db_session, agent)
    claim = make_claim(db_session, own_client)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    resp = client.get(f"/claims/{claim.id}", headers=auth_headers(user))
    assert resp.status_code == 200

    resp = client.patch(
        f"/claims/{claim.id}", json={"conversation": "actualizado"}, headers=auth_headers(user)
    )
    assert resp.status_code == 200
    assert resp.json()["conversation"] == "actualizado"


def test_agent_cannot_read_another_agents_client_claim(client, db_session):
    supervisor = make_supervisor(db_session)
    agent_a = make_agent(db_session, supervisor)
    agent_b = make_agent(db_session, supervisor)
    client_of_b = make_client(db_session, agent_b)
    claim_of_b = make_claim(db_session, client_of_b)
    user_a = make_user(db_session, role="agent", ref_id=agent_a.id)

    resp = client.get(f"/claims/{claim_of_b.id}", headers=auth_headers(user_a))
    assert resp.status_code == 404


def test_agent_cannot_patch_another_agents_client_claim(client, db_session):
    supervisor = make_supervisor(db_session)
    agent_a = make_agent(db_session, supervisor)
    agent_b = make_agent(db_session, supervisor)
    client_of_b = make_client(db_session, agent_b)
    claim_of_b = make_claim(db_session, client_of_b)
    user_a = make_user(db_session, role="agent", ref_id=agent_a.id)

    resp = client.patch(
        f"/claims/{claim_of_b.id}", json={"conversation": "hackeado"}, headers=auth_headers(user_a)
    )
    assert resp.status_code == 404


def test_agent_cannot_trigger_analyze_on_another_agents_client_claim(client, db_session):
    supervisor = make_supervisor(db_session)
    agent_a = make_agent(db_session, supervisor)
    agent_b = make_agent(db_session, supervisor)
    client_of_b = make_client(db_session, agent_b)
    claim_of_b = make_claim(db_session, client_of_b)
    user_a = make_user(db_session, role="agent", ref_id=agent_a.id)

    resp = client.post(f"/claims/{claim_of_b.id}/analyze", headers=auth_headers(user_a))
    assert resp.status_code == 404


def test_patch_cannot_set_analysis_fields_directly(client, db_session):
    """El campo antes explotable: PATCH ya no acepta claim_status/severity/etc."""
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    own_client = make_client(db_session, agent)
    claim = make_claim(db_session, own_client)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    resp = client.patch(
        f"/claims/{claim.id}",
        json={
            "claim_status": "supported",
            "evidence_standard_met": True,
            "valid_image": True,
            "severity": "high",
        },
        headers=auth_headers(user),
    )
    assert resp.status_code == 200  # los campos desconocidos se ignoran, no rompen la petición
    db_session.refresh(claim)
    assert claim.claim_status == "not_enough_information"
    assert claim.evidence_standard_met is False
    assert claim.severity == "unknown"


def test_supervisor_can_read_claim_of_their_team(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    team_client = make_client(db_session, agent)
    claim = make_claim(db_session, team_client)
    sup_user = make_user(db_session, role="supervisor", ref_id=supervisor.id)

    resp = client.get(f"/claims/{claim.id}", headers=auth_headers(sup_user))
    assert resp.status_code == 200


def test_admin_can_read_any_claim(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    some_client = make_client(db_session, agent)
    claim = make_claim(db_session, some_client)
    admin_user = make_user(db_session, role="admin")

    resp = client.get(f"/claims/{claim.id}", headers=auth_headers(admin_user))
    assert resp.status_code == 200
