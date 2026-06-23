from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.models import Agent
from app.clients.models import Client
from app.policies.models import Policy
from app.supervisors.models import Supervisor


def _count(db: Session, model, condition=None) -> int:
    """Count rows of a table, optionally filtered by a condition.

    Avoids repeating the same select(func.count()) boilerplate for every metric.
    """
    stmt = select(func.count()).select_from(model)
    if condition is not None:
        stmt = stmt.where(condition)
    return db.scalar(stmt) or 0


def dashboard_summary(db: Session) -> dict:
    today = date.today()

    # People counts
    total_supervisors = _count(db, Supervisor)
    total_agents = _count(db, Agent)
    total_clients = _count(db, Client)
    active_clients = _count(db, Client, Client.status == "active")
    inactive_clients = _count(db, Client, Client.status == "inactive")

    # Policy counts
    total_policies = _count(db, Policy)
    active_policies = _count(db, Policy, Policy.status == "active")
    expired_policies = _count(db, Policy, Policy.expiration_date < today)

    # Debtor clients: clients that have at least one expired policy.
    # The subquery gets the distinct client ids with an expired policy,
    # then we count how many there are.
    debtor_subquery = (
        select(Policy.client_id)
        .where(Policy.expiration_date < today)
        .distinct()
        .subquery()
    )
    debtor_clients = db.scalar(select(func.count()).select_from(debtor_subquery)) or 0

    # Total value of active policies. coalesce turns a NULL sum (no rows) into 0.
    active_value = db.scalar(
        select(func.coalesce(func.sum(Policy.price), 0)).where(
            Policy.status == "active"
        )
    )

    return {
        "total_supervisors": total_supervisors,
        "total_agents": total_agents,
        "total_clients": total_clients,
        "active_clients": active_clients,
        "inactive_clients": inactive_clients,
        "total_policies": total_policies,
        "active_policies": active_policies,
        "expired_policies": expired_policies,
        "debtor_clients": debtor_clients,
        "active_policies_value": float(active_value),
    }