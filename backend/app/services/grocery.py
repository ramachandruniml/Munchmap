from collections import defaultdict
from dataclasses import dataclass


@dataclass
class RecipeIngredientLine:
    ingredient_id: int
    quantity: float
    unit: str
    unit_cost: float


@dataclass
class GroceryLine:
    ingredient_id: int
    total_quantity: float
    unit: str
    estimated_cost: float


def build_grocery_list(
    recipe_ingredients_by_entry: list[list[RecipeIngredientLine]],
    pantry_quantities: dict[tuple[int, str], float] | None = None,
) -> list[GroceryLine]:
    """Consolidate ingredients across every meal-plan entry's recipe.

    Ingredients are grouped by (ingredient_id, unit) - the same ingredient in
    different units is kept as separate lines, since converting between
    arbitrary units (e.g. "cups" vs "grams") isn't reliable without a
    per-ingredient density table.

    ``pantry_quantities`` (keyed the same way) is subtracted from each line's
    total before it's returned; a line whose quantity is fully covered by the
    pantry is dropped entirely.
    """
    totals: dict[tuple[int, str], float] = defaultdict(float)
    unit_costs: dict[tuple[int, str], float] = {}

    for lines in recipe_ingredients_by_entry:
        for line in lines:
            key = (line.ingredient_id, line.unit)
            totals[key] += line.quantity
            unit_costs[key] = line.unit_cost

    pantry_quantities = pantry_quantities or {}
    lines_out = []
    for (ingredient_id, unit), quantity in totals.items():
        remaining = max(0.0, quantity - pantry_quantities.get((ingredient_id, unit), 0.0))
        if remaining <= 0:
            continue
        lines_out.append(
            GroceryLine(
                ingredient_id=ingredient_id,
                total_quantity=remaining,
                unit=unit,
                estimated_cost=round(remaining * unit_costs[(ingredient_id, unit)], 2),
            )
        )
    return lines_out
