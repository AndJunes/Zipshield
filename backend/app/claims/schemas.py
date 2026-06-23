from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


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


class ClaimCreate(ClaimBase):
    pass


class ClaimUpdate(BaseModel):
    object: ClaimObject | None = None
    conversation: str | None = None
    image_urls: list[str] | None = None
    evidence_standard_met: bool | None = None
    evidence_standard_met_reason: str | None = None
    risk_flags: list[str] | None = None
    issue_type: str | None = None
    object_part: str | None = None
    claim_status: ClaimStatus | None = None
    claim_status_justification: str | None = None
    supporting_image_ids: list[str] | None = None
    valid_image: bool | None = None
    severity: ClaimSeverity | None = None


class ClaimRead(ClaimBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
