from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


def _reject_future_date_of_loss(value: date | None) -> date | None:
    if value is not None and value > date.today():
        raise ValueError("date_of_loss no puede ser una fecha futura")
    return value


class ClaimObject(str, Enum):
    car = "car"
    laptop = "laptop"
    package = "package"


class ClaimStatus(str, Enum):
    supported = "supported"
    contradicted = "contradicted"
    not_enough_information = "not_enough_information"


class ClaimSeverity(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    unknown = "unknown"
    none = "none"


class ClaimBase(BaseModel):
    user_id: str
    object: ClaimObject
    conversation: str
    image_urls: list[str] = []
    evidence_standard_met: bool = False
    evidence_standard_met_reason: str = ""
    risk_flags: list[str] = []
    issue_type: str = "unknown"
    object_part: str = "unknown"
    claim_status: ClaimStatus = ClaimStatus.not_enough_information
    claim_status_justification: str = ""
    supporting_image_ids: list[str] = []
    valid_image: bool = True
    severity: ClaimSeverity = ClaimSeverity.unknown
    policy_id: int | None = None
    date_of_loss: date | None = None


class ClaimCreate(BaseModel):
    """Al crear, solo se reciben los 4 datos de entrada. Los 10 campos de análisis
    los genera la IA después (POST /claims/{id}/analyze)."""

    user_id: str
    object: ClaimObject
    conversation: str
    image_urls: list[str] = []
    policy_id: int | None = None
    date_of_loss: date | None = None

    _validate_date_of_loss = field_validator("date_of_loss")(_reject_future_date_of_loss)


class ClaimUpdate(BaseModel):
    """Solo campos de ENTRADA editables manualmente. Los 10 campos de análisis (ver
    ANALYSIS_FIELDS en claims/service.py) se escriben exclusivamente vía
    POST /claims/{id}/analyze — nunca a través de este PATCH genérico (ver BUG-02 en
    QA_AUDIT_REPORT.md)."""

    object: ClaimObject | None = None
    conversation: str | None = None
    image_urls: list[str] | None = None
    policy_id: int | None = None
    date_of_loss: date | None = None

    _validate_date_of_loss = field_validator("date_of_loss")(_reject_future_date_of_loss)


class ClaimRead(ClaimBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
