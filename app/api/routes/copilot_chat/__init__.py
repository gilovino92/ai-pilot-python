from fastapi import APIRouter
from .chat import router as chat_router

router = APIRouter(
    prefix="/copilot-chat",
    tags=["copilot-chat"],
    responses={404: {"description": "Not found"}},
)
router.include_router(chat_router)

__all__ = ["router"]