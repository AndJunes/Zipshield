from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.clients.models import Client
    from app.supervisors.models import Supervisor


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    phone: Mapped[str | None] = mapped_column(String(30), default=None)
    city: Mapped[str | None] = mapped_column(String(100), default=None)
    agent_number: Mapped[str] = mapped_column(String(50), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    contribution: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    losses: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    photo_url: Mapped[str | None] = mapped_column(String(500), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    supervisor_id: Mapped[int] = mapped_column(ForeignKey("supervisors.id"))
    supervisor: Mapped["Supervisor"] = relationship(back_populates="agents")

    clients: Mapped[list["Client"]] = relationship(back_populates="agent")
