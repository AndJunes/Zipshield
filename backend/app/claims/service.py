from sqlalchemy.orm import Session

from app.auth.models import User
from app.agents.models import Agent
from app.claims.models import ClaimCase
from app.claims.schemas import ClaimCreate, ClaimUpdate
from app.clients.models import Client
from app.core.exceptions import ConflictError, NotFoundError
from app.policies.models import Policy
from app.policies.service import can_file_claim


def _scope_by_role(query, db: Session, current_user: User):
    if current_user.role == "supervisor" and current_user.ref_id is not None:
        agent_ids_subquery = db.query(Agent.id).filter(Agent.supervisor_id == current_user.ref_id).subquery()
        user_ids_subquery = (
            db.query(Client.user_id).filter(Client.agent_id.in_(agent_ids_subquery)).subquery()
        )
        return query.filter(ClaimCase.user_id.in_(user_ids_subquery))
    if current_user.role == "agent" and current_user.ref_id is not None:
        user_ids_subquery = (
            db.query(Client.user_id).filter(Client.agent_id == current_user.ref_id).subquery()
        )
        return query.filter(ClaimCase.user_id.in_(user_ids_subquery))
    return query


def list_claims(db: Session, current_user: User) -> list[ClaimCase]:
    query = _scope_by_role(db.query(ClaimCase), db, current_user)
    return query.order_by(ClaimCase.id.asc()).all()


def get_claim(db: Session, claim_id: int, current_user: User) -> ClaimCase:
    query = _scope_by_role(db.query(ClaimCase).filter(ClaimCase.id == claim_id), db, current_user)
    claim = query.first()
    if not claim:
        raise NotFoundError(f"Claim {claim_id} not found")
    return claim


def create_claim(db: Session, data: ClaimCreate) -> ClaimCase:
    if data.policy_id is not None:
        policy = db.get(Policy, data.policy_id)
        if policy is None:
            raise NotFoundError(f"Policy {data.policy_id} not found")
        if policy.client.user_id != data.user_id:
            raise ConflictError("The policy does not belong to the user filing the claim")
        if not can_file_claim(policy, data.date_of_loss):
            raise ConflictError(
                "The policy is not in force on the date of loss; the claim cannot be filed."
            )
    claim = ClaimCase(**data.model_dump())
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


def update_claim(db: Session, claim_id: int, changes: ClaimUpdate, current_user: User) -> ClaimCase:
    claim = get_claim(db, claim_id, current_user)
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(claim, field, value)
    db.commit()
    db.refresh(claim)
    return claim


# Fields the LLM analysis may overwrite (the 10 the model produces).
ANALYSIS_FIELDS = frozenset(
    {
        "evidence_standard_met",
        "evidence_standard_met_reason",
        "risk_flags",
        "issue_type",
        "object_part",
        "claim_status",
        "claim_status_justification",
        "supporting_image_ids",
        "valid_image",
        "severity",
    }
)


def apply_analysis(db: Session, claim: ClaimCase, fields: dict) -> ClaimCase:
    """Persist the fields returned by the LLM analysis on the claim.

    Writes only the analysis columns (allowlist), never the input data
    (user_id, object, conversation, image_urls).
    """
    for field, value in fields.items():
        if field in ANALYSIS_FIELDS:
            setattr(claim, field, value)
    db.commit()
    db.refresh(claim)
    return claim
