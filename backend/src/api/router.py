from fastapi import APIRouter

from src.api.routes.public import router as public_router
from src.api.routes.student import router as student_router
from src.api.routes.admin import router as admin_router
from src.api.routes.shared import router as shared_router

router = APIRouter()
router.include_router(public_router)
router.include_router(student_router)
router.include_router(admin_router)
router.include_router(shared_router)
