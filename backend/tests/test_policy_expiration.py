"""Policy expiration regression tests: a lapsed policy must be moved to `expired`
automatically, so `/policies/balance` stops counting it as active forever, and the
dashboard must not compare against the string "active" (which no Policy.status ever
uses) and report 0 active policies regardless of the real data."""

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
    """A cancelled policy, even when its expiration date is also in the past, must not
    become 'expired' — the client cancelled it, they did not let it lapse."""
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
    """dashboard_summary must not compare against the string 'active', which no
    Policy.status ever uses — active_policies would always be 0 regardless of the data."""
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
    # Another cancelled policy with a past date: it must NOT count as "expired".
    make_policy(
        db_session,
        make_client(db_session, make_agent(db_session, make_supervisor(db_session))),
        status="cancelled",
        expiration_date=date.today() - timedelta(days=10),
        cancel_date=date.today() - timedelta(days=15),
    )

    resp = client.get("/dashboard", headers=auth_headers(admin_user))
    assert resp.status_code == 200
    # sync_expired_policies already ran (via /dashboard); the in_force one becomes
    # expired, the cancelled one stays cancelled -> exactly 1 real "expired".
    assert resp.json()["expired_policies"] == 1
