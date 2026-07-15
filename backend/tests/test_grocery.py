from app.services.grocery import RecipeIngredientLine, build_grocery_list


def test_build_grocery_list_consolidates_shared_ingredients() -> None:
    entries = [
        [RecipeIngredientLine(ingredient_id=1, quantity=2, unit="cup", unit_cost=0.5)],
        [RecipeIngredientLine(ingredient_id=1, quantity=1, unit="cup", unit_cost=0.5)],
        [RecipeIngredientLine(ingredient_id=2, quantity=3, unit="each", unit_cost=1.2)],
    ]

    lines = build_grocery_list(entries)
    by_ingredient = {line.ingredient_id: line for line in lines}

    assert by_ingredient[1].total_quantity == 3
    assert by_ingredient[1].estimated_cost == 1.5
    assert by_ingredient[2].total_quantity == 3
    assert by_ingredient[2].estimated_cost == 3.6


def test_build_grocery_list_keeps_different_units_separate() -> None:
    entries = [
        [RecipeIngredientLine(ingredient_id=1, quantity=2, unit="cup", unit_cost=0.5)],
        [RecipeIngredientLine(ingredient_id=1, quantity=100, unit="gram", unit_cost=0.01)],
    ]

    lines = build_grocery_list(entries)

    assert len(lines) == 2


def test_build_grocery_list_drops_lines_fully_covered_by_pantry() -> None:
    entries = [[RecipeIngredientLine(ingredient_id=1, quantity=2, unit="cup", unit_cost=0.5)]]

    lines = build_grocery_list(entries, pantry_quantities={(1, "cup"): 5})

    assert lines == []


def test_build_grocery_list_reduces_lines_partially_covered_by_pantry() -> None:
    entries = [[RecipeIngredientLine(ingredient_id=1, quantity=3, unit="cup", unit_cost=0.5)]]

    lines = build_grocery_list(entries, pantry_quantities={(1, "cup"): 1})

    assert len(lines) == 1
    assert lines[0].total_quantity == 2
    assert lines[0].estimated_cost == 1.0


def test_build_grocery_list_ignores_pantry_quantity_in_different_unit() -> None:
    entries = [[RecipeIngredientLine(ingredient_id=1, quantity=2, unit="cup", unit_cost=0.5)]]

    lines = build_grocery_list(entries, pantry_quantities={(1, "gram"): 100})

    assert len(lines) == 1
    assert lines[0].total_quantity == 2
