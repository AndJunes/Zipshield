from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.clients import service
from app.clients.schemas import ClientCreate, ClientRead, ClientUpdate
from app.core.database import get_db
from app.core.deps import get_current_user

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("", response_model=list[ClientRead])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_clients(db, current_user)


@router.get("/{client_id}", response_model=ClientRead)
def get_one(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_client(db, client_id)


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create(
    data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_client(db, data)


@router.patch("/{client_id}", response_model=ClientRead)
def update(
    client_id: int,
    changes: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_client(db, client_id, changes)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_client(db, client_id)
