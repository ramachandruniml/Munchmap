from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import Ingredient, PantryItem, Recipe, RecipeIngredient
from app.schemas.pantry import (
    ExpiringRecipeOut,
    PantryItemIn,
    PantryItemOut,
    PantryItemUpdate,
)

router = APIRouter(prefix="/pantry", tags=["pantry"])


async def _get_owned_item(db: AsyncSession, item_id: int, user_id) -> PantryItem:
    item = await db.get(PantryItem, item_id)
    if item is None or item.profile_id != user_id:
        raise HTTPException(status_code=404, detail="Pantry item not found")
    return item


@router.get("", response_model=list[PantryItemOut])
async def list_pantry_items(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PantryItemOut]:
    result = await db.execute(
        select(PantryItem, Ingredient.name)
        .join(Ingredient, Ingredient.id == PantryItem.ingredient_id)
        .where(PantryItem.profile_id == user.id)
        .order_by(Ingredient.name)
    )
    return [
        PantryItemOut(
            id=item.id,
            ingredient_id=item.ingredient_id,
            ingredient_name=name,
            quantity=float(item.quantity),
            unit=item.unit,
            expires_at=item.expires_at,
        )
        for item, name in result.all()
    ]


@router.get("/expiring-soon-recipes", response_model=list[ExpiringRecipeOut])
async def get_expiring_soon_recipes(
    days: int = 5,
    limit: int = 10,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ExpiringRecipeOut]:
    cutoff = date.today() + timedelta(days=days)
    soonest = func.min(PantryItem.expires_at).label("soonest_expiration")
    expiring_ingredients = func.array_agg(func.distinct(Ingredient.name)).label(
        "expiring_ingredients"
    )
    result = await db.execute(
        select(
            Recipe.id,
            Recipe.name,
            Recipe.cost_per_serving,
            soonest,
            expiring_ingredients,
        )
        .join(RecipeIngredient, RecipeIngredient.recipe_id == Recipe.id)
        .join(Ingredient, Ingredient.id == RecipeIngredient.ingredient_id)
        .join(PantryItem, PantryItem.ingredient_id == Ingredient.id)
        .where(
            PantryItem.profile_id == user.id,
            PantryItem.expires_at.isnot(None),
            PantryItem.expires_at <= cutoff,
        )
        .group_by(Recipe.id)
        .order_by(soonest)
        .limit(limit)
    )
    return [
        ExpiringRecipeOut(
            recipe_id=row.id,
            recipe_name=row.name,
            cost_per_serving=float(row.cost_per_serving),
            expiring_ingredients=row.expiring_ingredients,
            soonest_expiration=row.soonest_expiration,
        )
        for row in result.all()
    ]


@router.post("", response_model=PantryItemOut)
async def add_pantry_item(
    payload: PantryItemIn,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PantryItemOut:
    name = payload.ingredient_name.strip()
    ingredient = await db.scalar(
        select(Ingredient).where(func.lower(Ingredient.name) == name.lower())
    )
    if ingredient is None:
        ingredient = Ingredient(name=name, unit=payload.unit, unit_cost=0)
        db.add(ingredient)
        await db.flush()

    item = await db.scalar(
        select(PantryItem).where(
            PantryItem.profile_id == user.id,
            PantryItem.ingredient_id == ingredient.id,
            PantryItem.unit == payload.unit,
        )
    )
    if item is None:
        item = PantryItem(
            profile_id=user.id,
            ingredient_id=ingredient.id,
            quantity=payload.quantity,
            unit=payload.unit,
            expires_at=payload.expires_at,
        )
        db.add(item)
    else:
        item.quantity = float(item.quantity) + payload.quantity
        if payload.expires_at is not None:
            item.expires_at = payload.expires_at

    await db.commit()
    await db.refresh(item)
    return PantryItemOut(
        id=item.id,
        ingredient_id=item.ingredient_id,
        ingredient_name=ingredient.name,
        quantity=float(item.quantity),
        unit=item.unit,
        expires_at=item.expires_at,
    )


@router.patch("/{item_id}", response_model=PantryItemOut)
async def update_pantry_item(
    item_id: int,
    payload: PantryItemUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PantryItemOut:
    item = await _get_owned_item(db, item_id, user.id)
    item.quantity = payload.quantity
    item.expires_at = payload.expires_at
    await db.commit()
    await db.refresh(item)

    ingredient = await db.get(Ingredient, item.ingredient_id)
    return PantryItemOut(
        id=item.id,
        ingredient_id=item.ingredient_id,
        ingredient_name=ingredient.name,
        quantity=float(item.quantity),
        unit=item.unit,
        expires_at=item.expires_at,
    )


@router.delete("/{item_id}", status_code=204)
async def delete_pantry_item(
    item_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    item = await _get_owned_item(db, item_id, user.id)
    await db.delete(item)
    await db.commit()
    return Response(status_code=204)
