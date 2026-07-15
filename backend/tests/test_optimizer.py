from app.services.optimizer import (
    MEAL_SLOTS,
    ProfileConstraints,
    RecipeCandidate,
    filter_candidates,
    solve_weekly_plan,
)


def make_recipe(id_, cost, calories, equipment=None, diet_tags=None, ingredients=None) -> RecipeCandidate:
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
