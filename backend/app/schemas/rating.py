from pydantic import BaseModel


class RatingIn(BaseModel):
    liked: bool


class RatingOut(BaseModel):
    recipe_id: int
    liked: bool
