from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.models import Client
from app.core.exceptions import NotFoundError
from app.policies.models import Policy
from app.policies.schemas import PolicyCreate, PolicyUpdate


def create_policy(db: Session, data: PolicyCreate) -> Policy:
    client = db.get(Client, data.client_id)
    if client is None:
        raise NotFoundError("The referenced client does not exist")

    policy = Policy(**data.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def list_policies(db: Session) -> list[Policy]:
    return list(db.scalars(select(Policy)).all())


def active_policies_balance(db: Session) -> dict:
    policies = db.scalars(select(Policy).where(Policy.status == "active")).all()
    total = sum(float(p.price) for p in policies)
    return {
        "active_policies": len(policies),
        "total_value": round(total, 2),
    }


def update_policy(db: Session, policy_id: int, changes: PolicyUpdate) -> Policy:
    policy = db.get(Policy, policy_id)
    if policy is None:
        raise NotFoundError("Policy not found")
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)
    db.commit()
    db.refresh(policy)
    return policy


def delete_policy(db: Session, policy_id: int) -> None:
    # Soft delete: mark the policy as cancelled ("de baja") instead of removing it.
    policy = db.get(Policy, policy_id)
    if policy is None:
        raise NotFoundError("Policy not found")
    policy.status = "inactive"
    db.commit()
