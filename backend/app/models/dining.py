from datetime import date, datetime

from sqlalchemy import ARRAY, Date, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DiningHall(Base):
    __tablename__ = "dining_halls"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)


class Menu(Base):
    __tablename__ = "menus"
    __table_args__ = (UniqueConstraint("dining_hall_id", "menu_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    dining_hall_id: Mapped[int] = mapped_column(
        ForeignKey("dining_halls.id", ondelete="CASCADE")
    )
    menu_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    items: Mapped[list["MenuItem"]] = relationship(
        back_populates="menu", cascade="all, delete-orphan"
    )


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    menu_id: Mapped[int] = mapped_column(ForeignKey("menus.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String)
    station: Mapped[str] = mapped_column(String)
    diet_tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    menu: Mapped["Menu"] = relationship(back_populates="items")
