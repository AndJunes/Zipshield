"""N+1 regression tests: the `clients`, `agents`, `supervisors` and `policies` listings
must not run one extra query PER ROW (claim history, client/agent counts, policy
coverages) instead of a single aggregated query.

Rather than pinning a magic query count, each test compares the count with few rows
against the count with many more — with N+1 the difference would scale with the number
of new rows; with batched aggregation it must be practically zero.
"""

from contextlib import contextmanager

from sqlalchemy import event

from app.core.database import engine
from tests.conftest import (
    auth_headers,
    make_agent,
    make_claim,
    make_client,
    make_policy,
    make_supervisor,
    make_user,
)


@contextmanager
def count_queries():
    counter = {"n": 0}

    def _on_execute(conn, cursor, statement, parameters, context, executemany):
        counter["n"] += 1

    event.listen(engine, "before_cursor_execute", _on_execute)
    try:
        yield counter
    finally:
        event.remove(engine, "before_cursor_execute", _on_execute)


def test_list_clients_query_count_does_not_scale_with_number_of_clients(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    for _ in range(2):
        c = make_client(db_session, agent)
        make_claim(db_session, c)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    with count_queries() as small:
        resp = client.get("/clients", headers=auth_headers(user))
    assert resp.status_code == 200 and len(resp.json()) == 2

    for _ in range(8):
        c = make_client(db_session, agent)
        make_claim(db_session, c)

    with count_queries() as large:
        resp = client.get("/clients", headers=auth_headers(user))
    assert resp.status_code == 200 and len(resp.json()) == 10

    assert large["n"] - small["n"] <= 1


def test_list_agents_query_count_does_not_scale_with_number_of_agents(client, db_session):
    supervisor = make_supervisor(db_session)
    for _ in range(2):
        a = make_agent(db_session, supervisor)
        c = make_client(db_session, a)
        make_claim(db_session, c)
    admin_user = make_user(db_session, role="admin")

    with count_queries() as small:
        resp = client.get("/agents", headers=auth_headers(admin_user))
    assert resp.status_code == 200 and len(resp.json()) == 2

    for _ in range(8):
        a = make_agent(db_session, supervisor)
        c = make_client(db_session, a)
        make_claim(db_session, c)

    with count_queries() as large:
        resp = client.get("/agents", headers=auth_headers(admin_user))
    assert resp.status_code == 200 and len(resp.json()) == 10

    assert large["n"] - small["n"] <= 1


def test_list_supervisors_query_count_does_not_scale_with_number_of_supervisors(client, db_session):
    for _ in range(2):
        s = make_supervisor(db_session)
        make_agent(db_session, s)
    admin_user = make_user(db_session, role="admin")

    with count_queries() as small:
        resp = client.get("/supervisors", headers=auth_headers(admin_user))
    assert resp.status_code == 200 and len(resp.json()) == 2

    for _ in range(8):
        s = make_supervisor(db_session)
        make_agent(db_session, s)

    with count_queries() as large:
        resp = client.get("/supervisors", headers=auth_headers(admin_user))
    assert resp.status_code == 200 and len(resp.json()) == 10

    assert large["n"] - small["n"] <= 1


def test_list_policies_query_count_does_not_scale_with_number_of_policies(client, db_session):
    supervisor = make_supervisor(db_session)
    agent = make_agent(db_session, supervisor)
    owner = make_client(db_session, agent)
    for _ in range(2):
        make_policy(db_session, owner)
    user = make_user(db_session, role="agent", ref_id=agent.id)

    with count_queries() as small:
        resp = client.get("/policies", headers=auth_headers(user))
    assert resp.status_code == 200 and len(resp.json()) == 2

    for _ in range(8):
        make_policy(db_session, owner)

    with count_queries() as large:
        resp = client.get("/policies", headers=auth_headers(user))
    assert resp.status_code == 200 and len(resp.json()) == 10

    assert large["n"] - small["n"] <= 1
