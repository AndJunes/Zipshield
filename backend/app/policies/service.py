from calendar import monthrange
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.history import compute_client_history
from app.clients.models import Client
from app.core.exceptions import ConflictError, NotFoundError
from app.policies import pricing
from app.policies.models import Coverage, Policy, PolicyEvent
from app.policies.schemas import PolicyCreate, PolicyUpdate


# Máquina de estados de la póliza: qué transiciones son válidas desde cada estado.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "quote": {"underwriting", "declined"},
    "underwriting": {"pending_info", "in_force", "declined"},
    "pending_info": {"underwriting", "in_force", "declined"},
    "in_force": {"pending_cancel", "cancelled", "expired"},
    "pending_cancel": {"in_force", "cancelled"},
    "cancelled": {"in_force"},   # reinstatement
    "expired": {"in_force"},     # renovación tardía
    "declined": set(),           # terminal
}


def _add_months(start: date, months: int) -> date:
    total = start.month - 1 + months
    year = start.year + total // 12
    month = total % 12 + 1
    day = min(start.day, monthrange(year, month)[1])
    return date(year, month, day)


def risk_factor_for_client(db: Session, client: Client) -> float:
    """Recargo por siniestralidad: el historial del cliente alimenta la prima (como en la realidad)."""
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
    """Cotiza una póliza SIN guardarla (preview del rating)."""
    risk_factor = 1.0
    if client_id is not None:
        client = db.get(Client, client_id)
        if client is not None:
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
        rating_factors={"base_rate": q["base_rate"], "risk_factor": q["risk_factor"],
                        "tax_rate": q["tax_rate"], "policy_fee": q["policy_fee"]},
        coverage=data.coverage,
        client_id=data.client_id,
    )
    for c in q["coverages"]:
        policy.coverages.append(Coverage(**c))
    db.add(policy)
    db.flush()
    policy.events.append(PolicyEvent(
        policy_id=policy.id, event_type="issued", to_status="in_force",
        actor_id=actor_id, payload={"total_premium": float(q["total_premium"])},
    ))
    db.commit()
    db.refresh(policy)
    return policy


def list_policies(db: Session) -> list[Policy]:
    return list(db.scalars(select(Policy).order_by(Policy.id.asc())).all())


def get_policy(db: Session, policy_id: int) -> Policy:
    policy = db.get(Policy, policy_id)
    if policy is None:
        raise NotFoundError("Policy not found")
    return policy


def list_policy_events(db: Session, policy_id: int) -> list[PolicyEvent]:
    policy = get_policy(db, policy_id)
    return sorted(policy.events, key=lambda e: e.created_at)


def active_policies_balance(db: Session) -> dict:
    """Prima escrita de las pólizas vigentes (in_force)."""
    policies = db.scalars(select(Policy).where(Policy.status == "in_force")).all()
    total = sum(float(p.price) for p in policies)
    return {
        "active_policies": len(policies),
        "total_value": round(total, 2),
    }


def update_policy(db: Session, policy_id: int, changes: PolicyUpdate) -> Policy:
    policy = get_policy(db, policy_id)
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)
    db.commit()
    db.refresh(policy)
    return policy


def transition_status(db: Session, policy_id: int, to_status: str, actor_id: int | None = None,
                      reason: str | None = None, event_type: str | None = None) -> Policy:
    """Cambia el estado validando la máquina de estados y registra el evento en el historial."""
    policy = get_policy(db, policy_id)
    if to_status not in ALLOWED_TRANSITIONS.get(policy.status, set()):
        raise ConflictError(f"Transición inválida: '{policy.status}' → '{to_status}'")
    previous = policy.status
    policy.status = to_status
    if to_status == "cancelled":
        policy.cancel_date = date.today()
        policy.cancel_reason = reason or "insured_request"
    policy.events.append(PolicyEvent(
        policy_id=policy.id, event_type=event_type or to_status,
        from_status=previous, to_status=to_status, actor_id=actor_id,
        payload={"reason": reason} if reason else {},
    ))
    db.commit()
    db.refresh(policy)
    return policy


def cancel_policy(db: Session, policy_id: int, reason: str = "insured_request",
                  actor_id: int | None = None) -> Policy:
    return transition_status(db, policy_id, "cancelled", actor_id=actor_id,
                             reason=reason, event_type="cancelled")


def can_file_claim(policy: Policy | None, date_of_loss: date | None) -> bool:
    """Regla de oro: un reclamo es válido solo si el siniestro ocurrió mientras la cobertura
    estaba en vigor (no basta con que la póliza esté 'activa hoy')."""
    if policy is None:
        return False
    dol = date_of_loss or date.today()
    if policy.status in ("in_force", "pending_cancel"):
        return policy.effective_date <= dol <= policy.expiration_date
    if policy.status in ("cancelled", "expired"):
        end = policy.cancel_date or policy.expiration_date
        return policy.effective_date <= dol <= end
    return False
