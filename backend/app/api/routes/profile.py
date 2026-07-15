from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import Profile
from app.schemas.profile import ProfileIn, ProfileOut

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
async def get_profile(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Profile:
    profile = await db.get(Profile, user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found - complete onboarding")
    return profile


@router.put("", response_model=ProfileOut)
async def upsert_profile(
    payload: ProfileIn,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Profile:
    profile = await db.get(Profile, user.id)
    if profile is None:
        profile = Profile(id=user.id, **payload.model_dump())
        db.add(profile)
    else:
        for field, value in payload.model_dump().items():
            setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile
