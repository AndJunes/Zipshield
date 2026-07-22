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
        raise NotFoundError(f"Reclamo {claim_id} no encontrado")
    return claim


def create_claim(db: Session, data: ClaimCreate) -> ClaimCase:
    if data.policy_id is not None:
        policy = db.get(Policy, data.policy_id)
        if policy is None:
            raise NotFoundError(f"Póliza {data.policy_id} no encontrada")
        if policy.client.user_id != data.user_id:
            raise ConflictError("La póliza no pertenece al usuario que reporta el reclamo")
        if not can_file_claim(policy, data.date_of_loss):
            raise ConflictError(
                "La póliza no está vigente en la fecha de pérdida; no se puede registrar el reclamo."
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


# Campos que el análisis del LLM puede sobrescribir (los 10 que produce el modelo).
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
    """Persiste en el claim los campos devueltos por el análisis del LLM.

    Solo escribe las columnas de análisis (lista blanca), nunca los datos de entrada
    (user_id, object, conversation, image_urls).
    """
    for field, value in fields.items():
        if field in ANALYSIS_FIELDS:
            setattr(claim, field, value)
    db.commit()
    db.refresh(claim)
    return claim
