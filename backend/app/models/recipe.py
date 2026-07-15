from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    unit: Mapped[str] = mapped_column(String)
    unit_cost: Mapped[float] = mapped_column(Numeric(8, 4))


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    instructions: Mapped[str] = mapped_column(String)
    cook_time_minutes: Mapped[int] = mapped_column()
    servings: Mapped[int] = mapped_column()

    cost_per_serving: Mapped[float] = mapped_column(Numeric(8, 2))
    calories: Mapped[int] = mapped_column()
    protein_g: Mapped[float] = mapped_column(Numeric(6, 2))
    carb_g: Mapped[float] = mapped_column(Numeric(6, 2))
    fat_g: Mapped[float] = mapped_column(Numeric(6, 2))

    equipment_required: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    diet_tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)

    ingredients: Mapped[list["RecipeIngredient"]] = relationship(back_populates="recipe")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id", ondelete="CASCADE"))
    quantity: Mapped[float] = mapped_column(Numeric(8, 3))
    unit: Mapped[str] = mapped_column(String)

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")
    ingredient: Mapped["Ingredient"] = relationship()
