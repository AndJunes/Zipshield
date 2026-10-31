"""claims: analysis_status for the background AI analysis

Revision ID: c4f2a91d03e7
Revises: b10067cf1dca
Create Date: 2026-10-30 22:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4f2a91d03e7"
down_revision: str | None = "b10067cf1dca"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "claims",
        sa.Column("analysis_status", sa.String(length=10), nullable=False, server_default="none"),
    )


def downgrade() -> None:
    op.drop_column("claims", "analysis_status")
