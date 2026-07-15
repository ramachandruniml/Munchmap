from app.services.embeddings import recipe_embedding_text


def test_recipe_embedding_text_joins_name_tags_and_ingredients() -> None:
    text = recipe_embedding_text(
        "Spicy Chicken Bowl", ["gluten-free"], ["chicken", "rice", "chili"]
    )

    assert text == "Spicy Chicken Bowl, gluten-free, chicken, rice, chili"


def test_recipe_embedding_text_handles_no_diet_tags() -> None:
    text = recipe_embedding_text("Toast", [], ["bread", "butter"])

    assert text == "Toast, bread, butter"
