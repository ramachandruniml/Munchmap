from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.recipe import Ingredient


class GroceryList(Base):
    __tablename__ = "grocery_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    meal_plan_id: Mapped[int] = mapped_column(
        ForeignKey("meal_plans.id", ondelete="CASCADE"), unique=True
    )
    generated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    items: Mapped[list["GroceryListItem"]] = relationship(
        back_populates="grocery_list", cascade="all, delete-orphan"
    )


class GroceryListItem(Base):
    __tablename__ = "grocery_list_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    grocery_list_id: Mapped[int] = mapped_column(
        ForeignKey("grocery_lists.id", ondelete="CASCADE")
    )
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"))
    total_quantity: Mapped[float] = mapped_column(Numeric(8, 3))
    unit: Mapped[str] = mapped_column(String)
    estimated_cost: Mapped[float] = mapped_column(Numeric(8, 2))
    checked_off: Mapped[bool] = mapped_column(Boolean, default=False)

    grocery_list: Mapped["GroceryList"] = relationship(back_populates="items")
    ingredient: Mapped["Ingredient"] = relationship()
