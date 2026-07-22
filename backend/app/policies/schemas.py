from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


class PolicyType(str, Enum):
    # Reconciliado con ClaimObject (car/laptop/package). El label "Automóvil" se muestra en la UI.
    car = "car"
    laptop = "laptop"
    package = "package"


class PolicyStatus(str, Enum):
    quote = "quote"               # cotizada, sin cobertura
    underwriting = "underwriting"  # en suscripción
    pending_info = "pending_info"  # en suscripción, esperando información del asegurado
    in_force = "in_force"         # vigente (canónico para reclamos)
    pending_cancel = "pending_cancel"  # en mora / período de gracia
    cancelled = "cancelled"       # cancelada anticipadamente
    expired = "expired"           # venció sin renovar
    declined = "declined"         # rechazada en suscripción (terminal)


class CoverageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    limit_amount: Decimal
    deductible: Decimal
    premium: Decimal


class PolicyCreate(BaseModel):
    """Al crear, el agente ingresa los datos del riesgo; la prima la calcula el backend."""

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
    """Cotización (sin guardar): el agente ingresa el riesgo, el backend devuelve el precio."""

    type: PolicyType
    sum_insured: Decimal
    client_id: int | None = None   # si se pasa, el risk_factor sale del historial del cliente

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
    price: Decimal               # prima total
    coverage: str | None = None
    coverages: list[CoverageRead] = []
