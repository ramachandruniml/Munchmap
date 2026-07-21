"""persist meal plan generation constraints

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-20
"""

import sqlalchemy as sa

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "meal_plans",
        sa.Column("dining_hall_meals", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "meal_plans", sa.Column("weekly_cook_time_minutes", sa.Integer(), nullable=True)
    )
    op.add_column(
        "meal_plans",
        sa.Column("max_recipe_repeats", sa.Integer(), nullable=False, server_default="3"),
    )


def downgrade() -> None:
    op.drop_column("meal_plans", "max_recipe_repeats")
    op.drop_column("meal_plans", "weekly_cook_time_minutes")
    op.drop_column("meal_plans", "dining_hall_meals")
