from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import Recipe, RecipeIngredient, RecipeRating
from app.schemas.rating import RatingIn, RatingOut
from app.schemas.recipe import RecipeDetailOut, RecipeIngredientOut, RecipeSearchResult
from app.services.embeddings import embed_text

router = APIRouter(prefix="/recipes", tags=["recipes"])


async def _liked_map(db: AsyncSession, user_id, recipe_ids: list[int]) -> dict[int, bool]:
    if not recipe_ids:
        return {}
    result = await db.execute(
        select(RecipeRating.recipe_id, RecipeRating.liked).where(
            RecipeRating.profile_id == user_id, RecipeRating.recipe_id.in_(recipe_ids)
        )
    )
    return dict(result.all())


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
    liked_map = await _liked_map(db, user.id, [r.id for r in recipes])
    return [
        RecipeSearchResult(
            id=r.id,
            name=r.name,
            cost_per_serving=float(r.cost_per_serving),
            calories=r.calories,
            protein_g=float(r.protein_g),
            carb_g=float(r.carb_g),
            fat_g=float(r.fat_g),
            cook_time_minutes=r.cook_time_minutes,
            diet_tags=r.diet_tags,
            liked=liked_map.get(r.id),
        )
        for r in recipes
    ]


@router.get("/{recipe_id}", response_model=RecipeDetailOut)
async def get_recipe(
    recipe_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeDetailOut:
    result = await db.execute(
        select(Recipe)
        .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient))
        .where(Recipe.id == recipe_id)
    )
    recipe = result.scalar_one_or_none()
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    liked_map = await _liked_map(db, user.id, [recipe_id])

    return RecipeDetailOut(
        id=recipe.id,
        name=recipe.name,
        instructions=recipe.instructions,
        cook_time_minutes=recipe.cook_time_minutes,
        servings=recipe.servings,
        cost_per_serving=float(recipe.cost_per_serving),
        calories=recipe.calories,
        protein_g=float(recipe.protein_g),
        carb_g=float(recipe.carb_g),
        fat_g=float(recipe.fat_g),
        equipment_required=recipe.equipment_required,
        diet_tags=recipe.diet_tags,
        ingredients=[
            RecipeIngredientOut(
                ingredient_id=ri.ingredient_id,
                name=ri.ingredient.name,
                quantity=float(ri.quantity),
                unit=ri.unit,
            )
            for ri in recipe.ingredients
        ],
        liked=liked_map.get(recipe_id),
    )


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
