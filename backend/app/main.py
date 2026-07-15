from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import dining, grocery_lists, health, meal_plans, pantry, profile, recipes
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

Instrumentator().instrument(app).expose(app)

app.include_router(health.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(meal_plans.router, prefix="/api")
app.include_router(grocery_lists.router, prefix="/api")
app.include_router(pantry.router, prefix="/api")
app.include_router(recipes.router, prefix="/api")
app.include_router(dining.router, prefix="/api")
