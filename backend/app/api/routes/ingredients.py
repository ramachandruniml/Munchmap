from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import Ingredient
from app.schemas.ingredient import IngredientSubstitutesOut, SubstituteOut

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("/{ingredient_id}/substitutes", response_model=IngredientSubstitutesOut)
async def get_substitutes(
    ingredient_id: int,
    limit: int = 5,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IngredientSubstitutesOut:
    ingredient = await db.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    if ingredient.embedding is None:
        return IngredientSubstitutesOut(
            ingredient_id=ingredient.id, ingredient_name=ingredient.name, substitutes=[]
        )

    distance = Ingredient.embedding.cosine_distance(ingredient.embedding).label("distance")
    result = await db.execute(
        select(Ingredient, distance)
        .where(Ingredient.id != ingredient_id, Ingredient.embedding.isnot(None))
        .order_by(distance)
        .limit(limit)
    )
    substitutes = [
        SubstituteOut(id=row.id, name=row.name, similarity=round(1 - dist, 4))
        for row, dist in result.all()
    ]
    return IngredientSubstitutesOut(
        ingredient_id=ingredient.id, ingredient_name=ingredient.name, substitutes=substitutes
    )
