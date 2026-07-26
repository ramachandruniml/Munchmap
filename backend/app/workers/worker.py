from arq.connections import RedisSettings

from app.core.config import get_settings

settings = get_settings()


async def solve_meal_plan(ctx: dict, user_id: str) -> dict:
    """Placeholder job: runs the OR-Tools solver for a user's weekly plan."""
    return {"user_id": user_id, "status": "not_implemented"}


class WorkerSettings:
    functions = [solve_meal_plan]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
