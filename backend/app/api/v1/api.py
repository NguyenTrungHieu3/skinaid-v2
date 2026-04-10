from fastapi import APIRouter
from app.modules.auth.router import router as auth_router
from app.modules.users.profile_router import router as profile_router
from app.modules.ai.routes.ai_router import router as ai_router
from app.modules.ai.routes.model_management_router import router as model_management_router
from app.modules.firstaid.router import router as first_aid_router
from app.modules.guest.router import router as guest_router
from app.modules.audit.routes.dashboard_router import router as dashboard_router
from app.modules.audit.routes.audit_router import router as audit_router
from app.modules.users.router import router as users_router
from app.modules.map.router import router as map_router

from app.modules.chatbot.router import router as chatbot_router
from app.modules.rag.routes.rag_router import router as rag_router
from app.modules.llm.routes.llm_router import router as llm_router
from app.modules.questionnaires.router import router as questionnaires_router
from app.modules.notifications.router import router as notifications_router

router = APIRouter()

router.include_router(auth_router, tags=["Authentication"])
router.include_router(profile_router, tags=["User Profile Management"])
router.include_router(ai_router, tags=["AI Processing"])
router.include_router(model_management_router, tags=["AI Model Management"])
router.include_router(first_aid_router, tags=["First Aid Knowledge"])
router.include_router(guest_router, tags=["Guest Management"])
router.include_router(dashboard_router, tags=["Dashboard Analytics"])
router.include_router(audit_router, tags=["Audit Logs"])
router.include_router(users_router, tags=["User Management"])
router.include_router(map_router, tags=["Map"])
router.include_router(chatbot_router, tags=["Chatbot"])
router.include_router(rag_router, tags=["RAG - Knowledge Retrieval"])
router.include_router(llm_router, tags=["LLM - Response Synthesis"])
router.include_router(notifications_router, tags=["Notifications"])
router.include_router(questionnaires_router, prefix="/questionnaires", tags=["Questionnaires Management"])
