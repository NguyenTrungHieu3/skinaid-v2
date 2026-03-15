from fastapi import APIRouter, Depends
from app.modules.rag.services.stub_service import RAGStubService
from app.modules.rag.schemas.rag_schemas import (
    RAGRetrieveRequest,
    RAGRetrieveResponse,
)
from app.shared.response import SuccessResponse

router = APIRouter(tags=["RAG - Knowledge Retrieval"])


@router.post(
    "/retrieve",
    response_model=SuccessResponse[RAGRetrieveResponse],
    summary="Retrieve knowledge chunks (PBI-24)",
    description="Retrieve relevant knowledge chunks from the knowledge base. **Stub:** Returns empty chunks until real RAG is implemented.",
)
async def retrieve_knowledge(
    request: RAGRetrieveRequest,
    stub_service: RAGStubService = Depends(),
) -> SuccessResponse:
    """
    Retrieve relevant knowledge chunks from the knowledge base.
    
    **Stub:** Returns empty chunks until real RAG is implemented.
    """
    result = await stub_service.retrieve(request.query, request.top_k)
    
    return SuccessResponse(
        message="Truy xuất tri thức thành công",
        data=result,
    )
