from sqlalchemy import String, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    phone: Mapped[str | None] = mapped_column(String(30), default=None)
    city: Mapped[str | None] = mapped_column(String(100), default=None)
    client_number: Mapped[str] = mapped_column(String(50), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    photo_url: Mapped[str | None] = mapped_column(String(500), default=None)

    past_claim_count: Mapped[int] = mapped_column(Integer, default=0)
    accept_claim: Mapped[int] = mapped_column(Integer, default=0)
    manual_review_claim: Mapped[int] = mapped_column(Integer, default=0)
    rejected_claim: Mapped[int] = mapped_column(Integer, default=0)
    last_90_days_claim_count: Mapped[int] = mapped_column(Integer, default=0)
    history_flags: Mapped[list[str]] = mapped_column(JSON, default=list)
    history_summary: Mapped[str | None] = mapped_column(String(500), default=None)

    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    agent: Mapped["Agent"] = relationship(back_populates="clients")

    policies: Mapped[list["Policy"]] = relationship(back_populates="client")
