from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


class PolicyType(str, Enum):
    laptop = "laptop"
    automobile = "automobile"
    package = "package"


class PolicyBase(BaseModel):
    type: PolicyType
    name: str
    price: Decimal
    expiration_date: date
    coverage: str | None = None
    status: str = "active"

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("price must be greater than zero")
        return value


class PolicyCreate(PolicyBase):
    client_id: int


class PolicyUpdate(BaseModel):
    type: PolicyType | None = None
    name: str | None = None
    price: Decimal | None = None
    expiration_date: date | None = None
    coverage: str | None = None
    status: str | None = None
    client_id: int | None = None


class PolicyRead(PolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
