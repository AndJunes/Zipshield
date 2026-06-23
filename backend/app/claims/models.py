from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ClaimCase(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), index=True)
    object: Mapped[str] = mapped_column(String(20))
    conversation: Mapped[str] = mapped_column(Text)
    image_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence_standard_met: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence_standard_met_reason: Mapped[str] = mapped_column(Text, default="")
    risk_flags: Mapped[list[str]] = mapped_column(JSON, default=list)
    issue_type: Mapped[str] = mapped_column(String(50), default="unknown")
    object_part: Mapped[str] = mapped_column(String(50), default="unknown")
    claim_status: Mapped[str] = mapped_column(String(30), index=True)
    claim_status_justification: Mapped[str] = mapped_column(Text, default="")
    supporting_image_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    valid_image: Mapped[bool] = mapped_column(Boolean, default=True)
    severity: Mapped[str] = mapped_column(String(20), default="unknown")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
