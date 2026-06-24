from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.models import Agent
from app.auth.models import User
from app.clients.history import compute_client_history
from app.clients.models import Client
from app.clients.schemas import ClientCreate, ClientRead, ClientUpdate
from app.core.exceptions import ConflictError, NotFoundError


def _to_read(db: Session, client: Client) -> ClientRead:
    data = ClientRead.model_validate(client)
    data.history = compute_client_history(db, client)
    return data


def _filter_by_role(stmt, current_user: User):
    if current_user.role == "agent" and current_user.ref_id is not None:
        return stmt.where(Client.agent_id == current_user.ref_id)
    if current_user.role == "supervisor" and current_user.ref_id is not None:
        agent_ids = select(Agent.id).where(
            Agent.supervisor_id == current_user.ref_id
        )
        return stmt.where(Client.agent_id.in_(agent_ids))
    return stmt


def list_clients(db: Session, current_user: User) -> list[ClientRead]:
    stmt = _filter_by_role(select(Client), current_user).order_by(Client.id.asc())
    return [_to_read(db, c) for c in db.scalars(stmt).all()]


def _get_client_orm(db: Session, client_id: int) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise NotFoundError("Client not found")
    return client


def get_client(db: Session, client_id: int) -> ClientRead:
    return _to_read(db, _get_client_orm(db, client_id))


def create_client(db: Session, data: ClientCreate) -> ClientRead:
    agent = db.get(Agent, data.agent_id)
    if agent is None:
        raise NotFoundError("The referenced agent does not exist")

    existing = db.scalar(
        select(Client).where(Client.client_number == data.client_number)
    )
    if existing is not None:
        raise ConflictError("A client with this client_number already exists")

    client = Client(**data.model_dump(), user_id="")
    db.add(client)
    db.flush()  # assigns the autoincrement id without committing
    client.user_id = f"user_{client.id:03d}"
    db.commit()
    db.refresh(client)
    return _to_read(db, client)


def update_client(db: Session, client_id: int, changes: ClientUpdate) -> ClientRead:
    client = _get_client_orm(db, client_id)
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return _to_read(db, client)


def delete_client(db: Session, client_id: int) -> None:
    # Soft delete: mark the client as deregistered instead of removing the row.
    client = _get_client_orm(db, client_id)
    client.status = "inactive"
    db.commit()
