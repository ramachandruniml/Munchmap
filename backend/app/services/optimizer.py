from collections import defaultdict
from dataclasses import dataclass, field

from ortools.sat.python import cp_model

MEAL_SLOTS = ["breakfast", "lunch", "dinner"]
DAYS = range(7)


@dataclass
class RecipeCandidate:
    id: int
    cost_per_serving: float
    calories: int
    protein_g: float
    carb_g: float
    fat_g: float
    equipment_required: list[str]
    diet_tags: list[str]
    ingredients: list[tuple[int, str]] = field(default_factory=list)
    preference_score: float = 0.0


@dataclass
class ProfileConstraints:
    weekly_budget: float
    equipment: list[str]
    dietary_restrictions: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    dislikes: list[str] = field(default_factory=list)
    calorie_target: int | None = None
    protein_target_g: int | None = None
    carb_target_g: int | None = None
    fat_target_g: int | None = None


@dataclass
class MealAssignment:
    day_of_week: int
    meal_slot: str
    recipe_id: int
    cost: float


def filter_candidates(
    recipes: list[RecipeCandidate], profile: ProfileConstraints
) -> list[RecipeCandidate]:
    equipment_set = set(profile.equipment)
    required_diet_tags = set(profile.dietary_restrictions)
    excluded = {a.lower() for a in (*profile.allergies, *profile.dislikes)}

    candidates = []
    for recipe in recipes:
        if not set(recipe.equipment_required).issubset(equipment_set):
            continue
        if not required_diet_tags.issubset(set(recipe.diet_tags)):
            continue
        ingredient_names = {name.lower() for _, name in recipe.ingredients}
        if any(bad in name for bad in excluded for name in ingredient_names):
            continue
        candidates.append(recipe)
    return candidates


def _scale_cents(amount: float) -> int:
    return int(round(amount * 100))


def solve_weekly_plan(
    recipes: list[RecipeCandidate],
    profile: ProfileConstraints,
    max_recipe_repeats: int = 3,
    ingredient_overlap_weight: float = 50.0,
    preference_weight: float = 20.0,
    nutrition_tolerance: float = 0.15,
    time_limit_seconds: float = 10.0,
) -> list[MealAssignment]:
    candidates = filter_candidates(recipes, profile)
    if not candidates:
        raise ValueError(
            "No recipes satisfy this profile's equipment, diet, and allergy constraints"
        )

    model = cp_model.CpModel()

    x: dict[tuple[int, str, int], cp_model.IntVar] = {}
    for day in DAYS:
        for slot in MEAL_SLOTS:
            slot_vars = []
            for recipe in candidates:
                var = model.NewBoolVar(f"x_{day}_{slot}_{recipe.id}")
                x[day, slot, recipe.id] = var
                slot_vars.append(var)
            model.AddExactlyOne(slot_vars)

    for recipe in candidates:
        uses = [x[day, slot, recipe.id] for day in DAYS for slot in MEAL_SLOTS]
        model.Add(sum(uses) <= max_recipe_repeats)

    def total(attr: str, scale: int = 1) -> cp_model.LinearExpr:
        return sum(
            x[day, slot, recipe.id] * int(round(getattr(recipe, attr) * scale))
            for day in DAYS
            for slot in MEAL_SLOTS
            for recipe in candidates
        )

    if profile.calorie_target:
        lo = int(profile.calorie_target * 7 * (1 - nutrition_tolerance))
        hi = int(profile.calorie_target * 7 * (1 + nutrition_tolerance))
        model.Add(total("calories") >= lo)
        model.Add(total("calories") <= hi)

    for attr, target in (
        ("protein_g", profile.protein_target_g),
        ("carb_g", profile.carb_target_g),
        ("fat_g", profile.fat_target_g),
    ):
        if target:
            lo = int(target * 100 * 7 * (1 - nutrition_tolerance))
            hi = int(target * 100 * 7 * (1 + nutrition_tolerance))
            model.Add(total(attr, scale=100) >= lo)
            model.Add(total(attr, scale=100) <= hi)

    total_cost_cents = sum(
        x[day, slot, recipe.id] * _scale_cents(recipe.cost_per_serving)
        for day in DAYS
        for slot in MEAL_SLOTS
        for recipe in candidates
    )
    model.Add(total_cost_cents <= _scale_cents(profile.weekly_budget))

    ingredient_uses: dict[int, list[cp_model.IntVar]] = defaultdict(list)
    for recipe in candidates:
        for ingredient_id, _ in recipe.ingredients:
            ingredient_uses[ingredient_id] += [
                x[day, slot, recipe.id] for day in DAYS for slot in MEAL_SLOTS
            ]

    overlap_terms = []
    for ingredient_id, uses in ingredient_uses.items():
        used = model.NewBoolVar(f"y_{ingredient_id}")
        for u in uses:
            model.Add(used >= u)
        overlap_terms.append(used)

    preference_terms = sum(
        x[day, slot, recipe.id] * int(round(recipe.preference_score * preference_weight))
        for day in DAYS
        for slot in MEAL_SLOTS
        for recipe in candidates
    )

    model.Minimize(
        total_cost_cents + int(ingredient_overlap_weight) * sum(overlap_terms) - preference_terms
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise ValueError("No feasible meal plan found within budget and nutrition targets")

    assignments = []
    for day in DAYS:
        for slot in MEAL_SLOTS:
            for recipe in candidates:
                if solver.Value(x[day, slot, recipe.id]):
                    assignments.append(
                        MealAssignment(
                            day_of_week=day,
                            meal_slot=slot,
                            recipe_id=recipe.id,
                            cost=recipe.cost_per_serving,
                        )
                    )
    return assignments
