from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr

class SupervisorBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    city: str | None = None
    status: str = "active"
    contribution: Decimal = Decimal(0)
    losses: Decimal = Decimal(0)
    photo_url: str | None = None

class SupervisorCreate(SupervisorBase):
    pass

class SupervisorUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    city: str | None = None
    status: str | None = None
    contribution: Decimal | None = None
    losses: Decimal | None = None
    photo_url: str | None = None

class SupervisorRead(SupervisorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    agent_count: int = 0
