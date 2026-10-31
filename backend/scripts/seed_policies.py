"""Policy seeding.

Creates one policy per client that has a claim, with `type` equal to the claim's `object`
(so claim<->policy can be linked coherently). The premium is COMPUTED with the pricing
engine. Includes a variety of statuses (in force, expiring soon, expired, cancelled) so
the listing looks realistic.

Standalone usage (does NOT touch clients/claims):
    .venv/bin/python -m scripts.seed_policies
"""

from datetime import date, timedelta

from sqlalchemy import select, text

from app.agents import models as _agents  # noqa: F401

# Import the remaining models so the mapper registry is complete (relationships).
from app.auth import models as _auth  # noqa: F401
from app.claims.models import ClaimCase
from app.clients.models import Client
from app.core.database import SessionLocal
from app.policies import pricing
from app.policies.models import Coverage, Policy, PolicyEvent
from app.supervisors import models as _supervisors  # noqa: F401
from scripts.seed_claims import CLAIMS

SUM_INSURED = {"car": 18000, "laptop": 1500, "package": 600}
RISK_FACTORS = [1.0, 1.0, 1.15, 0.9, 1.0, 1.25, 0.95]


def seed_policies(db) -> int:
    today = date.today()
    seen: set[str] = set()
    count = 0
    for i, raw in enumerate(CLAIMS):
        uid = raw["user_id"]
        if uid in seen:
            continue
        seen.add(uid)
        client = db.scalar(select(Client).where(Client.user_id == uid))
        if client is None:
            continue
        ptype = raw["object"]
        if ptype not in SUM_INSURED:
            continue

        si = SUM_INSURED[ptype] + (i % 5) * (SUM_INSURED[ptype] // 20)
        rf = RISK_FACTORS[i % len(RISK_FACTORS)]
        q = pricing.quote(ptype, si, risk_factor=rf)

        status = "in_force"
        effective = today - timedelta(days=60)
        expiration = effective + timedelta(days=365)
        cancel_date = None
        cancel_reason = None
        if i % 9 == 0:
            status, effective, expiration = (
                "expired",
                today - timedelta(days=400),
                today - timedelta(days=35),
            )
        elif i % 13 == 0:
            status, cancel_date, cancel_reason = (
                "cancelled",
                today - timedelta(days=20),
                "insured_request",
            )
        elif i % 7 == 0:
            expiration = today + timedelta(days=20)  # expiring soon

        policy = Policy(
            type=ptype,
            name=f"Póliza {ptype} · {client.first_name} {client.last_name}",
            status=status,
            effective_date=effective,
            expiration_date=expiration,
            cancel_date=cancel_date,
            cancel_reason=cancel_reason,
            sum_insured=si,
            deductible=q["coverages"][0]["deductible"],
            base_rate=q["base_rate"],
            risk_factor=rf,
            net_premium=q["net_premium"],
            taxes_fees=q["taxes_fees"],
            price=q["total_premium"],
            # `rating_factors` is JSON: Decimal is not serializable there.
            rating_factors={
                "base_rate": float(q["base_rate"]),
                "risk_factor": rf,
                "tax_rate": q["tax_rate"],
                "policy_fee": q["policy_fee"],
            },
            client_id=client.id,
        )
        for c in q["coverages"]:
            policy.coverages.append(Coverage(**c))
        db.add(policy)
        db.flush()
        policy.events.append(
            PolicyEvent(
                policy_id=policy.id,
                event_type="issued",
                to_status="in_force",
                payload={"total_premium": float(q["total_premium"])},
            )
        )
        if status == "cancelled":
            policy.events.append(
                PolicyEvent(
                    policy_id=policy.id,
                    event_type="cancelled",
                    from_status="in_force",
                    to_status="cancelled",
                    payload={"reason": cancel_reason},
                )
            )
        count += 1
    db.commit()
    return count


def backfill_claim_policies(db) -> int:
    """Link each existing claim to its client's policy of the same type (coherent demo data)."""
    linked = 0
    for claim in db.scalars(select(ClaimCase)).all():
        client = db.scalar(select(Client).where(Client.user_id == claim.user_id))
        if client is None:
            continue
        policy = db.scalar(
            select(Policy).where(Policy.client_id == client.id, Policy.type == claim.object)
        )
        if policy is None:
            continue
        claim.policy_id = policy.id
        claim.date_of_loss = min(policy.effective_date + timedelta(days=10), policy.expiration_date)
        linked += 1
    db.commit()
    return linked


def main() -> None:
    db = SessionLocal()
    try:
        db.execute(
            text("UPDATE claims SET policy_id = NULL")
        )  # break the FK before deleting policies
        db.execute(text("DELETE FROM policy_events"))
        db.execute(text("DELETE FROM coverages"))
        db.execute(text("DELETE FROM policies"))
        db.commit()
        n = seed_policies(db)
        m = backfill_claim_policies(db)
        print(f"Seeded {n} policies; linked {m} claims to their policy.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
