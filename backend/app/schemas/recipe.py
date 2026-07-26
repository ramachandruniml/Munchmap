from pydantic import BaseModel


class RecipeSearchResult(BaseModel):
    id: int
    name: str
    cost_per_serving: float
    calories: int
    protein_g: float
    carb_g: float
    fat_g: float
    cook_time_minutes: int
    diet_tags: list[str]
    liked: bool | None = None


class RecipeIngredientOut(BaseModel):
    ingredient_id: int
    name: str
    quantity: float
    unit: str


class RecipeDetailOut(BaseModel):
    id: int
    name: str
    instructions: str
    cook_time_minutes: int
    servings: int
    cost_per_serving: float
    calories: int
    protein_g: float
    carb_g: float
    fat_g: float
    equipment_required: list[str]
    diet_tags: list[str]
    ingredients: list[RecipeIngredientOut]
    liked: bool | None = None
