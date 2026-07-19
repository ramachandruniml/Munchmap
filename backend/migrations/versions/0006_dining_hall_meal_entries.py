"""dining hall meal entries

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-19
"""

import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("meal_plan_entries", "recipe_id", nullable=True)
    op.add_column(
        "meal_plan_entries",
        sa.Column("is_dining_hall", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("meal_plan_entries", "is_dining_hall")
    op.alter_column("meal_plan_entries", "recipe_id", nullable=False)
