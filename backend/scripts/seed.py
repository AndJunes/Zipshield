"""Idempotent seed script.

Usage:
    python -m scripts.seed
"""
import unicodedata
from datetime import datetime

from sqlalchemy import text

from app.agents.models import Agent
from app.auth.models import User
from app.claims.models import ClaimCase
from app.clients.models import Client
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.policies.models import Policy  # noqa: F401  (registers the mapper)
from app.supervisors.models import Supervisor

from scripts.seed_data import AGENTS, SUPERVISORS
from scripts.seed_clients import CLIENTS
from scripts.seed_claims import CLAIMS


def slug(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    no_marks = "".join(c for c in decomposed if not unicodedata.combining(c))
    return no_marks.lower().replace(" ", "")


def split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.split(" ", 1)
    first = parts[0]
    last = parts[1] if len(parts) > 1 else ""
    return first, last


def truncate_all(db):
    # Order matters for FKs
    db.execute(text("DELETE FROM claims"))
    db.execute(text("DELETE FROM policies"))
    db.execute(text("DELETE FROM clients"))
    db.execute(text("DELETE FROM agents"))
    db.execute(text("DELETE FROM supervisors"))
    db.execute(text("DELETE FROM users"))
    db.commit()


def parse_dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def fix_sequences(db):
    """Realign Postgres id sequences after inserting rows with explicit ids.

    Inserting explicit primary keys does not advance the underlying sequence,
    so the next auto-generated id would collide. This bumps each sequence past
    the current max id. No-op on databases without serial sequences (e.g. SQLite).
    """
    for table in ("supervisors", "agents", "clients", "policies", "claims", "users"):
        db.execute(
            text(
                "SELECT setval(pg_get_serial_sequence(:t, 'id'), "
                "COALESCE((SELECT MAX(id) FROM " + table + "), 1))"
            ),
            {"t": table},
        )
    db.commit()


def seed_supervisors(db):
    for raw in SUPERVISORS:
        first, last = split_name(raw["full_name"])
        sup = Supervisor(
            id=raw["id"],
            first_name=first,
            last_name=last,
            email=f"{slug(first)}.{slug(last)}@zipshield.io",
            status=raw["status"],
            contribution=raw["contribution"],
            losses=raw["losses"],
            photo_url=raw["photo_url"],
            created_at=parse_dt(raw["created_at"]),
        )
        db.add(sup)
    db.commit()


def seed_agents(db):
    for raw in AGENTS:
        first, last = split_name(raw["full_name"])
        agent = Agent(
            id=raw["id"],
            first_name=first,
            last_name=last,
            email=f"{slug(first)}.{slug(last)}@zipshield.io",
            agent_number=f"AGT-{raw['id']:03d}",
            status=raw["status"],
            contribution=raw["contribution"],
            losses=raw["losses"],
            photo_url=raw["photo_url"],
            created_at=parse_dt(raw["created_at"]),
            supervisor_id=raw["supervisor_id"],
        )
        db.add(agent)
    db.commit()


def seed_clients(db):
    for raw in CLIENTS:
        client = Client(
            id=raw["id"],
            user_id=raw["user_id"],
            first_name=raw["first_name"],
            last_name=raw["last_name"],
            email=raw["email"],
            phone=raw["phone"],
            city=raw["city"],
            client_number=raw["client_number"],
            status=raw["status"],
            photo_url=raw["photo_url"],
            agent_id=raw["agent_id"],
            past_claim_count=raw["past_claim_count"],
            accept_claim=raw["accept_claim"],
            manual_review_claim=raw["manual_review_claim"],
            rejected_claim=raw["rejected_claim"],
            last_90_days_claim_count=raw["last_90_days_claim_count"],
            history_flags=raw["history_flags"],
            history_summary=raw["history_summary"],
        )
        db.add(client)
    db.commit()


def seed_claims(db):
    for raw in CLAIMS:
        claim = ClaimCase(
            id=raw["id"],
            user_id=raw["user_id"],
            object=raw["object"],
            conversation=raw["conversation"],
            image_urls=raw["image_urls"],
            evidence_standard_met=raw["evidence_standard_met"],
            evidence_standard_met_reason=raw["evidence_standard_met_reason"],
            risk_flags=raw["risk_flags"],
            issue_type=raw["issue_type"],
            object_part=raw["object_part"],
            claim_status=raw["claim_status"],
            claim_status_justification=raw["claim_status_justification"],
            supporting_image_ids=raw["supporting_image_ids"],
            valid_image=raw["valid_image"],
            severity=raw["severity"],
        )
        db.add(claim)
    db.commit()


def seed_users(db):
    # Admin
    db.add(
        User(
            email="admin@zipshield.io",
            password_hash=hash_password("admin1234"),
            role="admin",
            ref_id=None,
            first_name="Admin",
            last_name="Zipshield",
            photo_url="https://i.pravatar.cc/300?u=admin-zipshield",
        )
    )

    # Supervisors
    for raw in SUPERVISORS:
        first, last = split_name(raw["full_name"])
        db.add(
            User(
                email=f"{slug(first)}.{slug(last)}@zipshield.io",
                password_hash=hash_password("super1234"),
                role="supervisor",
                ref_id=raw["id"],
                first_name=first,
                last_name=last,
                photo_url=raw["photo_url"],
            )
        )

    # Agents
    for raw in AGENTS:
        first, last = split_name(raw["full_name"])
        db.add(
            User(
                email=f"{slug(first)}.{slug(last)}@zipshield.io",
                password_hash=hash_password("agent1234"),
                role="agent",
                ref_id=raw["id"],
                first_name=first,
                last_name=last,
                photo_url=raw["photo_url"],
            )
        )
    db.commit()


def main():
    db = SessionLocal()
    try:
        print("Truncating tables…")
        truncate_all(db)

        print(f"Seeding {len(SUPERVISORS)} supervisors…")
        seed_supervisors(db)

        print(f"Seeding {len(AGENTS)} agents…")
        seed_agents(db)

        print(f"Seeding {len(CLIENTS)} clients…")
        seed_clients(db)

        print(f"Seeding {len(CLAIMS)} claims…")
        seed_claims(db)

        print("Seeding users (1 admin + 10 supervisors + 12 agents)…")
        seed_users(db)

        print("Realigning id sequences…")
        fix_sequences(db)

        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
