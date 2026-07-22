"""Siembra de pólizas.

Crea una póliza por cada cliente que tiene un reclamo, con el `type` igual al `object` del
reclamo (para poder vincular claim<->póliza de forma coherente en la Fase B). La prima se
CALCULA con el motor de pricing. Incluye variedad de estados (vigente, vence pronto,
vencida, cancelada) para que la lista se vea realista.

Uso standalone (NO toca clientes/reclamos):
    .venv/bin/python -m scripts.seed_policies
"""
from datetime import date, timedelta

from sqlalchemy import select, text

from app.clients.models import Client
from app.core.database import SessionLocal
from app.policies import pricing
from app.policies.models import Coverage, Policy, PolicyEvent
from scripts.seed_claims import CLAIMS

# Importar el resto de modelos para que el registro de mappers esté completo (relaciones).
from app.auth import models as _auth  # noqa: F401
from app.supervisors import models as _supervisors  # noqa: F401
from app.agents import models as _agents  # noqa: F401
from app.claims.models import ClaimCase

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
            status, effective, expiration = "expired", today - timedelta(days=400), today - timedelta(days=35)
        elif i % 13 == 0:
            status, cancel_date, cancel_reason = "cancelled", today - timedelta(days=20), "insured_request"
        elif i % 7 == 0:
            expiration = today + timedelta(days=20)  # vence pronto

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
            # `rating_factors` es JSON: Decimal no es serializable ahí (ver BUG-13).
            rating_factors={"base_rate": float(q["base_rate"]), "risk_factor": rf,
                            "tax_rate": q["tax_rate"], "policy_fee": q["policy_fee"]},
            client_id=client.id,
        )
        for c in q["coverages"]:
            policy.coverages.append(Coverage(**c))
        db.add(policy)
        db.flush()
        policy.events.append(PolicyEvent(
            policy_id=policy.id, event_type="issued", to_status="in_force",
            payload={"total_premium": float(q["total_premium"])},
        ))
        if status == "cancelled":
            policy.events.append(PolicyEvent(
                policy_id=policy.id, event_type="cancelled",
                from_status="in_force", to_status="cancelled",
                payload={"reason": cancel_reason},
            ))
        count += 1
    db.commit()
    return count


def backfill_claim_policies(db) -> int:
    """Vincula cada reclamo existente con la póliza de su cliente del mismo tipo (demo coherente)."""
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
        db.execute(text("UPDATE claims SET policy_id = NULL"))   # romper FK antes de borrar pólizas
        db.execute(text("DELETE FROM policy_events"))
        db.execute(text("DELETE FROM coverages"))
        db.execute(text("DELETE FROM policies"))
        db.commit()
        n = seed_policies(db)
        m = backfill_claim_policies(db)
        print(f"Seeded {n} policies; vinculados {m} claims a su póliza.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
