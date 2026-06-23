from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.policies import service
from app.policies.schemas import PolicyCreate, PolicyRead, PolicyUpdate

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
def create(data: PolicyCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return service.create_policy(db, data)


@router.get("", response_model=list[PolicyRead])
def list_all(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return service.list_policies(db)


@router.get("/balance")
def balance(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return service.active_policies_balance(db)


@router.patch("/{policy_id}", response_model=PolicyRead)
def update(
    policy_id: int,
    changes: PolicyUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.update_policy(db, policy_id, changes)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(policy_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    service.delete_policy(db, policy_id)
