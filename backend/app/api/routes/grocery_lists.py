import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import GroceryList, GroceryListItem, Ingredient, MealPlan, MealPlanEntry, RecipeIngredient
from app.schemas.grocery_list import GroceryListItemOut, GroceryListOut, ToggleItemRequest
from app.services.grocery import RecipeIngredientLine, build_grocery_list

router = APIRouter(tags=["grocery-lists"])


async def _get_owned_meal_plan(
    db: AsyncSession, meal_plan_id: int, user_id: uuid.UUID
) -> MealPlan:
    meal_plan = await db.get(MealPlan, meal_plan_id)
    if meal_plan is None or meal_plan.user_id != user_id:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return meal_plan


async def _get_owned_grocery_list(
    db: AsyncSession, grocery_list_id: int, user_id: uuid.UUID
) -> GroceryList:
    grocery_list = await db.get(GroceryList, grocery_list_id)
    if grocery_list is None:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    await _get_owned_meal_plan(db, grocery_list.meal_plan_id, user_id)
    return grocery_list


async def _serialize(db: AsyncSession, grocery_list: GroceryList) -> GroceryListOut:
    result = await db.execute(
        select(GroceryListItem, Ingredient.name)
        .join(Ingredient, Ingredient.id == GroceryListItem.ingredient_id)
        .where(GroceryListItem.grocery_list_id == grocery_list.id)
        .order_by(Ingredient.name)
    )
    items = [
        GroceryListItemOut(
            id=item.id,
            ingredient_id=item.ingredient_id,
            ingredient_name=name,
            total_quantity=float(item.total_quantity),
            unit=item.unit,
            estimated_cost=float(item.estimated_cost),
            checked_off=item.checked_off,
        )
        for item, name in result.all()
    ]
    return GroceryListOut(
        id=grocery_list.id,
        meal_plan_id=grocery_list.meal_plan_id,
        items=items,
        total_cost=round(sum(i.estimated_cost for i in items), 2),
    )


@router.post("/meal-plans/{meal_plan_id}/grocery-list", response_model=GroceryListOut)
async def generate_grocery_list(
    meal_plan_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GroceryListOut:
    await _get_owned_meal_plan(db, meal_plan_id, user.id)

    existing = await db.scalar(
        select(GroceryList).where(GroceryList.meal_plan_id == meal_plan_id)
    )
    if existing is not None:
        return await _serialize(db, existing)

    result = await db.execute(
        select(RecipeIngredient, Ingredient.unit_cost)
        .join(Ingredient, Ingredient.id == RecipeIngredient.ingredient_id)
        .join(MealPlanEntry, MealPlanEntry.recipe_id == RecipeIngredient.recipe_id)
        .where(MealPlanEntry.meal_plan_id == meal_plan_id)
    )
    lines = [
        RecipeIngredientLine(
            ingredient_id=ri.ingredient_id,
            quantity=float(ri.quantity),
            unit=ri.unit,
            unit_cost=float(unit_cost),
        )
        for ri, unit_cost in result.all()
    ]
    grocery_lines = build_grocery_list([lines])

    grocery_list = GroceryList(meal_plan_id=meal_plan_id)
    grocery_list.items = [
        GroceryListItem(
            ingredient_id=line.ingredient_id,
            total_quantity=line.total_quantity,
            unit=line.unit,
            estimated_cost=line.estimated_cost,
        )
        for line in grocery_lines
    ]
    db.add(grocery_list)
    await db.commit()
    await db.refresh(grocery_list)
    return await _serialize(db, grocery_list)


@router.get("/grocery-lists/{grocery_list_id}", response_model=GroceryListOut)
async def get_grocery_list(
    grocery_list_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GroceryListOut:
    grocery_list = await _get_owned_grocery_list(db, grocery_list_id, user.id)
    return await _serialize(db, grocery_list)


@router.patch(
    "/grocery-lists/{grocery_list_id}/items/{item_id}", response_model=GroceryListItemOut
)
async def toggle_item(
    grocery_list_id: int,
    item_id: int,
    payload: ToggleItemRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GroceryListItemOut:
    await _get_owned_grocery_list(db, grocery_list_id, user.id)

    item = await db.get(GroceryListItem, item_id)
    if item is None or item.grocery_list_id != grocery_list_id:
        raise HTTPException(status_code=404, detail="Item not found")

    item.checked_off = payload.checked_off
    await db.commit()
    await db.refresh(item)

    ingredient = await db.get(Ingredient, item.ingredient_id)
    return GroceryListItemOut(
        id=item.id,
        ingredient_id=item.ingredient_id,
        ingredient_name=ingredient.name,
        total_quantity=float(item.total_quantity),
        unit=item.unit,
        estimated_cost=float(item.estimated_cost),
        checked_off=item.checked_off,
    )
