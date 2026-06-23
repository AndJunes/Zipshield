"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "supervisors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(150), unique=True, nullable=False),
        sa.Column("phone", sa.String(30)),
        sa.Column("city", sa.String(100)),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("contribution", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("losses", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("photo_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(150), unique=True, nullable=False),
        sa.Column("phone", sa.String(30)),
        sa.Column("city", sa.String(100)),
        sa.Column("agent_number", sa.String(50), unique=True, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("contribution", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("losses", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("photo_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("supervisor_id", sa.Integer(), sa.ForeignKey("supervisors.id"), nullable=False),
    )

    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(20), unique=True, nullable=False, index=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(150), unique=True, nullable=False),
        sa.Column("phone", sa.String(30)),
        sa.Column("city", sa.String(100)),
        sa.Column("client_number", sa.String(50), unique=True, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("photo_url", sa.String(500)),
        sa.Column("past_claim_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accept_claim", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("manual_review_claim", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_claim", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_90_days_claim_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("history_flags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("history_summary", sa.String(500)),
        sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=False),
    )

    op.create_table(
        "policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("expiration_date", sa.Date(), nullable=False),
        sa.Column("coverage", sa.String(500)),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(150), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, index=True),
        sa.Column("ref_id", sa.Integer()),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("photo_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "claims",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(20), nullable=False, index=True),
        sa.Column("object", sa.String(20), nullable=False),
        sa.Column("conversation", sa.Text(), nullable=False),
        sa.Column("image_urls", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("evidence_standard_met", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("evidence_standard_met_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("risk_flags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("issue_type", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("object_part", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("claim_status", sa.String(30), nullable=False, index=True),
        sa.Column("claim_status_justification", sa.Text(), nullable=False, server_default=""),
        sa.Column("supporting_image_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("valid_image", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("severity", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("claims")
    op.drop_table("users")
    op.drop_table("policies")
    op.drop_table("clients")
    op.drop_table("agents")
    op.drop_table("supervisors")
