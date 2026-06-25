from .health import router as health_router
from .players import router as players_router
from .profiles import router as profiles_router
from .reviews import router as reviews_router

__all__ = ["health_router", "players_router", "profiles_router", "reviews_router"]
