from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.models import Agent
from app.agents.schemas import AgentClaims, AgentCreate, AgentRead, AgentUpdate
from app.auth.models import User
from app.claims.models import ClaimCase
from app.clients.models import Client
from app.core.exceptions import ConflictError, NotFoundError
from app.supervisors.models import Supervisor


def _client_count(db: Session, agent_id: int) -> int:
    return db.scalar(
        select(func.count(Client.id)).where(Client.agent_id == agent_id)
    ) or 0


def _claims_for_agent(db: Session, agent_id: int) -> AgentClaims:
    """Aggregate the claims of an agent's clients into the card breakdown.

    Claims reference clients by ``user_id``. We bucket each claim_status into
    the shape the frontend expects:
      supported               -> granted
      contradicted            -> rejected
      not_enough_information   -> in_progress
    A claim is "resolved" once it reached a verdict (granted + rejected), so
    resolved + in_progress equals the agent's total claim count.
    """
    user_ids = select(Client.user_id).where(Client.agent_id == agent_id)
    rows = db.execute(
        select(ClaimCase.claim_status, func.count())
        .where(ClaimCase.user_id.in_(user_ids))
        .group_by(ClaimCase.claim_status)
    ).all()
    counts = {status: n for status, n in rows}
    granted = counts.get("supported", 0)
    rejected = counts.get("contradicted", 0)
    in_progress = counts.get("not_enough_information", 0)
    return AgentClaims(
        resolved=granted + rejected,
        in_progress=in_progress,
        granted=granted,
        rejected=rejected,
    )


def _to_read(db: Session, agent: Agent) -> AgentRead:
    data = AgentRead.model_validate(agent)
    data.client_count = _client_count(db, agent.id)
    data.claims = _claims_for_agent(db, agent.id)
    return data


def _filter_by_role(stmt, current_user: User):
    if current_user.role == "supervisor" and current_user.ref_id is not None:
        return stmt.where(Agent.supervisor_id == current_user.ref_id)
    if current_user.role == "agent":
        return stmt.where(Agent.id == (current_user.ref_id or -1))
    return stmt


def list_agents(db: Session, current_user: User) -> list[AgentRead]:
    stmt = _filter_by_role(select(Agent), current_user).order_by(Agent.id.asc())
    return [_to_read(db, agent) for agent in db.scalars(stmt).all()]


def _get_agent_orm(db: Session, agent_id: int) -> Agent:
    agent = db.get(Agent, agent_id)
    if agent is None:
        raise NotFoundError("Agent not found")
    return agent


def get_agent(db: Session, agent_id: int) -> AgentRead:
    return _to_read(db, _get_agent_orm(db, agent_id))


def create_agent(db: Session, data: AgentCreate) -> AgentRead:
    # The referenced supervisor must exist.
    supervisor = db.get(Supervisor, data.supervisor_id)
    if supervisor is None:
        raise NotFoundError("The referenced supervisor does not exist")

    # The agent number must be unique.
    existing = db.scalar(
        select(Agent).where(Agent.agent_number == data.agent_number)
    )
    if existing is not None:
        raise ConflictError("An agent with this agent_number already exists")

    agent = Agent(**data.model_dump())
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return _to_read(db, agent)


def update_agent(db: Session, agent_id: int, changes: AgentUpdate) -> AgentRead:
    agent = _get_agent_orm(db, agent_id)
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)
    db.commit()
    db.refresh(agent)
    return _to_read(db, agent)


def delete_agent(db: Session, agent_id: int) -> None:
    # Soft delete: mark the agent as deregistered instead of removing the row.
    agent = _get_agent_orm(db, agent_id)
    agent.status = "inactive"
    db.commit()
