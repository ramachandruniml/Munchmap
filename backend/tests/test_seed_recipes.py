from scripts.seed_recipes import (
    infer_diet_tags,
    infer_equipment,
    match_price,
    normalize_ingredient,
    nutrition_to_grams,
    parse_quantity,
)


def test_parse_quantity_handles_whole_and_fraction() -> None:
    assert parse_quantity("2 cups flour") == 2.0
    assert parse_quantity("1/2 cup sugar") == 0.5
    assert parse_quantity("1 1/2 tsp vanilla") == 1.5
    assert parse_quantity("salt to taste") == 1.0


def test_normalize_ingredient_strips_quantity_and_unit() -> None:
    assert normalize_ingredient("2 cups all-purpose flour") == "all purpose flour"
    assert normalize_ingredient("1/2 teaspoon salt") == "salt"


def test_match_price_falls_back_to_default() -> None:
    prices = {"salt": 0.05, "olive oil": 0.35}
    assert match_price("salt", prices) == 0.05
    assert match_price("extra virgin olive oil", prices) == 0.35
    assert match_price("dragonfruit", prices) == 1.0


def test_infer_equipment_defaults_to_stovetop() -> None:
    assert infer_equipment(["mix ingredients", "serve cold"]) == ["stovetop"]
    assert infer_equipment(["preheat oven to 350", "bake for 20 minutes"]) == ["oven"]


def test_infer_diet_tags_filters_known_tags() -> None:
    assert infer_diet_tags(["vegetarian", "60-minutes-or-less", "vegan"]) == [
        "vegetarian",
        "vegan",
    ]


def test_nutrition_to_grams_converts_pdv() -> None:
    # [calories, total_fat%DV, sugar%DV, sodium%DV, protein%DV, sat_fat%DV, carbs%DV]
    result = nutrition_to_grams([300.0, 50.0, 20.0, 10.0, 40.0, 25.0, 20.0])
    assert result["calories"] == 300.0
    assert result["protein_g"] == 20.0
    assert result["carb_g"] == 55.0
    assert result["fat_g"] == 39.0
