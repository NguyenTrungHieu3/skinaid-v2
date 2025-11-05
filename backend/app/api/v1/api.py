from fastapi import APIRouter
from app.modules.auth.routes.auth_router import router as auth_router
from app.modules.profile.routes.profile_router import router as profile_router
from app.modules.upload.routes.upload_router import router as upload_router
from app.modules.ai.routes.ai_router import router as ai_router
from app.modules.firstaid.routes.first_aid_router import router as first_aid_router
from app.modules.guest.routes.guest_router import router as guest_router

router = APIRouter()

router.include_router(auth_router, tags=["Authentication"])
router.include_router(profile_router, tags=["User Profile Management"])
router.include_router(upload_router, tags=["Upload Logs"])
router.include_router(ai_router, tags=["AI Processing"])
router.include_router(first_aid_router, tags=["First Aid Knowledge"])
router.include_router(guest_router, tags=["Guest Management"])