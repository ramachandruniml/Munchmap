from app.services.optimizer import (
    MEAL_SLOTS,
    ProfileConstraints,
    RecipeCandidate,
    filter_candidates,
    solve_weekly_plan,
)


def make_recipe(
    id_,
    cost,
    calories,
    equipment=None,
    diet_tags=None,
    ingredients=None,
    preference_score=0.0,
    pantry_score=0.0,
    cook_time_minutes=0,
) -> RecipeCandidate:
    return RecipeCandidate(
        id=id_,
        cost_per_serving=cost,
        calories=calories,
        protein_g=20.0,
        carb_g=40.0,
        fat_g=10.0,
        equipment_required=equipment or [],
        diet_tags=diet_tags or [],
        ingredients=ingredients or [(id_, f"ingredient-{id_}")],
        preference_score=preference_score,
        pantry_score=pantry_score,
        cook_time_minutes=cook_time_minutes,
    )


def test_filter_candidates_excludes_missing_equipment() -> None:
    recipes = [
        make_recipe(1, 2.0, 500, equipment=["stovetop"]),
        make_recipe(2, 2.0, 500, equipment=["oven"]),
    ]
    profile = ProfileConstraints(weekly_budget=100, equipment=["stovetop"])

    candidates = filter_candidates(recipes, profile)

    assert [r.id for r in candidates] == [1]


def test_filter_candidates_excludes_allergens() -> None:
    recipes = [
        make_recipe(1, 2.0, 500, ingredients=[(1, "peanut butter")]),
        make_recipe(2, 2.0, 500, ingredients=[(2, "almond butter")]),
    ]
    profile = ProfileConstraints(weekly_budget=100, equipment=[], allergies=["peanut"])

    candidates = filter_candidates(recipes, profile)

    assert [r.id for r in candidates] == [2]


def test_solve_weekly_plan_respects_budget() -> None:
    recipes = [make_recipe(i, cost=2.0, calories=600) for i in range(1, 8)]
    profile = ProfileConstraints(weekly_budget=1000, equipment=[])

    assignments = solve_weekly_plan(recipes, profile)

    assert len(assignments) == 7 * len(MEAL_SLOTS)
    total_cost = sum(a.cost for a in assignments)
    assert total_cost <= profile.weekly_budget


def test_solve_weekly_plan_raises_when_over_budget() -> None:
    recipes = [make_recipe(1, cost=50.0, calories=600)]
    profile = ProfileConstraints(weekly_budget=5, equipment=[])

    try:
        solve_weekly_plan(recipes, profile)
        assert False, "expected ValueError for infeasible budget"
    except ValueError:
        pass


def test_solve_weekly_plan_minimizes_distinct_ingredients() -> None:
    # Two cheap recipes sharing one ingredient vs. many recipes with unique ingredients.
    shared = [
        make_recipe(1, cost=2.0, calories=600, ingredients=[(100, "rice"), (101, "beans")]),
        make_recipe(2, cost=2.0, calories=600, ingredients=[(100, "rice"), (102, "chicken")]),
    ]
    profile = ProfileConstraints(weekly_budget=1000, equipment=[])

    assignments = solve_weekly_plan(shared, profile, max_recipe_repeats=21)

    used_recipe_ids = {a.recipe_id for a in assignments}
    assert used_recipe_ids.issubset({1, 2})


def test_solve_weekly_plan_favors_higher_preference_score() -> None:
    # Same cost and shared ingredient (so cost/overlap terms are tied) - only
    # preference_score should distinguish them.
    recipes = [
        make_recipe(1, cost=2.0, calories=600, ingredients=[(100, "rice")], preference_score=0.0),
        make_recipe(2, cost=2.0, calories=600, ingredients=[(100, "rice")], preference_score=1.0),
    ]
    profile = ProfileConstraints(weekly_budget=1000, equipment=[])

    assignments = solve_weekly_plan(recipes, profile, max_recipe_repeats=21)

    recipe_2_count = sum(1 for a in assignments if a.recipe_id == 2)
    assert recipe_2_count == len(assignments)


def test_solve_weekly_plan_respects_dining_hall_meals_count() -> None:
    recipes = [make_recipe(i, cost=2.0, calories=600) for i in range(1, 8)]
    profile = ProfileConstraints(weekly_budget=1000, equipment=[])

    assignments = solve_weekly_plan(recipes, profile, dining_hall_meals=5)

    dining_hall_assignments = [a for a in assignments if a.is_dining_hall]
    cooked_assignments = [a for a in assignments if not a.is_dining_hall]
    assert len(dining_hall_assignments) == 5
    assert all(a.recipe_id is None and a.cost == 0.0 for a in dining_hall_assignments)
    assert len(cooked_assignments) == 21 - 5
    assert all(a.recipe_id is not None for a in cooked_assignments)


def test_solve_weekly_plan_raises_when_cook_time_budget_too_tight() -> None:
    recipes = [make_recipe(1, cost=1.0, calories=600, cook_time_minutes=60)]
    profile = ProfileConstraints(weekly_budget=1000, equipment=[])

    try:
        solve_weekly_plan(
            recipes,
            profile,
            max_recipe_repeats=21,
            dining_hall_meals=10,
            weekly_cook_time_minutes=300,
        )
        assert False, "expected ValueError for infeasible cook-time budget"
    except ValueError:
        pass


def test_solve_weekly_plan_favors_recipe_using_pantry_ingredients() -> None:
    # Same cost, different (non-shared) ingredients - only pantry ownership of
    # ingredient 200 should distinguish them.
    recipes = [
        make_recipe(1, cost=2.0, calories=600, ingredients=[(100, "flour")], pantry_score=0.0),
        make_recipe(2, cost=2.0, calories=600, ingredients=[(200, "rice")], pantry_score=1.0),
    ]
    profile = ProfileConstraints(weekly_budget=1000, equipment=[])

    assignments = solve_weekly_plan(
        recipes, profile, max_recipe_repeats=21, pantry_ingredient_ids=frozenset({200})
    )

    recipe_2_count = sum(1 for a in assignments if a.recipe_id == 2)
    assert recipe_2_count == len(assignments)


def test_solve_weekly_plan_locks_slot_to_requested_recipe() -> None:
    recipes = [make_recipe(i, cost=2.0, calories=600) for i in range(1, 8)]
    profile = ProfileConstraints(weekly_budget=1000, equipment=[])

    assignments = solve_weekly_plan(
        recipes, profile, locked_recipe_by_slot={(0, "breakfast"): 3}
    )

    locked = next(a for a in assignments if a.day_of_week == 0 and a.meal_slot == "breakfast")
    assert locked.recipe_id == 3


def test_solve_weekly_plan_excludes_recipe_from_slot() -> None:
    # Recipe 2 is strongly preferred everywhere - except the excluded slot, which
    # must fall back to recipe 1.
    recipes = [
        make_recipe(1, cost=2.0, calories=600, ingredients=[(100, "rice")], preference_score=0.0),
        make_recipe(2, cost=2.0, calories=600, ingredients=[(100, "rice")], preference_score=1.0),
    ]
    profile = ProfileConstraints(weekly_budget=1000, equipment=[])

    assignments = solve_weekly_plan(
        recipes,
        profile,
        max_recipe_repeats=21,
        excluded_recipe_by_slot={(0, "breakfast"): 2},
    )

    excluded_slot = next(
        a for a in assignments if a.day_of_week == 0 and a.meal_slot == "breakfast"
    )
    assert excluded_slot.recipe_id == 1
    other_slots = [
        a for a in assignments if not (a.day_of_week == 0 and a.meal_slot == "breakfast")
    ]
    assert all(a.recipe_id == 2 for a in other_slots)
