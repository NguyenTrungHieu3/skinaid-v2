from fastapi import APIRouter
from app.modules.auth.routes.auth_router import router as auth_router
from app.modules.profile.routes.profile_router import router as profile_router
from app.modules.ai.routes.ai_router import router as ai_router
from app.modules.firstaid.routes.first_aid_router import router as first_aid_router
from app.modules.guest.routes.guest_router import router as guest_router
from app.modules.admin.routes.admin_router import router as admin_router
from app.modules.admin.routes.user_management_router import router as user_management_router
from app.modules.admin.routes.cleanup import router as cleanup_router
from app.modules.audit.routes.audit_router import router as audit_router
router = APIRouter()

router.include_router(auth_router, tags=["Authentication"])
router.include_router(profile_router, tags=["User Profile Management"])
router.include_router(ai_router, tags=["AI Processing"])
router.include_router(first_aid_router, tags=["First Aid Knowledge"])
router.include_router(guest_router, tags=["Guest Management"])
router.include_router(admin_router, tags=["Admin Dashboard"])
router.include_router(user_management_router, tags=["Admin - User Management"])
router.include_router(cleanup_router,tags=["Admin - Cleanup"])
router.include_router(audit_router, tags=["Audit"])
