from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import DiningHall, Menu, MenuItem
from app.schemas.dining import MenuItemOut, MenuOut, MenuPasteRequest
from app.services.menu_parser import parse_menu_items

router = APIRouter(prefix="/dining", tags=["dining"])


def _serialize(hall_name: str, menu: Menu) -> MenuOut:
    return MenuOut(
        id=menu.id,
        dining_hall_name=hall_name,
        menu_date=menu.menu_date,
        items=[
            MenuItemOut(id=item.id, name=item.name, station=item.station, diet_tags=item.diet_tags)
            for item in menu.items
        ],
    )


@router.post("/menus/paste", response_model=MenuOut)
async def paste_menu(
    payload: MenuPasteRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MenuOut:
    hall_name = payload.dining_hall_name.strip()
    hall = await db.scalar(select(DiningHall).where(DiningHall.name == hall_name))
    if hall is None:
        hall = DiningHall(name=hall_name)
        db.add(hall)
        await db.flush()

    menu = await db.scalar(
        select(Menu)
        .options(selectinload(Menu.items))
        .where(Menu.dining_hall_id == hall.id, Menu.menu_date == payload.menu_date)
    )
    if menu is None:
        menu = Menu(dining_hall_id=hall.id, menu_date=payload.menu_date)
        db.add(menu)
        await db.flush()
    else:
        await db.execute(delete(MenuItem).where(MenuItem.menu_id == menu.id))

    parsed_items = await parse_menu_items(payload.raw_text)
    menu.items = [
        MenuItem(name=item.name, station=item.station, diet_tags=item.diet_tags)
        for item in parsed_items
    ]

    await db.commit()
    await db.refresh(menu, attribute_names=["items"])
    return _serialize(hall.name, menu)


@router.get("/menus", response_model=MenuOut)
async def get_menu(
    dining_hall_name: str,
    menu_date: date,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MenuOut:
    hall = await db.scalar(select(DiningHall).where(DiningHall.name == dining_hall_name.strip()))
    if hall is None:
        raise HTTPException(status_code=404, detail="Dining hall not found")

    menu = await db.scalar(
        select(Menu)
        .options(selectinload(Menu.items))
        .where(Menu.dining_hall_id == hall.id, Menu.menu_date == menu_date)
    )
    if menu is None:
        raise HTTPException(status_code=404, detail="Menu not found")

    return _serialize(hall.name, menu)
