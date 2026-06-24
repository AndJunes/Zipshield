from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.claims import service
from app.claims.schemas import ClaimCreate, ClaimRead, ClaimUpdate
from app.core.database import get_db
from app.core.deps import get_current_user
from app.llm import service as llm_service

router = APIRouter(prefix="/claims", tags=["Claims"])


@router.get("", response_model=list[ClaimRead])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_claims(db, current_user)


@router.get("/{claim_id}", response_model=ClaimRead)
def get_one(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_claim(db, claim_id)


@router.post("", response_model=ClaimRead, status_code=status.HTTP_201_CREATED)
def create(
    data: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_claim(db, data)


@router.patch("/{claim_id}", response_model=ClaimRead)
def update(
    claim_id: int,
    changes: ClaimUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_claim(db, claim_id, changes)


@router.post("/{claim_id}/analyze", response_model=ClaimRead)
def analyze(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analiza el reclamo con el LLM y persiste los 10 campos del resultado.

    Si el LLM no está disponible (falta la API key o falla la red), responde 502 y el
    reclamo queda intacto.
    """
    claim = service.get_claim(db, claim_id)
    try:
        fields = llm_service.analyze_claim(db, claim)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo completar el análisis: {exc}",
        )
    return service.apply_analysis(db, claim, fields)
