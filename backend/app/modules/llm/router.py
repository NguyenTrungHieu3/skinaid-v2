from fastapi import APIRouter
from app.modules.llm.routes.llm_router import router as llm_router

router = APIRouter(prefix="/llm", tags=["LLM"])

router.include_router(llm_router)
