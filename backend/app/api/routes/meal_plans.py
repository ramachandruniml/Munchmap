import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import (
    MealPlan,
    MealPlanEntry,
    PantryItem,
    Profile,
    Recipe,
    RecipeIngredient,
    RecipeRating,
)
from app.schemas.meal_plan import MealPlanEntryOut, MealPlanGenerateRequest, MealPlanOut
from app.services.optimizer import ProfileConstraints, RecipeCandidate, solve_weekly_plan
from app.services.personalization import build_preference_vector, cosine_similarity

router = APIRouter(prefix="/meal-plans", tags=["meal-plans"])


async def _load_profile(db: AsyncSession, user_id: uuid.UUID) -> Profile:
    profile = await db.get(Profile, user_id)
    if profile is None:
        raise HTTPException(
            status_code=400, detail="Complete onboarding before generating a meal plan"
        )
    return profile


async def _load_candidates(
    db: AsyncSession, user_id: uuid.UUID
) -> tuple[list[RecipeCandidate], frozenset[int]]:
    result = await db.execute(
        select(Recipe).options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient)
        )
    )
    recipes = result.scalars().all()

    ratings_result = await db.execute(
        select(RecipeRating).where(RecipeRating.profile_id == user_id)
    )
    ratings = {r.recipe_id: r.liked for r in ratings_result.scalars()}
    embeddings_by_id = {r.id: r.embedding for r in recipes}
    liked_embeddings = [
        embeddings_by_id[rid]
        for rid, liked in ratings.items()
        if liked and embeddings_by_id.get(rid) is not None
    ]
    disliked_embeddings = [
        embeddings_by_id[rid]
        for rid, liked in ratings.items()
        if not liked and embeddings_by_id.get(rid) is not None
    ]
    preference_vector = build_preference_vector(liked_embeddings, disliked_embeddings)

    pantry_result = await db.execute(
        select(PantryItem.ingredient_id).where(PantryItem.profile_id == user_id)
    )
    pantry_ingredient_ids = frozenset(pantry_result.scalars())

    candidates = [
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
            cook_time_minutes=r.cook_time_minutes,
            preference_score=(
                cosine_similarity(r.embedding, preference_vector)
                if r.embedding is not None and preference_vector is not None
                else 0.0
            ),
            pantry_score=(
                sum(1 for ri in r.ingredients if ri.ingredient_id in pantry_ingredient_ids)
                / len(r.ingredients)
                if r.ingredients
                else 0.0
            ),
        )
        for r in recipes
    ]
    return candidates, pantry_ingredient_ids


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
        .outerjoin(Recipe, Recipe.id == MealPlanEntry.recipe_id)
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
            is_dining_hall=entry.is_dining_hall,
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
    candidates, pantry_ingredient_ids = await _load_candidates(db, user.id)

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
            candidates,
            constraints,
            max_recipe_repeats=payload.max_recipe_repeats,
            pantry_ingredient_ids=pantry_ingredient_ids,
            dining_hall_meals=payload.dining_hall_meals,
            weekly_cook_time_minutes=payload.weekly_cook_time_minutes,
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
            is_dining_hall=a.is_dining_hall,
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
