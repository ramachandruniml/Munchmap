import uuid

from pydantic import BaseModel, ConfigDict


class ProfileIn(BaseModel):
    weekly_budget: float
    equipment: list[str] = []
    dietary_restrictions: list[str] = []
    allergies: list[str] = []
    dislikes: list[str] = []
    calorie_target: int | None = None
    protein_target_g: int | None = None
    carb_target_g: int | None = None
    fat_target_g: int | None = None


class ProfileOut(ProfileIn):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
