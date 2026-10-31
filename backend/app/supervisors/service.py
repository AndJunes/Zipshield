from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.models import Agent
from app.auth.models import User
from app.core.exceptions import ConflictError, NotFoundError
from app.supervisors.models import Supervisor
from app.supervisors.schemas import SupervisorCreate, SupervisorRead, SupervisorUpdate


def _agent_counts_by_supervisor(db: Session, supervisor_ids: list[int]) -> dict[int, int]:
    if not supervisor_ids:
        return {}
    rows = db.execute(
        select(Agent.supervisor_id, func.count(Agent.id))
        .where(Agent.supervisor_id.in_(supervisor_ids))
        .group_by(Agent.supervisor_id)
    ).all()
    return {supervisor_id: n for supervisor_id, n in rows}


def _attach_agent_count(
    db: Session, supervisor: Supervisor, agent_count: int | None = None
) -> SupervisorRead:
    count = (
        agent_count
        if agent_count is not None
        else (
            db.scalar(select(func.count(Agent.id)).where(Agent.supervisor_id == supervisor.id)) or 0
        )
    )
    data = SupervisorRead.model_validate(supervisor)
    data.agent_count = count
    return data


def _filter_by_role(query, current_user: User):
    if current_user.role == "supervisor" and current_user.ref_id is not None:
        return query.where(Supervisor.id == current_user.ref_id)
    if current_user.role == "agent":
        return query.where(Supervisor.id == -1)  # empty
    return query


def list_supervisors(db: Session, current_user: User) -> list[SupervisorRead]:
    stmt = _filter_by_role(select(Supervisor), current_user)
    supervisors = list(db.scalars(stmt).all())
    agent_counts = _agent_counts_by_supervisor(db, [s.id for s in supervisors])
    return [_attach_agent_count(db, s, agent_counts.get(s.id, 0)) for s in supervisors]


def get_supervisor(db: Session, supervisor_id: int, current_user: User) -> SupervisorRead:
    stmt = _filter_by_role(select(Supervisor).where(Supervisor.id == supervisor_id), current_user)
    supervisor = db.scalars(stmt).first()
    if supervisor is None:
        raise NotFoundError("Supervisor no encontrado")
    return _attach_agent_count(db, supervisor)


def create_supervisor(db: Session, data: SupervisorCreate) -> SupervisorRead:
    existing = db.scalar(select(Supervisor).where(Supervisor.email == data.email))
    if existing is not None:
        raise ConflictError("Ya existe un supervisor con ese email")
    supervisor = Supervisor(**data.model_dump())
    db.add(supervisor)
    db.commit()
    db.refresh(supervisor)
    return _attach_agent_count(db, supervisor)


def update_supervisor(
    db: Session, supervisor_id: int, changes: SupervisorUpdate, current_user: User
) -> SupervisorRead:
    stmt = _filter_by_role(select(Supervisor).where(Supervisor.id == supervisor_id), current_user)
    supervisor = db.scalars(stmt).first()
    if supervisor is None:
        raise NotFoundError("Supervisor no encontrado")
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(supervisor, field, value)
    db.commit()
    db.refresh(supervisor)
    return _attach_agent_count(db, supervisor)


def delete_supervisor(db: Session, supervisor_id: int) -> None:
    supervisor = db.get(Supervisor, supervisor_id)
    if supervisor is None:
        raise NotFoundError("Supervisor no encontrado")
    supervisor.status = "inactive"
    db.commit()
