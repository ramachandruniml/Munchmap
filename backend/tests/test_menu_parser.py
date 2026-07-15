from app.services.menu_parser import build_prompt


def test_build_prompt_includes_raw_text() -> None:
    prompt = build_prompt("Grilled Chicken - Grill Station\nTofu Stir Fry - Vegan")

    assert "Grilled Chicken - Grill Station" in prompt
    assert "Tofu Stir Fry - Vegan" in prompt


def test_build_prompt_includes_extraction_instructions() -> None:
    prompt = build_prompt("some menu text")

    assert "station" in prompt
    assert "diet" in prompt.lower()
