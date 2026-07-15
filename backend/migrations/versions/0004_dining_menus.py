"""dining hall menus

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-15
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dining_halls",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
    )

    op.create_table(
        "menus",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "dining_hall_id",
            sa.Integer(),
            sa.ForeignKey("dining_halls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("menu_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("dining_hall_id", "menu_date", name="uq_menu_hall_date"),
    )

    op.create_table(
        "menu_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "menu_id", sa.Integer(), sa.ForeignKey("menus.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("station", sa.String(), nullable=False),
        sa.Column("diet_tags", postgresql.ARRAY(sa.String()), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("menu_items")
    op.drop_table("menus")
    op.drop_table("dining_halls")
