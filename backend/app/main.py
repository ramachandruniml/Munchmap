from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import grocery_lists, health, meal_plans, pantry, profile
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Munchmap API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(meal_plans.router, prefix="/api")
app.include_router(grocery_lists.router, prefix="/api")
app.include_router(pantry.router, prefix="/api")
