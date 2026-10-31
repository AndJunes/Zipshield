"""Shared test infrastructure.

Uses a SQLite database in a temporary file (not `:memory:`, to avoid the "a different
in-memory DB per connection" problem) instead of the real Postgres from `DATABASE_URL`,
so the suite runs without Docker/Postgres up.

`DATABASE_URL` is set BEFORE importing any `app` module, because `app.core.database`
builds the engine from `get_settings()` at import time.

The real schema is owned by Alembic, but the migration chain contains
Postgres-only DDL, so the test database is built with `create_all` instead.
"""

import os
import tempfile
import uuid
from datetime import date, timedelta
from decimal import Decimal

os.environ.setdefault("JWT_SECRET", "test-only-secret-not-for-prod")
os.environ.setdefault("ENVIRONMENT", "test")

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.database import Base, SessionLocal, engine, get_db
from app.core.security import create_access_token, hash_password
from app.main import app

from app.auth.models import User
from app.agents.models import Agent
from app.clients.models import Client
from app.supervisors.models import Supervisor
from app.policies.models import Policy
from app.claims.models import ClaimCase

# Build the test schema directly: Alembic owns the real one, but the migration
# chain contains Postgres-only DDL and this suite runs on SQLite.
Base.metadata.create_all(bind=engine)

# The `pysqlite` driver manages its own BEGIN/COMMIT underneath SQLAlchemy (the stdlib's
# implicit autocommit), which breaks the "savepoint per test" pattern of `db_session`
# below: a `session.commit()` from the app ended up committing the real transaction
# instead of just the savepoint, and the final rollback undid nothing. This is the
# workaround SQLAlchemy's own docs recommend for transaction isolation with SQLite.
@event.listens_for(engine, "connect")
def _sqlite_disable_pysqlite_autocommit(dbapi_connection, connection_record):
    dbapi_connection.isolation_level = None


@event.listens_for(engine, "begin")
def _sqlite_emit_explicit_begin(conn):
    conn.exec_driver_sql("BEGIN")


@pytest.fixture()
def db_session():
    """A session bound to a single connection + savepoint: any `commit()` the app code
    makes stays within the savepoint, and everything is rolled back when the test ends."""
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = SessionLocal(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    """TestClient with `get_db` overridden to use the test session (same transaction)."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def make_supervisor(db_session, **overrides) -> Supervisor:
    defaults = dict(
        first_name="Sup",
        last_name=_unique("Test"),
        email=f"{_unique('supervisor')}@example.com",
        status="active",
    )
    defaults.update(overrides)
    supervisor = Supervisor(**defaults)
    db_session.add(supervisor)
    db_session.commit()
    db_session.refresh(supervisor)
    return supervisor


def make_agent(db_session, supervisor: Supervisor, **overrides) -> Agent:
    defaults = dict(
        first_name="Agent",
        last_name=_unique("Test"),
        email=f"{_unique('agent')}@example.com",
        agent_number=_unique("AG"),
        status="active",
        supervisor_id=supervisor.id,
    )
    defaults.update(overrides)
    agent = Agent(**defaults)
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


def make_client(db_session, agent: Agent, **overrides) -> Client:
    defaults = dict(
        user_id=_unique("user"),
        first_name="Client",
        last_name=_unique("Test"),
        email=f"{_unique('client')}@example.com",
        client_number=_unique("CL"),
        status="active",
        agent_id=agent.id,
    )
    defaults.update(overrides)
    client_row = Client(**defaults)
    db_session.add(client_row)
    db_session.commit()
    db_session.refresh(client_row)
    return client_row


def make_policy(db_session, client_row: Client, **overrides) -> Policy:
    today = date.today()
    defaults = dict(
        type="car",
        name="Test Policy",
        status="in_force",
        effective_date=today - timedelta(days=30),
        expiration_date=today + timedelta(days=335),
        sum_insured=Decimal("18000.00"),
        deductible=Decimal("500.00"),
        base_rate=Decimal("0.0300"),
        risk_factor=Decimal("1.000"),
        net_premium=Decimal("540.00"),
        taxes_fees=Decimal("111.40"),
        price=Decimal("651.40"),
        client_id=client_row.id,
    )
    defaults.update(overrides)
    policy = Policy(**defaults)
    db_session.add(policy)
    db_session.commit()
    db_session.refresh(policy)
    return policy


def make_claim(db_session, client_row: Client, **overrides) -> ClaimCase:
    defaults = dict(
        user_id=client_row.user_id,
        object="car",
        conversation="Test conversation",
    )
    defaults.update(overrides)
    claim = ClaimCase(**defaults)
    db_session.add(claim)
    db_session.commit()
    db_session.refresh(claim)
    return claim


def make_user(db_session, *, role: str, ref_id: int | None = None,
              password: str = "Secret123!", **overrides) -> User:
    defaults = dict(
        email=f"{_unique(role)}@example.com",
        password_hash=hash_password(password),
        role=role,
        ref_id=ref_id,
        first_name="Test",
        last_name=role.capitalize(),
    )
    defaults.update(overrides)
    user = User(**defaults)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_headers(user: User) -> dict:
    token, _ = create_access_token(subject=user.id, role=user.role, ref_id=user.ref_id)
    return {"Authorization": f"Bearer {token}"}
