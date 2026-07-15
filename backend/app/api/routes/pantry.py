from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import Ingredient, PantryItem
from app.schemas.pantry import PantryItemIn, PantryItemOut, PantryItemUpdate

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
        )
        for item, name in result.all()
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
        )
        db.add(item)
    else:
        item.quantity = float(item.quantity) + payload.quantity

    await db.commit()
    await db.refresh(item)
    return PantryItemOut(
        id=item.id,
        ingredient_id=item.ingredient_id,
        ingredient_name=ingredient.name,
        quantity=float(item.quantity),
        unit=item.unit,
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
    await db.commit()
    await db.refresh(item)

    ingredient = await db.get(Ingredient, item.ingredient_id)
    return PantryItemOut(
        id=item.id,
        ingredient_id=item.ingredient_id,
        ingredient_name=ingredient.name,
        quantity=float(item.quantity),
        unit=item.unit,
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
