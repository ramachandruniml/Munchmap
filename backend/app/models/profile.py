import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    weekly_budget: Mapped[float] = mapped_column(Numeric(8, 2))
    equipment: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    dietary_restrictions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    allergies: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    dislikes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    calorie_target: Mapped[int | None] = mapped_column(nullable=True)
    protein_target_g: Mapped[int | None] = mapped_column(nullable=True)
    carb_target_g: Mapped[int | None] = mapped_column(nullable=True)
    fat_target_g: Mapped[int | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
