from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.supervisors import service
from app.supervisors.schemas import SupervisorCreate, SupervisorRead, SupervisorUpdate

router = APIRouter(prefix="/supervisors", tags=["Supervisors"])


@router.get("", response_model=list[SupervisorRead])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_supervisors(db, current_user)


@router.get("/{supervisor_id}", response_model=SupervisorRead)
def get_one(
    supervisor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_supervisor(db, supervisor_id)


@router.post(
    "",
    response_model=SupervisorRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def create(data: SupervisorCreate, db: Session = Depends(get_db)):
    return service.create_supervisor(db, data)


@router.patch(
    "/{supervisor_id}",
    response_model=SupervisorRead,
    dependencies=[Depends(require_role("admin", "supervisor"))],
)
def update(
    supervisor_id: int,
    changes: SupervisorUpdate,
    db: Session = Depends(get_db),
):
    return service.update_supervisor(db, supervisor_id, changes)


@router.delete(
    "/{supervisor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin"))],
)
def delete(supervisor_id: int, db: Session = Depends(get_db)):
    service.delete_supervisor(db, supervisor_id)
