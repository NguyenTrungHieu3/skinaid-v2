from __future__ import annotations

import asyncio
import random
import re
from typing import Optional

from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI, RateLimitError

from app.core.config import settings

_CONTEXT_PROMPT = """<document>
{doc}
</document>

Here is the chunk we want to situate within the whole document:
<chunk>
{chunk}
</chunk>

Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else. Answer in the same language as the chunk."""

_CONTEXT_MAX_DOC_CHARS = 20_000
_CONTEXT_CONCURRENCY = 2
_MAX_RETRIES = 5
_DEFAULT_BACKOFF = 8.0


class ChunkingService:
    def __init__(
        self,
        *,
        context_model: str = "gpt-4.1-mini",
        breakpoint_threshold_type: str = "percentile",
        breakpoint_threshold_amount: float = 95.0,
    ) -> None:
        self._embeddings = OpenAIEmbeddings(
            model=settings.OPEN_EMBEDDING_MODEL,
            api_key=settings.OPEN_API_KEY,
        )
        self._splitter = SemanticChunker(
            embeddings=self._embeddings,
            breakpoint_threshold_type=breakpoint_threshold_type,
            breakpoint_threshold_amount=breakpoint_threshold_amount,
        )
        self._openai = AsyncOpenAI(api_key=settings.OPEN_API_KEY)
        self._context_model = context_model

    def semantic_split(self, text: str) -> list[str]:
        chunks = self._splitter.split_text(text)
        return [c.strip() for c in chunks if c and c.strip()]

    async def add_context(
        self, full_doc: str, chunks: list[str]
    ) -> list[str]:
        if not chunks:
            return []

        doc_for_prompt = (
            full_doc if len(full_doc) <= _CONTEXT_MAX_DOC_CHARS
            else full_doc[:_CONTEXT_MAX_DOC_CHARS] + "\n...[truncated]"
        )

        sem = asyncio.Semaphore(_CONTEXT_CONCURRENCY)

        async def _one(chunk: str) -> str:
            async with sem:
                ctx = await self._call_llm(doc_for_prompt, chunk)
                if not ctx:
                    return chunk
                return f"{ctx}\n\n{chunk}"

        return await asyncio.gather(*(_one(c) for c in chunks))

    async def _call_llm(self, doc: str, chunk: str) -> Optional[str]:
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._openai.chat.completions.create(
                    model=self._context_model,
                    temperature=0.0,
                    max_tokens=150,
                    messages=[
                        {"role": "user", "content": _CONTEXT_PROMPT.format(doc=doc, chunk=chunk)}
                    ],
                )
                return (resp.choices[0].message.content or "").strip()
            except RateLimitError as exc:
                wait = self._parse_retry_after(str(exc)) or (_DEFAULT_BACKOFF * (2 ** attempt))
                wait += random.uniform(0, 1)
                await asyncio.sleep(wait)
            except Exception:
                return None
        return None

    @staticmethod
    def _parse_retry_after(msg: str) -> Optional[float]:
        match = re.search(r"try again in ([\d.]+)s", msg)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
