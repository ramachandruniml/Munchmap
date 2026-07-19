from datetime import date

from pydantic import BaseModel


class MealPlanGenerateRequest(BaseModel):
    week_start_date: date
    max_recipe_repeats: int = 3
    dining_hall_meals: int = 0
    weekly_cook_time_minutes: int | None = None


class MealPlanEntryOut(BaseModel):
    day_of_week: int
    meal_slot: str
    recipe_id: int | None
    recipe_name: str | None
    cost: float
    is_dining_hall: bool


class MealPlanOut(BaseModel):
    id: int
    week_start_date: date
    total_cost: float
    status: str
    entries: list[MealPlanEntryOut]
