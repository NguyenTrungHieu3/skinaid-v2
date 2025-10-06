from fastapi import APIRouter
from app.modules.auth.routes.auth_routers import router as auth_router
from app.modules.profile.routes.profile_routers import router as profile_router
from app.modules.upload.routes.upload_routers import router as upload_router
from app.modules.ai.routes.ai_router import router as ai_router
from app.modules.firstaid.routes.first_aid_router import router as first_aid_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(profile_router)
router.include_router(upload_router)
router.include_router(ai_router)
router.include_router(first_aid_router)