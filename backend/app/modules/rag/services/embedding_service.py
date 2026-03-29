from __future__ import annotations

import asyncio
import logging
from typing import Final

import tiktoken
from langchain_openai import OpenAIEmbeddings
from openai import RateLimitError

from app.core.config import settings
from app.modules.rag.exceptions import QdrantSearchError, RAGIndexingError

logger = logging.getLogger(__name__)

EMBEDDING_MODEL: Final[str] = settings.OPEN_EMBEDDING_MODEL
EMBEDDING_DIM: Final[int] = settings.RAG_EMBEDDING_DIMENSION

MAX_TOKENS_PER_TEXT: Final[int] = 8191
DEFAULT_BATCH_SIZE: Final[int] = 100
DEFAULT_MAX_CONCURRENT_BATCHES: Final[int] = 5
_MAX_RETRY_ATTEMPTS: Final[int] = 3
_RETRY_BASE_DELAY_SECONDS: Final[float] = 1.0


class EmbeddingService:

    def __init__(
        self,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_concurrent_batches: int = DEFAULT_MAX_CONCURRENT_BATCHES,
    ) -> None:
        if not (1 <= batch_size <= 2048):
            raise ValueError(f"batch_size phải trong khoảng [1, 2048], nhận: {batch_size}")
        if max_concurrent_batches < 1:
            raise ValueError(f"max_concurrent_batches phải >= 1, nhận: {max_concurrent_batches}")

        self._batch_size = batch_size
        self._semaphore = asyncio.Semaphore(max_concurrent_batches)

        self._embedder = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIM,
            api_key=settings.OPEN_API_KEY,  # type: ignore[arg-type]
            max_retries=0,
        )

        self._tokenizer = tiktoken.get_encoding("cl100k_base")

        logger.info(
            "[EmbeddingService] Khởi tạo với model=%s, dim=%d, batch_size=%d, max_concurrent=%d",
            EMBEDDING_MODEL,
            EMBEDDING_DIM,
            self._batch_size,
            max_concurrent_batches,
        )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed danh sách văn bản thành dense vectors (batch + parallel).
        """
        if not texts:
            return []

        safe_texts = [self._truncate_if_needed(text, idx) for idx, text in enumerate(texts)]
        batches = self._split_into_batches(safe_texts)

        logger.info(
            "[EmbeddingService] embed_texts: %d texts → %d batches (batch_size=%d)",
            len(safe_texts),
            len(batches),
            self._batch_size,
        )

        try:
            batch_results: list[list[list[float]]] = await asyncio.gather(
                *[self._embed_batch_with_retry(batch, batch_idx=i) for i, batch in enumerate(batches)]
            )
        except Exception as exc:
            raise RAGIndexingError(
                message="Embedding texts thất bại",
                details={
                    "error": str(exc),
                    "text_count": len(texts),
                    "model": EMBEDDING_MODEL,
                },
            ) from exc

        all_vectors: list[list[float]] = [
            vector
            for batch_vectors in batch_results
            for vector in batch_vectors
        ]

        logger.info(
            "[EmbeddingService] embed_texts hoàn thành: %d vectors (dim=%d)",
            len(all_vectors),
            EMBEDDING_DIM,
        )
        return all_vectors

    async def embed_query(self, query: str) -> list[float]:
        """
        Embed một câu truy vấn đơn (dùng aembed_query cho asymmetric embedding).
        """
        if not query or not query.strip():
            raise QdrantSearchError(
                message="Query không được rỗng khi embed",
                details={"query": query},
            )

        safe_query = self._truncate_if_needed(query.strip(), text_idx=0)

        try:
            vector = await self._embed_query_with_retry(safe_query)
        except (QdrantSearchError, RAGIndexingError):
            raise
        except Exception as exc:
            raise QdrantSearchError(
                message="Embedding query thất bại",
                details={
                    "error": str(exc),
                    "query_preview": query[:100],
                    "model": EMBEDDING_MODEL,
                },
            ) from exc

        return vector

    @property
    def model(self) -> str:
        """Tên model đang dùng."""
        return EMBEDDING_MODEL

    @property
    def dimension(self) -> int:
        """Số chiều của vector output."""
        return EMBEDDING_DIM

    def _split_into_batches(self, texts: list[str]) -> list[list[str]]:
        """Chia list texts thành batches kích thước batch_size."""
        return [
            texts[start : start + self._batch_size]
            for start in range(0, len(texts), self._batch_size)
        ]

    async def _embed_batch_with_retry(
        self, batch: list[str], batch_idx: int = 0
    ) -> list[list[float]]:
        """Embed một batch với Semaphore + exponential backoff retry (RateLimitError)."""
        async with self._semaphore:
            last_exc: Exception | None = None

            for attempt in range(1, _MAX_RETRY_ATTEMPTS + 1):
                try:
                    vectors = await self._embedder.aembed_documents(batch)

                    if attempt > 1:
                        logger.info(
                            "[EmbeddingService] Batch %d thành công ở lần thử %d.",
                            batch_idx,
                            attempt,
                        )
                    return vectors

                except RateLimitError as exc:
                    last_exc = exc
                    if attempt == _MAX_RETRY_ATTEMPTS:
                        logger.error(
                            "[EmbeddingService] Batch %d thất bại sau %d lần retry (RateLimit).",
                            batch_idx,
                            _MAX_RETRY_ATTEMPTS,
                        )
                        break

                    delay = _RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                    logger.warning(
                        "[EmbeddingService] Batch %d gặp RateLimitError (lần %d/%d). Chờ %.1fs...",
                        batch_idx,
                        attempt,
                        _MAX_RETRY_ATTEMPTS,
                        delay,
                    )
                    await asyncio.sleep(delay)

                except Exception as exc:
                    logger.error(
                        "[EmbeddingService] Batch %d gặp lỗi không retry được: %s",
                        batch_idx,
                        str(exc),
                    )
                    raise

            raise RAGIndexingError(
                message=f"Embedding batch {batch_idx} thất bại sau {_MAX_RETRY_ATTEMPTS} lần retry",
                details={
                    "batch_idx": batch_idx,
                    "batch_size": len(batch),
                    "error": str(last_exc),
                },
            ) from last_exc

    async def _embed_query_with_retry(self, query: str) -> list[float]:
        """Embed single query với retry exponential backoff."""
        last_exc: Exception | None = None

        for attempt in range(1, _MAX_RETRY_ATTEMPTS + 1):
            try:
                vector: list[float] = await self._embedder.aembed_query(query)
                return vector

            except RateLimitError as exc:
                last_exc = exc
                if attempt == _MAX_RETRY_ATTEMPTS:
                    break

                delay = _RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    "[EmbeddingService] embed_query gặp RateLimitError (lần %d/%d). Chờ %.1fs...",
                    attempt,
                    _MAX_RETRY_ATTEMPTS,
                    delay,
                )
                await asyncio.sleep(delay)

            except Exception:
                raise

        raise QdrantSearchError(
            message="Embedding query thất bại sau tất cả retry",
            details={"error": str(last_exc), "query_preview": query[:100]},
        ) from last_exc

    def _truncate_if_needed(self, text: str, text_idx: int = 0) -> str:
        """Truncate text xuống MAX_TOKENS_PER_TEXT nếu vượt giới hạn."""
        tokens = self._tokenizer.encode(text)

        if len(tokens) <= MAX_TOKENS_PER_TEXT:
            return text

        logger.warning(
            "[EmbeddingService] Text[%d] có %d tokens > giới hạn %d. Đang truncate.",
            text_idx,
            len(tokens),
            MAX_TOKENS_PER_TEXT,
        )

        truncated_tokens = tokens[:MAX_TOKENS_PER_TEXT]
        return self._tokenizer.decode(truncated_tokens)

    def count_tokens(self, text: str) -> int:
        """Đếm số token của một text theo encoding cl100k_base."""
        return len(self._tokenizer.encode(text))


embedding_service = EmbeddingService()
