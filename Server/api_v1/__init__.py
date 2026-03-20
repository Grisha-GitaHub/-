
from fastapi import APIRouter

from .dialogs.views import router as dialogs_router
from .users.views import router as users_router
from .auth.jwt_auth import router as auth_router
from .tests.views import router as tests_router

router = APIRouter()
router.include_router(router=dialogs_router, prefix="/dialogs")
router.include_router(router=users_router, prefix="/users")
router.include_router(router=auth_router, prefix="/auth")
router.include_router(router=tests_router, prefix="/tests")