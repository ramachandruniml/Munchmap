from google import genai
from google.genai import types
from pydantic import BaseModel

from app.core.config import get_settings

MODEL = "gemini-flash-latest"


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
    client = genai.Client(api_key=get_settings().gemini_api_key)
    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=build_prompt(raw_text),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ParsedMenu,
        ),
    )
    parsed: ParsedMenu = response.parsed
    return parsed.items
