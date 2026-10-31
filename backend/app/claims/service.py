import logging

from sqlalchemy.orm import Session

from app.auth.models import User
from app.agents.models import Agent
from app.claims.models import ClaimCase
from app.claims.schemas import ClaimCreate, ClaimUpdate
from app.clients.models import Client
from app.core.database import SessionLocal
from app.core.exceptions import ConflictError, NotFoundError
from app.llm import service as llm_service
from app.policies.service import can_file_claim, get_policy

log = logging.getLogger(__name__)


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


def create_claim(db: Session, data: ClaimCreate, current_user: User) -> ClaimCase:
    # get_policy is role-scoped: a policy outside the actor's book is a 404, so
    # existence doesn't leak. The claimant comes from the policy, never the body.
    policy = get_policy(db, data.policy_id, current_user)
    if not can_file_claim(policy, data.date_of_loss):
        raise ConflictError(
            "The policy is not in force on the date of loss; the claim cannot be filed."
        )
    claim = ClaimCase(**data.model_dump(), user_id=policy.client.user_id)
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


def update_claim(db: Session, claim_id: int, changes: ClaimUpdate, current_user: User) -> ClaimCase:
    claim = get_claim(db, claim_id, current_user)
    data = changes.model_dump(exclude_unset=True)
    if data.get("policy_id") is not None and data["policy_id"] != claim.policy_id:
        # Repointing a claim follows the same rules as filing it.
        policy = get_policy(db, data["policy_id"], current_user)
        if policy.client.user_id != claim.user_id:
            raise ConflictError("The policy does not belong to the claimant")
        if not can_file_claim(policy, data.get("date_of_loss", claim.date_of_loss)):
            raise ConflictError(
                "The policy is not in force on the date of loss; the claim cannot be filed."
            )
    for field, value in data.items():
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


def start_analysis(db: Session, claim: ClaimCase) -> ClaimCase:
    claim.analysis_status = "pending"
    db.commit()
    db.refresh(claim)
    return claim


def run_analysis(claim_id: int) -> None:
    """Background entry point: owns its session and never raises — the outcome
    lands in analysis_status, which the frontend polls."""
    db = SessionLocal()
    try:
        claim = db.get(ClaimCase, claim_id)
        if claim is None:
            return
        try:
            fields = llm_service.analyze_claim(db, claim)
        except Exception as exc:
            log.warning("Analysis of claim %d failed: %s", claim_id, exc)
            claim.analysis_status = "failed"
            db.commit()
            return
        claim.analysis_status = "done"
        apply_analysis(db, claim, fields)
    finally:
        db.close()


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
