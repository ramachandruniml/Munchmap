import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import MealPlan, MealPlanEntry, Profile, Recipe, RecipeIngredient
from app.schemas.meal_plan import MealPlanEntryOut, MealPlanGenerateRequest, MealPlanOut
from app.services.optimizer import ProfileConstraints, RecipeCandidate, solve_weekly_plan

router = APIRouter(prefix="/meal-plans", tags=["meal-plans"])


async def _load_profile(db: AsyncSession, user_id: uuid.UUID) -> Profile:
    profile = await db.get(Profile, user_id)
    if profile is None:
        raise HTTPException(
            status_code=400, detail="Complete onboarding before generating a meal plan"
        )
    return profile


async def _load_candidates(db: AsyncSession) -> list[RecipeCandidate]:
    result = await db.execute(
        select(Recipe).options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient)
        )
    )
    recipes = result.scalars().all()
    return [
        RecipeCandidate(
            id=r.id,
            cost_per_serving=float(r.cost_per_serving),
            calories=r.calories,
            protein_g=float(r.protein_g),
            carb_g=float(r.carb_g),
            fat_g=float(r.fat_g),
            equipment_required=r.equipment_required,
            diet_tags=r.diet_tags,
            ingredients=[(ri.ingredient_id, ri.ingredient.name) for ri in r.ingredients],
        )
        for r in recipes
    ]


async def _get_owned_meal_plan(
    db: AsyncSession, meal_plan_id: int, user_id: uuid.UUID
) -> MealPlan:
    meal_plan = await db.get(MealPlan, meal_plan_id)
    if meal_plan is None or meal_plan.user_id != user_id:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return meal_plan


async def _serialize_meal_plan(db: AsyncSession, meal_plan: MealPlan) -> MealPlanOut:
    result = await db.execute(
        select(MealPlanEntry, Recipe.name)
        .join(Recipe, Recipe.id == MealPlanEntry.recipe_id)
        .where(MealPlanEntry.meal_plan_id == meal_plan.id)
        .order_by(MealPlanEntry.day_of_week, MealPlanEntry.meal_slot)
    )
    entries = [
        MealPlanEntryOut(
            day_of_week=entry.day_of_week,
            meal_slot=entry.meal_slot,
            recipe_id=entry.recipe_id,
            recipe_name=name,
            cost=float(entry.cost),
        )
        for entry, name in result.all()
    ]
    return MealPlanOut(
        id=meal_plan.id,
        week_start_date=meal_plan.week_start_date,
        total_cost=float(meal_plan.total_cost),
        status=meal_plan.status,
        entries=entries,
    )


@router.post("", response_model=MealPlanOut)
async def generate_meal_plan(
    payload: MealPlanGenerateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MealPlanOut:
    profile = await _load_profile(db, user.id)
    candidates = await _load_candidates(db)

    constraints = ProfileConstraints(
        weekly_budget=float(profile.weekly_budget),
        equipment=profile.equipment,
        dietary_restrictions=profile.dietary_restrictions,
        allergies=profile.allergies,
        dislikes=profile.dislikes,
        calorie_target=profile.calorie_target,
        protein_target_g=profile.protein_target_g,
        carb_target_g=profile.carb_target_g,
        fat_target_g=profile.fat_target_g,
    )

    try:
        assignments = solve_weekly_plan(
            candidates, constraints, max_recipe_repeats=payload.max_recipe_repeats
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    meal_plan = MealPlan(
        user_id=user.id,
        week_start_date=payload.week_start_date,
        total_cost=sum(a.cost for a in assignments),
        status="active",
    )
    meal_plan.entries = [
        MealPlanEntry(
            day_of_week=a.day_of_week,
            meal_slot=a.meal_slot,
            recipe_id=a.recipe_id,
            cost=a.cost,
        )
        for a in assignments
    ]
    db.add(meal_plan)
    await db.commit()
    await db.refresh(meal_plan)
    return await _serialize_meal_plan(db, meal_plan)


@router.get("/{meal_plan_id}", response_model=MealPlanOut)
async def get_meal_plan(
    meal_plan_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MealPlanOut:
    meal_plan = await _get_owned_meal_plan(db, meal_plan_id, user.id)
    return await _serialize_meal_plan(db, meal_plan)


@router.get("", response_model=list[MealPlanOut])
async def list_meal_plans(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MealPlanOut]:
    result = await db.execute(
        select(MealPlan)
        .where(MealPlan.user_id == user.id)
        .order_by(MealPlan.week_start_date.desc())
    )
    plans = result.scalars().all()
    return [await _serialize_meal_plan(db, plan) for plan in plans]
