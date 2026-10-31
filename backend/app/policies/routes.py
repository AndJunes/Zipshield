from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.policies import service
from app.policies.schemas import (
    PolicyCreate,
    PolicyEventRead,
    PolicyRead,
    PolicyUpdate,
    QuoteRequest,
    QuoteResponse,
)

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
def create(data: PolicyCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return service.create_policy(db, data, actor_id=current_user.id)


@router.post("/quote", response_model=QuoteResponse)
def quote(data: QuoteRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Quote a policy without saving it (returns the premium breakdown)."""
    return service.quote_policy(db, data.type.value, data.sum_insured, client_id=data.client_id)


@router.get("", response_model=list[PolicyRead])
def list_all(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return service.list_policies(db, current_user)


@router.get("/balance")
def balance(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return service.active_policies_balance(db)


@router.get("/{policy_id}", response_model=PolicyRead)
def get_one(policy_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return service.get_policy(db, policy_id, current_user)


@router.get("/{policy_id}/events", response_model=list[PolicyEventRead])
def events(policy_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return service.list_policy_events(db, policy_id, current_user)


@router.patch("/{policy_id}", response_model=PolicyRead)
def update(
    policy_id: int,
    changes: PolicyUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.update_policy(db, policy_id, changes, current_user)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(policy_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service.cancel_policy(db, policy_id, current_user, actor_id=current_user.id)
