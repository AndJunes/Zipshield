from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.agents import service
from app.agents.schemas import AgentCreate, AgentRead, AgentUpdate
from app.auth.models import User
from app.core.database import get_db
from app.core.deps import get_current_user, require_role

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", response_model=list[AgentRead])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_agents(db, current_user)


@router.get("/{agent_id}", response_model=AgentRead)
def get_one(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_agent(db, agent_id)


@router.post(
    "",
    response_model=AgentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "supervisor"))],
)
def create(data: AgentCreate, db: Session = Depends(get_db)):
    return service.create_agent(db, data)


@router.patch("/{agent_id}", response_model=AgentRead)
def update(
    agent_id: int,
    changes: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_agent(db, agent_id, changes)


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "supervisor"))],
)
def delete(agent_id: int, db: Session = Depends(get_db)):
    service.delete_agent(db, agent_id)
