from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient, AsyncQdrantClient  
from qdrant_client.http import models as rest
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings
from app.modules.rag.exceptions import (
    QdrantCollectionError,
    QdrantDeleteError,
    QdrantSearchError,
    QdrantUpsertError,
    RAGServiceNotInitializedError,
)

logger = logging.getLogger(__name__)

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"
DENSE_VECTOR_DIM = settings.RAG_EMBEDDING_DIMENSION

_LANGCHAIN_DENSE_VECTOR_KEY = DENSE_VECTOR_NAME
_LANGCHAIN_SPARSE_VECTOR_KEY = SPARSE_VECTOR_NAME


@dataclass
class RetrievedChunk:
    """A chunk returned from hybrid search."""

    point_id: str
    document_id: str
    chunk_index: int
    file_type: str
    content: str
    context: str
    score: float
    metadata: dict[str, Any]

    @classmethod
    def from_langchain_document(
        cls, doc: Document, score: float
    ) -> "RetrievedChunk":
        meta = doc.metadata or {}
        return cls(
            point_id=str(meta.get("_id", "")),
            document_id=str(meta.get("document_id", "")),
            chunk_index=int(meta.get("chunk_index", 0)),
            file_type=str(meta.get("file_type", "")),
            content=doc.page_content,
            context=str(meta.get("context", "")),
            score=score,
            metadata=meta,
        )


@dataclass
class ChunkInput:
    """A chunk to be indexed into Qdrant."""

    document_id: str
    chunk_index: int
    file_type: str
    content: str
    context: str


class QdrantService:

    def __init__(self) -> None:
        self._collection_name: str = settings.RAG_COLLECTION_NAME
        self._qdrant_url: str = settings.QDRANT
        self._openai_api_key: str = settings.OPEN_API_KEY
        self._score_threshold: float = settings.RAG_SCORE_THRESHOLD

        self._sync_client: QdrantClient | None = None
        self._client: AsyncQdrantClient | None = None
        self._dense_embedder: OpenAIEmbeddings | None = None
        self._sparse_embedder: FastEmbedSparse | None = None
        self._vector_store: QdrantVectorStore | None = None
        self._initialized: bool = False

    async def initialize(self) -> None:
        if self._initialized:
            logger.debug("[QdrantService] Already initialized, skipping.")
            return

        logger.info("[QdrantService] Initializing...")

        self._client = AsyncQdrantClient(url=self._qdrant_url)
        self._sync_client = QdrantClient(url=self._qdrant_url)

        self._dense_embedder = OpenAIEmbeddings(
            model="text-embedding-3-large",
            dimensions=DENSE_VECTOR_DIM,
            api_key=self._openai_api_key,  # type: ignore[arg-type]
        )

        self._sparse_embedder = FastEmbedSparse(model_name="Qdrant/bm25")

        await self._ensure_collection()

        self._vector_store = QdrantVectorStore(
            client=self._sync_client,
            collection_name=self._collection_name,
            embedding=self._dense_embedder,
            sparse_embedding=self._sparse_embedder,
            retrieval_mode=RetrievalMode.HYBRID,
            vector_name=_LANGCHAIN_DENSE_VECTOR_KEY,
            sparse_vector_name=_LANGCHAIN_SPARSE_VECTOR_KEY,
        )

        self._initialized = True
        logger.info(
            "[QdrantService] Initialized successfully. Collection: %s",
            self._collection_name,
        )

    async def close(self) -> None:
        if self._sync_client:
            self._sync_client.close()
        if self._client:
            await self._client.close()
            logger.info("[QdrantService] Qdrant connection closed.")
        self._initialized = False

    async def create_collection(self, recreate: bool = False) -> None:
        self._check_initialized()
        assert self._client is not None

        try:
            exists = await self._collection_exists()

            if exists and recreate:
                logger.warning(
                    "[QdrantService] Deleting collection '%s' to recreate.",
                    self._collection_name,
                )
                await self._client.delete_collection(self._collection_name)
                exists = False

            if exists:
                logger.info(
                    "[QdrantService] Collection '%s' already exists, skipping creation.",
                    self._collection_name,
                )
                return

            await self._create_collection_with_named_vectors()
            logger.info(
                "[QdrantService] Created collection '%s'.", self._collection_name
            )

        except (QdrantCollectionError, RAGServiceNotInitializedError):
            raise
        except Exception as exc:
            raise QdrantCollectionError(
                message=f"Cannot create Qdrant collection '{self._collection_name}'",
                details={"error": str(exc), "collection": self._collection_name},
            ) from exc

    async def upsert_documents(self, chunks: list[ChunkInput]) -> int:
        self._check_initialized()
        assert self._vector_store is not None

        if not chunks:
            logger.debug("[QdrantService] upsert_documents called with empty list, skipping.")
            return 0

        try:
            documents = [self._chunk_to_langchain_document(c) for c in chunks]
            point_ids = await self._vector_store.aadd_documents(documents)

            logger.info(
                "[QdrantService] Upserted %d chunks (sample document_id: %s).",
                len(point_ids),
                chunks[0].document_id if chunks else "N/A",
            )
            return len(point_ids)

        except (QdrantUpsertError, RAGServiceNotInitializedError):
            raise
        except Exception as exc:
            raise QdrantUpsertError(
                message="Failed to upsert chunks into Qdrant",
                details={
                    "error": str(exc),
                    "chunk_count": len(chunks),
                    "document_id": chunks[0].document_id if chunks else None,
                },
            ) from exc

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        self._check_initialized()
        assert self._vector_store is not None

        if not query or not query.strip():
            raise QdrantSearchError(
                message="Query cannot be empty",
                details={"query": query},
            )

        threshold = score_threshold if score_threshold is not None else self._score_threshold

        try:
            qdrant_filter = self._build_qdrant_filter(filters)
            results: list[tuple[Document, float]] = (
                await self._vector_store.asimilarity_search_with_relevance_scores(
                    query=query,
                    k=top_k,
                    filter=qdrant_filter,
                    score_threshold=threshold,
                )
            )

            retrieved = [
                RetrievedChunk.from_langchain_document(doc, score)
                for doc, score in results
            ]

            logger.info(
                "[QdrantService] Hybrid search '%s...' → %d results (top_k=%d, threshold=%.2f).",
                query[:50],
                len(retrieved),
                top_k,
                threshold,
            )
            return retrieved

        except (QdrantSearchError, RAGServiceNotInitializedError):
            raise
        except Exception as exc:
            raise QdrantSearchError(
                message="Hybrid search failed",
                details={
                    "error": str(exc),
                    "query_preview": query[:100],
                    "filters": filters,
                    "top_k": top_k,
                },
            ) from exc

    async def delete_by_document_id(self, document_id: str) -> int:
        self._check_initialized()
        assert self._client is not None

        if not document_id or not document_id.strip():
            raise QdrantDeleteError(
                message="document_id cannot be empty",
                details={"document_id": document_id},
            )

        try:
            count_before = await self._count_points_by_document_id(document_id)

            if count_before == 0:
                logger.info(
                    "[QdrantService] No points found for document_id='%s'.",
                    document_id,
                )
                return 0

            await self._client.delete(
                collection_name=self._collection_name,
                points_selector=rest.FilterSelector(
                    filter=rest.Filter(
                        must=[
                            rest.FieldCondition(
                                key="metadata.document_id",
                                match=rest.MatchValue(value=document_id),
                            )
                        ]
                    )
                ),
            )

            logger.info(
                "[QdrantService] Deleted %d points for document_id='%s'.",
                count_before,
                document_id,
            )
            return count_before

        except (QdrantDeleteError, RAGServiceNotInitializedError):
            raise
        except Exception as exc:
            raise QdrantDeleteError(
                message=f"Cannot delete points for document '{document_id}'",
                details={"error": str(exc), "document_id": document_id},
            ) from exc

    async def get_collection_info(self) -> dict[str, Any]:
        self._check_initialized()
        assert self._client is not None

        try:
            info = await self._client.get_collection(self._collection_name)
            return {
                "collection_name": self._collection_name,
                "points_count": info.points_count,
                "status": info.status.value if info.status else "unknown",
                "vectors_count": getattr(info, "indexed_vectors_count", None),
                "indexed_vectors_count": info.indexed_vectors_count,
            }
        except Exception as exc:
            raise QdrantCollectionError(
                message="Cannot retrieve collection info",
                details={"error": str(exc), "collection": self._collection_name},
            ) from exc

    def _check_initialized(self) -> None:
        if not self._initialized:
            raise RAGServiceNotInitializedError()

    async def _ensure_collection(self) -> None:
        exists = await self._collection_exists()
        if not exists:
            await self._create_collection_with_named_vectors()
            logger.info(
                "[QdrantService] Created new collection '%s'.",
                self._collection_name,
            )
        else:
            logger.info(
                "[QdrantService] Collection '%s' already exists.",
                self._collection_name,
            )

    async def _collection_exists(self) -> bool:
        assert self._client is not None
        try:
            await self._client.get_collection(self._collection_name)
            return True
        except UnexpectedResponse:
            return False
        except Exception:
            return False

    async def _create_collection_with_named_vectors(self) -> None:
        assert self._client is not None
        await self._client.create_collection(
            collection_name=self._collection_name,
            vectors_config={
                DENSE_VECTOR_NAME: rest.VectorParams(
                    size=DENSE_VECTOR_DIM,
                    distance=rest.Distance.COSINE,
                    hnsw_config=rest.HnswConfigDiff(
                        m=16,
                        ef_construct=100,
                    ),
                )
            },
            sparse_vectors_config={
                SPARSE_VECTOR_NAME: rest.SparseVectorParams(
                    index=rest.SparseIndexParams(
                        on_disk=False,
                    )
                )
            },
        )

        await self._client.create_payload_index(
            collection_name=self._collection_name,
            field_name="metadata.document_id",
            field_schema=rest.PayloadSchemaType.KEYWORD,
        )
        await self._client.create_payload_index(
            collection_name=self._collection_name,
            field_name="metadata.file_type",
            field_schema=rest.PayloadSchemaType.KEYWORD,
        )

    def _chunk_to_langchain_document(self, chunk: ChunkInput) -> Document:
        embed_text = f"{chunk.context}\n\n{chunk.content}" if chunk.context else chunk.content

        return Document(
            page_content=embed_text,
            metadata={
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "file_type": chunk.file_type,
                "content": chunk.content,
                "context": chunk.context,
            },
        )

    def _build_qdrant_filter(
        self, filters: dict[str, Any] | None
    ) -> rest.Filter | None:
        if not filters:
            return None

        conditions: list[rest.FieldCondition] = []

        for key in ("document_id", "file_type"):
            value = filters.get(key)
            if value is not None:
                conditions.append(
                    rest.FieldCondition(
                        key=f"metadata.{key}",
                        match=rest.MatchValue(value=str(value)),
                    )
                )

        if not conditions:
            return None

        return rest.Filter(must=conditions)

    async def _count_points_by_document_id(self, document_id: str) -> int:
        assert self._client is not None
        result = await self._client.count(
            collection_name=self._collection_name,
            count_filter=rest.Filter(
                must=[
                    rest.FieldCondition(
                        key="metadata.document_id",
                        match=rest.MatchValue(value=document_id),
                    )
                ]
            ),
            exact=True,
        )
        return result.count


qdrant_service = QdrantService()