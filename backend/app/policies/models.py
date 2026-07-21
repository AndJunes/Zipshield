from datetime import date, datetime, timezone

from sqlalchemy import String, Numeric, Date, DateTime, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(20))          # car | laptop | package (LOB)
    name: Mapped[str] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(20), default="in_force", index=True)

    # Vigencia
    effective_date: Mapped[date] = mapped_column(Date)
    expiration_date: Mapped[date] = mapped_column(Date)
    cancel_date: Mapped[date | None] = mapped_column(Date, default=None)
    cancel_reason: Mapped[str | None] = mapped_column(String(50), default=None)

    # Pricing (desglose de la prima — calculado, auditable)
    sum_insured: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    deductible: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    base_rate: Mapped[float] = mapped_column(Numeric(6, 4), default=0)
    risk_factor: Mapped[float] = mapped_column(Numeric(5, 3), default=1)
    net_premium: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    taxes_fees: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    price: Mapped[float] = mapped_column(Numeric(12, 2))    # prima total (= net_premium + taxes_fees)
    rating_factors: Mapped[dict] = mapped_column(JSON, default=dict)

    coverage: Mapped[str | None] = mapped_column(String(500), default=None)  # descripción legible

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    client: Mapped["Client"] = relationship(back_populates="policies")

    coverages: Mapped[list["Coverage"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan"
    )
    events: Mapped[list["PolicyEvent"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan"
    )


class Coverage(Base):
    """Una cobertura de una póliza, con su límite, deducible y prima propios (rating por cobertura)."""

    __tablename__ = "coverages"

    id: Mapped[int] = mapped_column(primary_key=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), index=True)
    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(100))
    limit_amount: Mapped[float] = mapped_column(Numeric(12, 2))
    deductible: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    premium: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    params: Mapped[dict] = mapped_column(JSON, default=dict)

    policy: Mapped["Policy"] = relationship(back_populates="coverages")


class PolicyEvent(Base):
    """Registro inmutable de cada transacción de la póliza (timeline auditable)."""

    __tablename__ = "policy_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(40))   # issued | endorsed | renewed | cancelled | payment | claim_filed
    from_status: Mapped[str | None] = mapped_column(String(20), default=None)
    to_status: Mapped[str | None] = mapped_column(String(20), default=None)
    actor_id: Mapped[int | None] = mapped_column(Integer, default=None)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    policy: Mapped["Policy"] = relationship(back_populates="events")
