from arq import cron
from arq.connections import RedisSettings

from app.core.config import get_settings

settings = get_settings()


async def solve_meal_plan(ctx: dict, user_id: str) -> dict:
    """Placeholder job: runs the OR-Tools solver for a user's weekly plan."""
    return {"user_id": user_id, "status": "not_implemented"}


async def scrape_dining_menus(ctx: dict) -> None:
    """Placeholder scheduled job: pulls and parses campus dining hall menus."""


class WorkerSettings:
    functions = [solve_meal_plan]
    cron_jobs = [cron(scrape_dining_menus, hour=4, minute=0)]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
