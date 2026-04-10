from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Final

from langchain_experimental.text_splitter import SemanticChunker  
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import RateLimitError

from app.core.config import settings
from app.modules.rag.exceptions import RAGIndexingError

logger = logging.getLogger(__name__)

_SEMANTIC_EMBEDDING_MODEL: Final[str] = "text-embedding-3-large"
_CONTEXT_LLM_MODEL: Final[str] = "gpt-4.1-mini"
_MAX_DOC_FOR_CONTEXT: Final[int] = 8_000
_MAX_CONCURRENT_LLM: Final[int] = 5
_MAX_RETRY: Final[int] = 3
_RETRY_BASE_DELAY: Final[float] = 1.0
_MIN_CHUNK_CHARS: Final[int] = 50
_MAX_CHUNK_CHARS: Final[int] = 4_000


@dataclass
class ChunkOutput:

    content: str
    context: str
    chunk_index: int


class ChunkingService:

    def __init__(
        self,
        max_concurrent_llm: int = _MAX_CONCURRENT_LLM,
        enable_contextual_retrieval: bool = True,
    ) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrent_llm)
        self._enable_contextual = enable_contextual_retrieval
        self._semantic_chunker: SemanticChunker | None = None
        self._context_llm: ChatOpenAI | None = None

    async def chunk(
        self,
        text: str,
        use_contextual: bool | None = None,
    ) -> list[ChunkOutput]:
        """Split text into semantic chunks with optional LLM context."""
        if not text or not text.strip():
            logger.debug("[ChunkingService] Empty text, skipping chunking.")
            return []

        should_contextualize = (
            use_contextual if use_contextual is not None else self._enable_contextual
        )

        try:
            raw_chunks = await self._semantic_chunk(text)

            if not raw_chunks:
                logger.warning("[ChunkingService] Semantic chunking returned 0 chunks.")
                return []

            logger.info(
                "[ChunkingService] Semantic chunking: %d chunks from %d chars.",
                len(raw_chunks),
                len(text),
            )

            if should_contextualize:
                chunks = await self._add_context_to_chunks(text, raw_chunks)
            else:
                chunks = [
                    ChunkOutput(content=c, context="", chunk_index=i)
                    for i, c in enumerate(raw_chunks)
                ]

            logger.info(
                "[ChunkingService] Chunking complete: %d chunks (contextual=%s).",
                len(chunks),
                should_contextualize,
            )
            return chunks

        except (RAGIndexingError,):
            raise
        except Exception as exc:
            raise RAGIndexingError(
                message="Chunking failed",
                details={"error": str(exc), "text_length": len(text)},
            ) from exc

    async def _semantic_chunk(self, text: str) -> list[str]:
        """Split text using SemanticChunker in a threadpool. Filters out too-short or too-long chunks."""
        chunker = self._get_semantic_chunker()

        import asyncio

        def _run_sync() -> list[str]:
            docs = chunker.create_documents([text])
            chunks = [doc.page_content for doc in docs if doc.page_content.strip()]

            result: list[str] = []
            for chunk in chunks:
                if len(chunk) < _MIN_CHUNK_CHARS:
                    logger.debug(
                        "[ChunkingService] Skipping chunk that is too short (%d chars).", len(chunk)
                    )
                    continue
                if len(chunk) > _MAX_CHUNK_CHARS:
                    sub_chunks = self._split_long_chunk(chunk)
                    result.extend(sub_chunks)
                else:
                    result.append(chunk)
            return result

        return await asyncio.get_event_loop().run_in_executor(None, _run_sync)

    def _split_long_chunk(self, text: str) -> list[str]:
        """Fallback splitter for oversized chunks: split by paragraph then by sentence."""
        paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]

        if all(len(p) <= _MAX_CHUNK_CHARS for p in paragraphs):
            return [p for p in paragraphs if len(p) >= _MIN_CHUNK_CHARS]

        result: list[str] = []
        current = ""
        sentences = re.split(r"(?<=[.!?])\s+", text)

        for sentence in sentences:
            if len(current) + len(sentence) <= _MAX_CHUNK_CHARS:
                current = (current + " " + sentence).strip()
            else:
                if len(current) >= _MIN_CHUNK_CHARS:
                    result.append(current)
                current = sentence

        if len(current) >= _MIN_CHUNK_CHARS:
            result.append(current)

        return result

    async def _add_context_to_chunks(
        self, full_document: str, raw_chunks: list[str]
    ) -> list[ChunkOutput]:
        """Call LLM concurrently to generate context for each chunk."""
        doc_preview = self._truncate_document_for_context(full_document)

        tasks = [
            self._generate_context_with_retry(
                doc_preview=doc_preview,
                chunk=chunk,
                chunk_index=i,
            )
            for i, chunk in enumerate(raw_chunks)
        ]

        context_results: list[str] = await asyncio.gather(*tasks)

        return [
            ChunkOutput(content=chunk, context=ctx, chunk_index=i)
            for i, (chunk, ctx) in enumerate(zip(raw_chunks, context_results))
        ]

    async def _generate_context_with_retry(
        self,
        doc_preview: str,
        chunk: str,
        chunk_index: int,
    ) -> str:
        """Generate context for a single chunk with retry and Semaphore throttling."""
        async with self._semaphore:
            last_exc: Exception | None = None

            for attempt in range(1, _MAX_RETRY + 1):
                try:
                    context = await self._call_context_llm(doc_preview, chunk)
                    return context

                except RateLimitError as exc:
                    last_exc = exc
                    if attempt == _MAX_RETRY:
                        break
                    delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        "[ChunkingService] Chunk %d: RateLimitError (attempt %d/%d). Waiting %.1fs...",
                        chunk_index,
                        attempt,
                        _MAX_RETRY,
                        delay,
                    )
                    await asyncio.sleep(delay)

                except Exception as exc:
                    logger.warning(
                        "[ChunkingService] Chunk %d: Cannot generate context (%s). Using empty context.",
                        chunk_index,
                        str(exc)[:100],
                    )
                    return ""

        logger.error(
            "[ChunkingService] Chunk %d: Exhausted %d retries (RateLimit). Using empty context.",
            chunk_index,
            _MAX_RETRY,
        )
        return ""

    async def _call_context_llm(self, doc_preview: str, chunk: str) -> str:
        """Call LLM to generate 1-2 sentence context for a chunk using Contextual Retrieval."""
        llm = self._get_context_llm()

        prompt = (
            f"Đây là một tài liệu y tế:\n"
            f"<document>\n{doc_preview}\n</document>\n\n"
            f"Đây là một đoạn trích từ tài liệu trên:\n"
            f"<chunk>\n{chunk}\n</chunk>\n\n"
            f"Hãy viết 1-2 câu ngắn gọn mô tả đoạn trích này nằm ở phần nào "
            f"của tài liệu và nội dung chính của nó là gì. "
            f"Chỉ trả lời bằng 1-2 câu, không giải thích thêm."
        )

        response = await llm.ainvoke(prompt)

        content = response.content
        if isinstance(content, list):
            content = " ".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )

        return str(content).strip()

    def _get_semantic_chunker(self) -> SemanticChunker:
        """Lazily create SemanticChunker on first use."""
        if self._semantic_chunker is None:
            embedder = OpenAIEmbeddings(
                model=_SEMANTIC_EMBEDDING_MODEL,
                dimensions=settings.RAG_EMBEDDING_DIMENSION,
                api_key=settings.OPEN_API_KEY,  # type: ignore[arg-type]
                max_retries=3,
            )
            self._semantic_chunker = SemanticChunker(
                embeddings=embedder,
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=95,
            )
            logger.info(
                "[ChunkingService] SemanticChunker initialized (model=%s, threshold=percentile/95).",
                _SEMANTIC_EMBEDDING_MODEL,
            )
        return self._semantic_chunker

    def _get_context_llm(self) -> ChatOpenAI:
        """Lazily create ChatOpenAI client on first use."""
        if self._context_llm is None:
            self._context_llm = ChatOpenAI(
                model=_CONTEXT_LLM_MODEL,
                temperature=0.1,
                max_completion_tokens=150,
                api_key=settings.OPEN_API_KEY,  # type: ignore[arg-type]
                max_retries=0,
            )
            logger.info(
                "[ChunkingService] Context LLM initialized (model=%s).",
                _CONTEXT_LLM_MODEL,
            )
        return self._context_llm

    def _truncate_document_for_context(self, document: str) -> str:
        """Truncate document to _MAX_DOC_FOR_CONTEXT chars, keeping 70% head + 30% tail."""
        if len(document) <= _MAX_DOC_FOR_CONTEXT:
            return document

        head_size = int(_MAX_DOC_FOR_CONTEXT * 0.7)
        tail_size = _MAX_DOC_FOR_CONTEXT - head_size

        head = document[:head_size]
        tail = document[-tail_size:]

        return f"{head}\n\n[... content truncated ...]\n\n{tail}"


chunking_service = ChunkingService()
