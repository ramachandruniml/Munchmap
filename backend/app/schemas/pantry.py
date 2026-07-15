from pydantic import BaseModel


class PantryItemIn(BaseModel):
    ingredient_name: str
    quantity: float
    unit: str


class PantryItemUpdate(BaseModel):
    quantity: float


class PantryItemOut(BaseModel):
    id: int
    ingredient_id: int
    ingredient_name: str
    quantity: float
    unit: str
