from datetime import date

from pydantic import BaseModel


class MenuPasteRequest(BaseModel):
    dining_hall_name: str
    menu_date: date
    raw_text: str


class MenuItemOut(BaseModel):
    id: int
    name: str
    station: str
    diet_tags: list[str]


class MenuOut(BaseModel):
    id: int
    dining_hall_name: str
    menu_date: date
    items: list[MenuItemOut]
