import uuid
from datetime import date, datetime

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.recipe import Recipe


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE")
    )
    week_start_date: Mapped[date] = mapped_column()
    total_cost: Mapped[float] = mapped_column(Numeric(8, 2))
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    entries: Mapped[list["MealPlanEntry"]] = relationship(
        back_populates="meal_plan", cascade="all, delete-orphan"
    )


class MealPlanEntry(Base):
    __tablename__ = "meal_plan_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    meal_plan_id: Mapped[int] = mapped_column(
        ForeignKey("meal_plans.id", ondelete="CASCADE")
    )
    day_of_week: Mapped[int] = mapped_column()
    meal_slot: Mapped[str] = mapped_column(String)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"))
    cost: Mapped[float] = mapped_column(Numeric(8, 2))

    meal_plan: Mapped["MealPlan"] = relationship(back_populates="entries")
    recipe: Mapped["Recipe"] = relationship()
