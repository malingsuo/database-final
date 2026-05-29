from fastapi import APIRouter

from src.api.routes.checker import router as checker_router

router = APIRouter()
router.include_router(checker_router)
