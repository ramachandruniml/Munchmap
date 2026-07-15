from datetime import date

from pydantic import BaseModel


class MealPlanGenerateRequest(BaseModel):
    week_start_date: date
    max_recipe_repeats: int = 3


class MealPlanEntryOut(BaseModel):
    day_of_week: int
    meal_slot: str
    recipe_id: int
    recipe_name: str
    cost: float


class MealPlanOut(BaseModel):
    id: int
    week_start_date: date
    total_cost: float
    status: str
    entries: list[MealPlanEntryOut]
