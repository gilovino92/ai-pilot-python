from fastapi import APIRouter

from app.api.routes.utils import router as utils_router
from app.api.routes.copilot_chat import router as copilot_chat_router


api_router = APIRouter()

# Include all routers
api_router.include_router(utils_router)
api_router.include_router(copilot_chat_router)
__all__ = ["api_router"]