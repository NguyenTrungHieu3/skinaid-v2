from fastapi import APIRouter
from app.modules.auth.router import router as auth_router
from app.modules.profile.router import router as profile_router
from app.modules.ai.routes.ai_router import router as ai_router
from app.modules.firstaid.router import router as first_aid_router
from app.modules.guest.router import router as guest_router
from app.modules.audit.routes.dashboard_router import router as dashboard_router
from app.modules.users.routes.user_list_router import router as user_list_router
from app.modules.users.routes.user_ops_router import router as user_ops_router
from app.modules.map.router import router as map_router

router = APIRouter()

router.include_router(auth_router, tags=["Authentication"])
router.include_router(profile_router, tags=["User Profile Management"])
router.include_router(ai_router, tags=["AI Processing"])
router.include_router(first_aid_router, tags=["First Aid Knowledge"])
router.include_router(guest_router, tags=["Guest Management"])
router.include_router(dashboard_router, tags=["Dashboard Analytics"])
router.include_router(user_list_router, tags=["Admin - User Management"])
router.include_router(user_ops_router, tags=["Admin - User Management"])
router.include_router(map_router, tags=["Map"])
