"""Seed recipes/ingredients from Kaggle's Food.com Recipes and Interactions dataset.

Download RAW_recipes.csv from:
    https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions
and place it at backend/data/RAW_recipes.csv, then run:

    python -m scripts.seed_recipes

Ingredient quantities and unit costs are approximate: the dataset gives ingredients as
free-text strings (e.g. "2 cups flour") with no structured quantity/unit/price, so this
script extracts a leading numeric quantity heuristically and prices each normalized
ingredient name against a small hand-curated lookup table
(data/ingredient_prices.json), falling back to a flat default for unmatched names.
Good enough to seed real numbers for the solver; not a substitute for a real pricing
API or a proper unit-conversion table.
"""

import ast
import asyncio
import csv
import json
import re
import sys
from pathlib import Path

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models import Ingredient, Recipe, RecipeIngredient
from app.services.embeddings import embed_text, recipe_embedding_text

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RECIPES_CSV = DATA_DIR / "RAW_recipes.csv"
PRICES_JSON = DATA_DIR / "ingredient_prices.json"

SAMPLE_SIZE = 500
MAX_MINUTES = 90
DEFAULT_SERVINGS = 4
DEFAULT_INGREDIENT_PRICE = 1.0

# FDA 2016 label daily-value reference amounts, used to convert the dataset's
# %DV nutrition fields back to grams.
DV_REFERENCE = {
    "total_fat_g": 78.0,
    "sugar_g": 50.0,
    "protein_g": 50.0,
    "saturated_fat_g": 20.0,
    "carbs_g": 275.0,
}

EQUIPMENT_KEYWORDS = {
    "oven": ["oven", "bake", "roast", "broil"],
    "stovetop": ["saute", "sauté", "simmer", "boil", "fry", "skillet", "stovetop", "pan"],
    "microwave": ["microwave"],
}
KNOWN_DIET_TAGS = {"vegetarian", "vegan", "gluten-free", "dairy-free", "low-carb"}

_LEADING_QTY_RE = re.compile(r"^(\d+\s+\d+/\d+|\d+/\d+|\d+\.\d+|\d+)")
_QUANTITY_WORD_RE = re.compile(
    r"^\d+[\d/. ]*\s*(cups?|tablespoons?|tbsp|teaspoons?|tsp|ounces?|oz|pounds?|lbs?|"
    r"grams?|g|kg|cans?|cloves?|slices?|pinch(es)?|dash(es)?)?\s*(of)?\s*"
)


def parse_quantity(raw: str) -> float:
    match = _LEADING_QTY_RE.match(raw.strip())
    if not match:
        return 1.0
    token = match.group(1)
    if "/" in token:
        parts = token.split()
        whole = float(parts[0]) if len(parts) > 1 else 0.0
        num, denom = parts[-1].split("/")
        return whole + float(num) / float(denom)
    return float(token)


def normalize_ingredient(raw: str) -> str:
    name = raw.lower().strip()
    name = _QUANTITY_WORD_RE.sub("", name)
    name = re.sub(r"[^a-z]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def match_price(name: str, prices: dict[str, float]) -> float:
    if name in prices:
        return prices[name]
    for key, price in prices.items():
        if key in name or name in key:
            return price
    return DEFAULT_INGREDIENT_PRICE


def infer_equipment(steps: list[str]) -> list[str]:
    text = " ".join(steps).lower()
    tags = [
        tag for tag, keywords in EQUIPMENT_KEYWORDS.items() if any(k in text for k in keywords)
    ]
    return tags or ["stovetop"]


def infer_diet_tags(tags: list[str]) -> list[str]:
    return [tag for tag in tags if tag in KNOWN_DIET_TAGS]


def nutrition_to_grams(nutrition: list[float]) -> dict[str, float]:
    calories, total_fat_dv, sugar_dv, _sodium_dv, protein_dv, _sat_fat_dv, carbs_dv = nutrition
    return {
        "calories": calories,
        "protein_g": protein_dv / 100 * DV_REFERENCE["protein_g"],
        "carb_g": carbs_dv / 100 * DV_REFERENCE["carbs_g"],
        "fat_g": total_fat_dv / 100 * DV_REFERENCE["total_fat_g"],
    }


async def seed() -> None:
    if not RECIPES_CSV.exists():
        sys.exit(
            f"Missing {RECIPES_CSV}.\n"
            "Download RAW_recipes.csv from "
            "https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions "
            "and place it there before running this script."
        )

    prices: dict[str, float] = json.loads(PRICES_JSON.read_text())
    ingredient_cache: dict[str, Ingredient] = {}
    recipe_count = 0

    async with async_session_factory() as session:
        with RECIPES_CSV.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if recipe_count >= SAMPLE_SIZE:
                    break
                try:
                    minutes = int(row["minutes"])
                    if minutes <= 0 or minutes > MAX_MINUTES:
                        continue
                    ingredients_raw = ast.literal_eval(row["ingredients"])
                    steps = ast.literal_eval(row["steps"])
                    tags = ast.literal_eval(row["tags"])
                    nutrition = ast.literal_eval(row["nutrition"])
                    if not ingredients_raw or not steps:
                        continue
                except (ValueError, SyntaxError, KeyError):
                    continue

                nutrients = nutrition_to_grams(nutrition)
                recipe_cost = 0.0
                recipe_ingredients: list[tuple[Ingredient, float]] = []

                for raw_name in ingredients_raw:
                    name = normalize_ingredient(raw_name)
                    if not name:
                        continue
                    quantity = parse_quantity(raw_name)

                    if name not in ingredient_cache:
                        existing = await session.scalar(
                            select(Ingredient).where(Ingredient.name == name)
                        )
                        if existing is None:
                            existing = Ingredient(
                                name=name, unit="unit", unit_cost=match_price(name, prices)
                            )
                            session.add(existing)
                            await session.flush()
                        ingredient_cache[name] = existing

                    ingredient = ingredient_cache[name]
                    recipe_cost += float(ingredient.unit_cost) * quantity
                    recipe_ingredients.append((ingredient, quantity))

                if not recipe_ingredients:
                    continue

                recipe = Recipe(
                    name=row["name"][:255],
                    instructions=" ".join(steps)[:4000],
                    cook_time_minutes=minutes,
                    servings=DEFAULT_SERVINGS,
                    cost_per_serving=round(recipe_cost / DEFAULT_SERVINGS, 2),
                    calories=int(nutrients["calories"]),
                    protein_g=round(nutrients["protein_g"], 2),
                    carb_g=round(nutrients["carb_g"], 2),
                    fat_g=round(nutrients["fat_g"], 2),
                    equipment_required=infer_equipment(steps),
                    diet_tags=infer_diet_tags(tags),
                )
                recipe.ingredients = [
                    RecipeIngredient(ingredient=ing, quantity=qty, unit="unit")
                    for ing, qty in recipe_ingredients
                ]
                recipe.embedding = embed_text(
                    recipe_embedding_text(
                        recipe.name,
                        recipe.diet_tags,
                        [ing.name for ing, _ in recipe_ingredients],
                    )
                )
                session.add(recipe)
                recipe_count += 1

        await session.commit()

    print(f"Seeded {recipe_count} recipes and {len(ingredient_cache)} ingredients.")


if __name__ == "__main__":
    asyncio.run(seed())
