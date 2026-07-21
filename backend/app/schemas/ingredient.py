from pydantic import BaseModel


class SubstituteOut(BaseModel):
    id: int
    name: str
    similarity: float


class IngredientSubstitutesOut(BaseModel):
    ingredient_id: int
    ingredient_name: str
    substitutes: list[SubstituteOut]
