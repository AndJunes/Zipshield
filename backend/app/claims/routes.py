from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.claims import service
from app.claims.schemas import ClaimCreate, ClaimRead, ClaimUpdate
from app.core.database import get_db
from app.core.deps import get_current_user

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
    return service.get_claim(db, claim_id, current_user)


@router.post("", response_model=ClaimRead, status_code=status.HTTP_201_CREATED)
def create(
    data: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_claim(db, data, current_user)


@router.patch("/{claim_id}", response_model=ClaimRead)
def update(
    claim_id: int,
    changes: ClaimUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_claim(db, claim_id, changes, current_user)


@router.post("/{claim_id}/analyze", response_model=ClaimRead, status_code=status.HTTP_202_ACCEPTED)
def analyze(
    claim_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Queue the AI analysis and answer right away with analysis_status="pending".

    The worst-case LLM call (retries included) takes minutes, so it never runs on
    the request path: the result lands on the claim and the client polls
    analysis_status until it leaves "pending" (done or failed).
    """
    claim = service.get_claim(db, claim_id, current_user)
    if claim.analysis_status == "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An analysis is already running for this claim",
        )
    claim = service.start_analysis(db, claim)
    background_tasks.add_task(service.run_analysis, claim.id)
    return claim
