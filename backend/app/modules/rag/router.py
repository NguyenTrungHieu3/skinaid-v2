from fastapi import APIRouter
from app.modules.rag.routes.rag_router import router as rag_router

router = APIRouter(prefix="/rag", tags=["RAG"])

router.include_router(rag_router)
