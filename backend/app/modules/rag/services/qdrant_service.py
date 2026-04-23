from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID, uuid4

from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient, models

from app.core.config import settings
from app.modules.rag.exceptions import QdrantOperationError

logger = logging.getLogger(__name__)

_EMBED_BATCH = 100


@dataclass
class RetrievedChunk:

    text: str
    score: float
    document_id: Optional[str]
    chunk_index: Optional[int]
    metadata: dict[str, Any]


class QdrantService:
    def __init__(self) -> None:
        self._client: Optional[AsyncQdrantClient] = None
        self._openai: Optional[AsyncOpenAI] = None
        self._collection = settings.RAG_COLLECTION_NAME
        self._dim = settings.RAG_EMBEDDING_DIMENSION
        self._embed_model = settings.OPEN_EMBEDDING_MODEL

    @property
    def collection_name(self) -> str:
        return self._collection

    async def initialize(self) -> None:
        try:
            self._client = AsyncQdrantClient(url=settings.QDRANT)
            self._openai = AsyncOpenAI(api_key=settings.OPEN_API_KEY)
            await self._ensure_collection()
        except Exception as exc:
            logger.warning("Qdrant init failed: %s", exc)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def _ensure_collection(self) -> None:
        assert self._client is not None
        if await self._client.collection_exists(self._collection):
            info = await self._client.get_collection(self._collection)
            vectors_cfg = info.config.params.vectors
            is_unnamed = isinstance(vectors_cfg, models.VectorParams)
            size_ok = is_unnamed and vectors_cfg.size == self._dim
            if size_ok:
                return
            await self._client.delete_collection(self._collection)

        await self._client.create_collection(
            collection_name=self._collection,
            vectors_config=models.VectorParams(size=self._dim, distance=models.Distance.COSINE),
        )
        await self._client.create_payload_index(
            collection_name=self._collection,
            field_name="document_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    # ── Embedding ─────────────────────────────────────────
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._openai is None:
            self._openai = AsyncOpenAI(api_key=settings.OPEN_API_KEY)

        vectors: list[list[float]] = []
        for i in range(0, len(texts), _EMBED_BATCH):
            batch = texts[i : i + _EMBED_BATCH]
            resp = await self._openai.embeddings.create(
                model=self._embed_model, input=batch
            )
            vectors.extend(d.embedding for d in resp.data)
        return vectors

    # ── Write ─────────────────────────────────────────────
    async def upsert_chunks(
        self,
        *,
        document_id: UUID,
        embed_texts: list[str],
        original_chunks: list[str],
        doc_metadata: Optional[dict[str, Any]] = None,
    ) -> int:
        """Embed + upsert. Returns số points đã upsert."""
        if self._client is None:
            raise QdrantOperationError("Qdrant client chưa init")
        if len(embed_texts) != len(original_chunks):
            raise QdrantOperationError("embed_texts và original_chunks phải cùng length")
        if not embed_texts:
            return 0

        vectors = await self.embed_texts(embed_texts)
        base_meta = dict(doc_metadata or {})
        points: list[models.PointStruct] = []
        for idx, (vec, orig) in enumerate(zip(vectors, original_chunks)):
            payload = {
                "document_id": str(document_id),
                "chunk_index": idx,
                "text": orig,
                **base_meta,
            }
            points.append(
                models.PointStruct(id=str(uuid4()), vector=vec, payload=payload)
            )

        try:
            await self._client.upsert(
                collection_name=self._collection, points=points, wait=True
            )
        except Exception as exc:
            raise QdrantOperationError(f"Upsert failed: {exc}") from exc
        return len(points)

    # ── Delete ────────────────────────────────────────────
    async def delete_by_document_id(self, document_id: UUID) -> int:
        if self._client is None:
            raise QdrantOperationError("Qdrant client chưa init")

        flt = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=str(document_id)),
                )
            ]
        )
        try:
            # Count trước để báo về FE
            count = (
                await self._client.count(
                    collection_name=self._collection, count_filter=flt
                )
            ).count
            await self._client.delete(
                collection_name=self._collection,
                points_selector=models.FilterSelector(filter=flt),
                wait=True,
            )
            return int(count)
        except Exception as exc:
            raise QdrantOperationError(f"Delete failed: {exc}") from exc

    # ── Read ──────────────────────────────────────────────
    async def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
    ) -> list[RetrievedChunk]:
        if self._client is None:
            raise QdrantOperationError("Qdrant client chưa init")
        vectors = await self.embed_texts([query])
        resp = await self._client.query_points(
            collection_name=self._collection,
            query=vectors[0],
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True,
        )
        out: list[RetrievedChunk] = []
        for pt in resp.points:
            payload = pt.payload or {}
            out.append(
                RetrievedChunk(
                    text=str(payload.get("text", "")),
                    score=float(pt.score),
                    document_id=payload.get("document_id"),
                    chunk_index=payload.get("chunk_index"),
                    metadata={
                        k: v
                        for k, v in payload.items()
                        if k not in {"text", "document_id", "chunk_index"}
                    },
                )
            )
        return out

    async def hybrid_search(
        self, query: str, top_k: int = 5
    ) -> list[RetrievedChunk]:
        """Alias giữ backward-compat — hiện dense-only."""
        return await self.search(query=query, top_k=top_k)

    async def count_points(self) -> int:
        if self._client is None:
            return 0
        try:
            resp = await self._client.count(collection_name=self._collection)
            return int(resp.count)
        except Exception:
            return 0

    async def ping(self) -> bool:
        if self._client is None:
            return False
        try:
            await self._client.get_collections()
            return True
        except Exception:
            return False


qdrant_service = QdrantService()
