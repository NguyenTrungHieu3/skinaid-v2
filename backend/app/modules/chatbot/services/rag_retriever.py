from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ChatRagRetriever:
    async def query(
        self,
        wound_type: str,
        severity: str,
        user_message: str,
    ) -> list[Any]:
        try:
            from app.modules.rag.services.qdrant_service import qdrant_service

            query = f"{wound_type} {severity} {user_message}"
            return await qdrant_service.hybrid_search(query=query, top_k=3)
        except Exception as exc:
            logger.warning(
                "[ChatRagRetriever] RAG search failed, continuing without RAG: %s",
                str(exc)[:200],
            )
            return []
