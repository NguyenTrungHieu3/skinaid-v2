from fastapi import APIRouter
from app.modules.chatbot.routes.chat_router import router as chat_router

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

router.include_router(chat_router)
