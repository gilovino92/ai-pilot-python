from fastapi import APIRouter

router = APIRouter(
    prefix="/utils",
    tags=["utils"],
    responses={404: {"description": "Not found"}},
)

@router.get("/health-check/")
async def health_check() -> bool:
    return True 