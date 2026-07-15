from pydantic import BaseModel


class GroceryListItemOut(BaseModel):
    id: int
    ingredient_id: int
    ingredient_name: str
    total_quantity: float
    unit: str
    estimated_cost: float
    checked_off: bool


class GroceryListOut(BaseModel):
    id: int
    meal_plan_id: int
    items: list[GroceryListItemOut]
    total_cost: float


class ToggleItemRequest(BaseModel):
    checked_off: bool
