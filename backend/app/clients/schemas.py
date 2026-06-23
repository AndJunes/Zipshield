from pydantic import BaseModel, ConfigDict, EmailStr


class ClientBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    city: str | None = None
    client_number: str
    status: str = "active"
    photo_url: str | None = None


class ClientCreate(ClientBase):
    agent_id: int


class ClientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    city: str | None = None
    status: str | None = None
    photo_url: str | None = None
    agent_id: int | None = None


class ClientHistory(BaseModel):
    past_claim_count: int = 0
    accept_claim: int = 0
    manual_review_claim: int = 0
    rejected_claim: int = 0
    last_90_days_claim_count: int = 0
    history_flags: list[str] = []
    history_summary: str | None = None


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    agent_id: int
    history: ClientHistory = ClientHistory()
