from pydantic import BaseModel


class RecipeSearchResult(BaseModel):
    id: int
    name: str
    cost_per_serving: float
    calories: int
    protein_g: float
    carb_g: float
    fat_g: float
    diet_tags: list[str]
