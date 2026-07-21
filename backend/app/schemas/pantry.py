from datetime import date

from pydantic import BaseModel


class PantryItemIn(BaseModel):
    ingredient_name: str
    quantity: float
    unit: str
    expires_at: date | None = None


class PantryItemUpdate(BaseModel):
    quantity: float
    expires_at: date | None = None


class PantryItemOut(BaseModel):
    id: int
    ingredient_id: int
    ingredient_name: str
    quantity: float
    unit: str
    expires_at: date | None


class ExpiringRecipeOut(BaseModel):
    recipe_id: int
    recipe_name: str
    cost_per_serving: float
    expiring_ingredients: list[str]
    soonest_expiration: date
