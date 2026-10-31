from calendar import monthrange
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.agents.models import Agent
from app.auth.models import User
from app.clients.history import compute_client_history
from app.clients.models import Client
from app.core.exceptions import ConflictError, NotFoundError
from app.policies import pricing
from app.policies.models import Coverage, Policy, PolicyEvent
from app.policies.schemas import PolicyCreate, PolicyUpdate


def _filter_by_role(stmt, current_user: User):
    """Same pattern as `clients/service.py::_filter_by_role`: an agent only sees the
    policies of their own clients; a supervisor, those of the agents on their team."""
    if current_user.role == "agent" and current_user.ref_id is not None:
        return stmt.join(Client, Policy.client_id == Client.id).where(
            Client.agent_id == current_user.ref_id
        )
    if current_user.role == "supervisor" and current_user.ref_id is not None:
        agent_ids = select(Agent.id).where(Agent.supervisor_id == current_user.ref_id)
        return stmt.join(Client, Policy.client_id == Client.id).where(
            Client.agent_id.in_(agent_ids)
        )
    return stmt


# Policy state machine: which transitions are valid from each status.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "quote": {"underwriting", "declined"},
    "underwriting": {"pending_info", "in_force", "declined"},
    "pending_info": {"underwriting", "in_force", "declined"},
    "in_force": {"pending_cancel", "cancelled", "expired"},
    "pending_cancel": {"in_force", "cancelled"},
    "cancelled": {"in_force"},  # reinstatement
    "expired": {"in_force"},  # late renewal
    "declined": set(),  # terminal
}


def _add_months(start: date, months: int) -> date:
    total = start.month - 1 + months
    year = start.year + total // 12
    month = total % 12 + 1
    day = min(start.day, monthrange(year, month)[1])
    return date(year, month, day)


def risk_factor_for_client(db: Session, client: Client) -> float:
    """Loss-history surcharge: the client's history feeds the premium (as in real life)."""
    h = compute_client_history(db, client)
    factor = 1.0
    if h.rejected_claim >= 2:
        factor += 0.15
    if "user_history_risk" in h.history_flags:
        factor += 0.10
    if "manual_review_required" in h.history_flags:
        factor += 0.05
    return round(min(factor, 1.5), 3)


def quote_policy(db: Session, policy_type: str, sum_insured, client_id: int | None = None) -> dict:
    """Quote a policy WITHOUT saving it (rating preview)."""
    risk_factor = 1.0
    if client_id is not None:
        client = db.get(Client, client_id)
        if client is None:
            raise NotFoundError(f"Client {client_id} not found")
        risk_factor = risk_factor_for_client(db, client)
    return pricing.quote(policy_type, sum_insured, risk_factor=risk_factor)


def create_policy(db: Session, data: PolicyCreate, actor_id: int | None = None) -> Policy:
    client = db.get(Client, data.client_id)
    if client is None:
        raise NotFoundError("The referenced client does not exist")

    risk_factor = risk_factor_for_client(db, client)
    q = pricing.quote(data.type.value, data.sum_insured, risk_factor=risk_factor)
    policy = Policy(
        type=data.type.value,
        name=data.name,
        status="in_force",
        effective_date=data.effective_date,
        expiration_date=_add_months(data.effective_date, data.term_months),
        sum_insured=data.sum_insured,
        deductible=data.deductible,
        base_rate=q["base_rate"],
        risk_factor=q["risk_factor"],
        net_premium=q["net_premium"],
        taxes_fees=q["taxes_fees"],
        price=q["total_premium"],
        # `rating_factors` is JSON: Decimal is not serializable there, unlike the
        # Numeric columns above (which accept it directly).
        rating_factors={
            "base_rate": float(q["base_rate"]),
            "risk_factor": float(q["risk_factor"]),
            "tax_rate": q["tax_rate"],
            "policy_fee": q["policy_fee"],
        },
        coverage=data.coverage,
        client_id=data.client_id,
    )
    for c in q["coverages"]:
        policy.coverages.append(Coverage(**c))
    db.add(policy)
    db.flush()
    policy.events.append(
        PolicyEvent(
            policy_id=policy.id,
            event_type="issued",
            to_status="in_force",
            actor_id=actor_id,
            payload={"total_premium": float(q["total_premium"])},
        )
    )
    db.commit()
    db.refresh(policy)
    return policy


def sync_expired_policies(db: Session) -> int:
    """`ALLOWED_TRANSITIONS` declares `in_force -> expired`, but nothing used to trigger
    it automatically as time passed: the `status` stayed `in_force` forever even after
    `expiration_date`, so the active-policy balance and the dashboard ended up counting
    different things. Synced lazily, without going through `transition_status` (which
    requires a `current_user` for role scoping — this is a system transition, not a
    user's)."""
    today = date.today()
    stale = list(
        db.scalars(
            select(Policy).where(
                Policy.status.in_(("in_force", "pending_cancel")),
                Policy.expiration_date < today,
            )
        ).all()
    )
    for policy in stale:
        previous = policy.status
        policy.status = "expired"
        policy.events.append(
            PolicyEvent(
                policy_id=policy.id,
                event_type="expired",
                from_status=previous,
                to_status="expired",
            )
        )
    if stale:
        db.commit()
    return len(stale)


def list_policies(db: Session, current_user: User) -> list[Policy]:
    sync_expired_policies(db)
    # selectinload avoids one extra query per policy when serializing
    # PolicyRead.coverages: without it, Policy.coverages (lazy="select" by default)
    # fires an additional query for every row in the listing (N+1).
    stmt = (
        _filter_by_role(select(Policy), current_user)
        .options(selectinload(Policy.coverages))
        .order_by(Policy.id.asc())
    )
    return list(db.scalars(stmt).all())


def get_policy(db: Session, policy_id: int, current_user: User) -> Policy:
    sync_expired_policies(db)
    stmt = _filter_by_role(select(Policy).where(Policy.id == policy_id), current_user)
    policy = db.scalars(stmt).first()
    if policy is None:
        raise NotFoundError("Policy not found")
    return policy


def list_policy_events(db: Session, policy_id: int, current_user: User) -> list[PolicyEvent]:
    policy = get_policy(db, policy_id, current_user)
    return sorted(policy.events, key=lambda e: e.created_at)


def active_policies_balance(db: Session) -> dict:
    """Written premium of the active (in_force) policies."""
    sync_expired_policies(db)
    policies = db.scalars(select(Policy).where(Policy.status == "in_force")).all()
    total = sum(float(p.price) for p in policies)
    return {
        "active_policies": len(policies),
        "total_value": round(total, 2),
    }


# Terminal states of the `ALLOWED_TRANSITIONS` machine: once there, the policy must
# not be edited again through the generic PATCH.
_TERMINAL_STATUSES = {"cancelled", "declined", "expired"}


def update_policy(db: Session, policy_id: int, changes: PolicyUpdate, current_user: User) -> Policy:
    policy = get_policy(db, policy_id, current_user)
    if policy.status in _TERMINAL_STATUSES:
        raise ConflictError(f"Policy is in status '{policy.status}' and cannot be edited.")

    updates = changes.model_dump(exclude_unset=True)
    new_expiration = updates.get("expiration_date", policy.expiration_date)
    if new_expiration < policy.effective_date:
        raise ConflictError("expiration_date cannot be earlier than effective_date")

    for field, value in updates.items():
        setattr(policy, field, value)
    policy.events.append(
        PolicyEvent(
            policy_id=policy.id,
            event_type="updated",
            payload={k: (v.isoformat() if isinstance(v, date) else v) for k, v in updates.items()},
        )
    )
    db.commit()
    db.refresh(policy)
    return policy


def transition_status(
    db: Session,
    policy_id: int,
    to_status: str,
    current_user: User,
    actor_id: int | None = None,
    reason: str | None = None,
    event_type: str | None = None,
) -> Policy:
    """Change the status validating the state machine, and record the event in the timeline."""
    policy = get_policy(db, policy_id, current_user)
    if to_status not in ALLOWED_TRANSITIONS.get(policy.status, set()):
        raise ConflictError(f"Invalid transition: '{policy.status}' → '{to_status}'")
    previous = policy.status
    policy.status = to_status
    if to_status == "cancelled":
        policy.cancel_date = date.today()
        policy.cancel_reason = reason or "insured_request"
    policy.events.append(
        PolicyEvent(
            policy_id=policy.id,
            event_type=event_type or to_status,
            from_status=previous,
            to_status=to_status,
            actor_id=actor_id,
            payload={"reason": reason} if reason else {},
        )
    )
    db.commit()
    db.refresh(policy)
    return policy


def cancel_policy(
    db: Session,
    policy_id: int,
    current_user: User,
    reason: str = "insured_request",
    actor_id: int | None = None,
) -> Policy:
    return transition_status(
        db,
        policy_id,
        "cancelled",
        current_user,
        actor_id=actor_id,
        reason=reason,
        event_type="cancelled",
    )


def can_file_claim(policy: Policy | None, date_of_loss: date | None) -> bool:
    """Golden rule: a claim is valid only if the loss occurred while coverage was in
    force (the policy being 'active today' is not enough)."""
    if policy is None:
        return False
    dol = date_of_loss or date.today()
    if policy.status in ("in_force", "pending_cancel"):
        return policy.effective_date <= dol <= policy.expiration_date
    if policy.status in ("cancelled", "expired"):
        end = policy.cancel_date or policy.expiration_date
        return policy.effective_date <= dol <= end
    return False
