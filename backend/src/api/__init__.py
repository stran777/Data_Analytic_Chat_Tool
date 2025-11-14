"""
API router configuration.
"""
from fastapi import APIRouter

from .analytics import router as analytics_router
from .chat import router as chat_router
from .health import router as health_router
from .users import router as users_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(users_router)
api_router.include_router(analytics_router)

__all__ = [
    "api_router",
    "chat_router",
    "users_router",
    "analytics_router",
    "health_router"
]
