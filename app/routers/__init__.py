"""API routers for HTTP request handling."""

from app.routers.auth import router as auth_router
from app.routers.drivers import router as drivers_router
from app.routers.users import router as users_router
from app.routers.vehicles import router as vehicles_router

__all__ = [
    "auth_router",
    "users_router",
    "drivers_router",
    "vehicles_router",
]
