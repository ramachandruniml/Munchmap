"""initial core-loop schema

Revision ID: 0001
Revises:
Create Date: 2026-07-14
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("weekly_budget", sa.Numeric(8, 2), nullable=False),
        sa.Column("equipment", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("dietary_restrictions", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("allergies", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("dislikes", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("calorie_target", sa.Integer(), nullable=True),
        sa.Column("protein_target_g", sa.Integer(), nullable=True),
        sa.Column("carb_target_g", sa.Integer(), nullable=True),
        sa.Column("fat_target_g", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["id"], ["auth.users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "ingredients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("unit_cost", sa.Numeric(8, 4), nullable=False),
    )

    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("instructions", sa.String(), nullable=False),
        sa.Column("cook_time_minutes", sa.Integer(), nullable=False),
        sa.Column("servings", sa.Integer(), nullable=False),
        sa.Column("cost_per_serving", sa.Numeric(8, 2), nullable=False),
        sa.Column("calories", sa.Integer(), nullable=False),
        sa.Column("protein_g", sa.Numeric(6, 2), nullable=False),
        sa.Column("carb_g", sa.Numeric(6, 2), nullable=False),
        sa.Column("fat_g", sa.Numeric(6, 2), nullable=False),
        sa.Column("equipment_required", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("diet_tags", postgresql.ARRAY(sa.String()), nullable=False),
    )

    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "recipe_id",
            sa.Integer(),
            sa.ForeignKey("recipes.id", ondelete="CASCADE"),
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
    )

    op.create_table(
        "meal_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("week_start_date", sa.Date(), nullable=False),
        sa.Column("total_cost", sa.Numeric(8, 2), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "meal_plan_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "meal_plan_id",
            sa.Integer(),
            sa.ForeignKey("meal_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("meal_slot", sa.String(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), sa.ForeignKey("recipes.id"), nullable=False),
        sa.Column("cost", sa.Numeric(8, 2), nullable=False),
    )

    op.create_table(
        "grocery_lists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "meal_plan_id",
            sa.Integer(),
            sa.ForeignKey("meal_plans.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("generated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "grocery_list_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "grocery_list_id",
            sa.Integer(),
            sa.ForeignKey("grocery_lists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ingredient_id", sa.Integer(), sa.ForeignKey("ingredients.id"), nullable=False),
        sa.Column("total_quantity", sa.Numeric(8, 3), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("estimated_cost", sa.Numeric(8, 2), nullable=False),
        sa.Column("checked_off", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_table("grocery_list_items")
    op.drop_table("grocery_lists")
    op.drop_table("meal_plan_entries")
    op.drop_table("meal_plans")
    op.drop_table("recipe_ingredients")
    op.drop_table("recipes")
    op.drop_table("ingredients")
    op.drop_table("profiles")
