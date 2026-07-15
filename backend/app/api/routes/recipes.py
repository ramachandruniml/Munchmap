from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import Recipe, RecipeRating
from app.schemas.rating import RatingIn, RatingOut
from app.schemas.recipe import RecipeSearchResult
from app.services.embeddings import embed_text

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/search", response_model=list[RecipeSearchResult])
async def search_recipes(
    q: str,
    limit: int = 10,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecipeSearchResult]:
    query_embedding = embed_text(q)
    result = await db.execute(
        select(Recipe)
        .where(Recipe.embedding.isnot(None))
        .order_by(Recipe.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    recipes = result.scalars().all()
    return [
        RecipeSearchResult(
            id=r.id,
            name=r.name,
            cost_per_serving=float(r.cost_per_serving),
            calories=r.calories,
            protein_g=float(r.protein_g),
            carb_g=float(r.carb_g),
            fat_g=float(r.fat_g),
            diet_tags=r.diet_tags,
        )
        for r in recipes
    ]


@router.post("/{recipe_id}/rating", response_model=RatingOut)
async def rate_recipe(
    recipe_id: int,
    payload: RatingIn,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RatingOut:
    recipe = await db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    rating = await db.scalar(
        select(RecipeRating).where(
            RecipeRating.profile_id == user.id, RecipeRating.recipe_id == recipe_id
        )
    )
    if rating is None:
        rating = RecipeRating(profile_id=user.id, recipe_id=recipe_id, liked=payload.liked)
        db.add(rating)
    else:
        rating.liked = payload.liked

    await db.commit()
    return RatingOut(recipe_id=recipe_id, liked=payload.liked)
