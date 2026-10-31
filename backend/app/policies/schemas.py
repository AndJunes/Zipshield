from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


class PolicyType(str, Enum):
    # Reconciled with ClaimObject (car/laptop/package). The "Automóvil" label is shown in the UI.
    car = "car"
    laptop = "laptop"
    package = "package"


class PolicyStatus(str, Enum):
    quote = "quote"               # quoted, no coverage yet
    underwriting = "underwriting"  # in underwriting
    pending_info = "pending_info"  # in underwriting, waiting on insured's information
    in_force = "in_force"         # active (canonical for claims)
    pending_cancel = "pending_cancel"  # past due / grace period
    cancelled = "cancelled"       # cancelled early
    expired = "expired"           # expired without renewal
    declined = "declined"         # declined in underwriting (terminal)


class CoverageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    limit_amount: Decimal
    deductible: Decimal
    premium: Decimal


class PolicyCreate(BaseModel):
    """On create, the agent enters the risk data; the backend computes the premium."""

    client_id: int
    type: PolicyType
    name: str
    sum_insured: Decimal
    deductible: Decimal = Decimal("0")
    effective_date: date
    term_months: int = 12
    coverage: str | None = None

    @field_validator("sum_insured")
    @classmethod
    def sum_insured_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("sum_insured must be greater than zero")
        return value


class PolicyUpdate(BaseModel):
    name: str | None = None
    coverage: str | None = None
    expiration_date: date | None = None


class QuoteRequest(BaseModel):
    """Quote (not saved): the agent enters the risk, the backend returns the price."""

    type: PolicyType
    sum_insured: Decimal
    client_id: int | None = None   # when given, risk_factor comes from the client's history

    @field_validator("sum_insured")
    @classmethod
    def sum_insured_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("sum_insured must be greater than zero")
        return value


class QuoteResponse(BaseModel):
    coverages: list[CoverageRead]
    net_premium: Decimal
    taxes_fees: Decimal
    total_premium: Decimal
    base_rate: Decimal
    risk_factor: Decimal


class PolicyEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    from_status: str | None = None
    to_status: str | None = None
    payload: dict
    created_at: datetime


class PolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    type: PolicyType
    name: str
    status: str
    effective_date: date
    expiration_date: date
    cancel_date: date | None = None
    cancel_reason: str | None = None
    sum_insured: Decimal
    deductible: Decimal
    net_premium: Decimal
    taxes_fees: Decimal
    price: Decimal               # total premium
    coverage: str | None = None
    coverages: list[CoverageRead] = []
