"""Regresión para BUG-15: ninguna transición automática movía una póliza vencida a
`expired`, así que `/policies/balance` seguía contándola como vigente para siempre,
mientras que el dashboard (por su propio bug de comparar contra el string "active", que
nunca existe) reportaba 0 pólizas activas sin importar los datos reales."""

from datetime import date, timedelta

from tests.conftest import auth_headers, make_agent, make_client, make_policy, make_supervisor, make_user


def _lapsed_policy(db_session, **overrides):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    defaults = dict(
        status="in_force",
        effective_date=date.today() - timedelta(days=400),
        expiration_date=date.today() - timedelta(days=35),
    )
    defaults.update(overrides)
    policy = make_policy(db_session, owner, **defaults)
    user = make_user(db_session, role="agent", ref_id=agent.id)
    return user, policy


def test_get_policies_transitions_a_lapsed_policy_to_expired(client, db_session):
    user, policy = _lapsed_policy(db_session)

    resp = client.get("/policies", headers=auth_headers(user))
    assert resp.status_code == 200

    db_session.refresh(policy)
    assert policy.status == "expired"
    assert any(e.event_type == "expired" for e in policy.events)


def test_pending_cancel_policy_also_expires_once_lapsed(client, db_session):
    user, policy = _lapsed_policy(db_session, status="pending_cancel")

    client.get(f"/policies/{policy.id}", headers=auth_headers(user))

    db_session.refresh(policy)
    assert policy.status == "expired"


def test_already_cancelled_policy_is_not_reclassified_as_expired(client, db_session):
    """Una póliza cancelada, aunque su fecha de vencimiento también quedó en el pasado,
    no debe convertirse en 'expired' — el cliente la canceló, no dejó que venciera."""
    user, policy = _lapsed_policy(db_session, status="cancelled", cancel_date=date.today() - timedelta(days=40))

    client.get(f"/policies/{policy.id}", headers=auth_headers(user))

    db_session.refresh(policy)
    assert policy.status == "cancelled"


def test_active_policies_balance_excludes_a_lapsed_policy(client, db_session):
    user, policy = _lapsed_policy(db_session)

    resp = client.get("/policies/balance", headers=auth_headers(user))
    assert resp.status_code == 200
    assert resp.json()["active_policies"] == 0


def test_dashboard_reports_in_force_policies_as_active_not_zero(client, db_session):
    """Antes del fix, dashboard_summary comparaba contra el string 'active', que ningún
    Policy.status usa jamás — active_policies daba 0 siempre, sin importar los datos."""
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    make_policy(db_session, owner, status="in_force")
    admin_user = make_user(db_session, role="admin")

    resp = client.get("/dashboard", headers=auth_headers(admin_user))
    assert resp.status_code == 200
    body = resp.json()
    assert body["active_policies"] == 1
    assert body["active_policies_value"] > 0


def test_dashboard_expired_count_matches_status_not_just_date(client, db_session):
    user, lapsed_policy = _lapsed_policy(db_session)
    admin_user = make_user(db_session, role="admin")
    # Otra póliza cancelada con fecha pasada: NO debe contarse como "expired".
    make_policy(
        db_session,
        make_client(db_session, make_agent(db_session, make_supervisor(db_session))),
        status="cancelled",
        expiration_date=date.today() - timedelta(days=10),
        cancel_date=date.today() - timedelta(days=15),
    )

    resp = client.get("/dashboard", headers=auth_headers(admin_user))
    assert resp.status_code == 200
    # sync_expired_policies ya corrió (via /dashboard); la de in_force pasa a expired,
    # la cancelada se queda cancelada -> exactamente 1 "expired" real.
    assert resp.json()["expired_policies"] == 1
