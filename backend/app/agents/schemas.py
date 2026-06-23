from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr


class AgentBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    city: str | None = None
    agent_number: str
    status: str = "active"
    contribution: Decimal = Decimal(0)
    losses: Decimal = Decimal(0)
    photo_url: str | None = None


class AgentCreate(AgentBase):
    supervisor_id: int


class AgentUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    city: str | None = None
    status: str | None = None
    contribution: Decimal | None = None
    losses: Decimal | None = None
    photo_url: str | None = None
    supervisor_id: int | None = None


class AgentClaims(BaseModel):
    resolved: int = 0
    in_progress: int = 0
    granted: int = 0
    rejected: int = 0


class AgentRead(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supervisor_id: int
    created_at: datetime
    client_count: int = 0
    claims: AgentClaims = AgentClaims()
