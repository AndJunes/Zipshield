from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: str
    ref_id: int | None
    first_name: str
    last_name: str
    photo_url: str | None


class TokenInfo(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class SessionResponse(BaseModel):
    token: str
    user: UserRead
    expires_at: datetime
