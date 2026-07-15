from anthropic import AsyncAnthropic
from pydantic import BaseModel

from app.core.config import get_settings

MODEL = "claude-opus-4-8"


class ParsedMenuItem(BaseModel):
    name: str
    station: str
    diet_tags: list[str]


class ParsedMenu(BaseModel):
    items: list[ParsedMenuItem]


def build_prompt(raw_text: str) -> str:
    return (
        "Extract dining hall menu items from the following raw menu text/HTML. "
        "For each item, identify its name, its station or category (e.g. Grill, "
        "Salad Bar, Dessert), and any dietary tags that apply from: vegetarian, "
        "vegan, gluten-free, dairy-free, low-carb. Omit items you can't confidently "
        "parse.\n\n"
        f"{raw_text}"
    )


async def parse_menu_items(raw_text: str) -> list[ParsedMenuItem]:
    client = AsyncAnthropic(api_key=get_settings().anthropic_api_key)
    response = await client.messages.parse(
        model=MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": build_prompt(raw_text)}],
        output_format=ParsedMenu,
    )
    return response.parsed_output.items
