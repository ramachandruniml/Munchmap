"""pantry items

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-15
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pantry_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ingredient_id",
            sa.Integer(),
            sa.ForeignKey("ingredients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Numeric(8, 3), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "profile_id", "ingredient_id", "unit", name="uq_pantry_item_profile_ingredient_unit"
        ),
    )


def downgrade() -> None:
    op.drop_table("pantry_items")
