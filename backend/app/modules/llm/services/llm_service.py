from __future__ import annotations

import asyncio
import logging
from typing import Final

from openai import AsyncOpenAI, APIConnectionError, APITimeoutError, RateLimitError

from app.core.config import settings
from app.modules.llm.exceptions import (
    LLMInvalidResponseError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
)

logger = logging.getLogger(__name__)

_MAX_RETRY: Final[int] = 2
_RETRY_BASE_DELAY: Final[float] = 1.0  


class LLMService:
    """Async OpenAI wrapper với retry logic cho B5 synthesis."""

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        """Lazy-init AsyncOpenAI client."""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.OPEN_API_KEY,
                max_retries=0, 
                timeout=30.0,
            )
            logger.info(
                "[LLMService] AsyncOpenAI client khởi tạo (model=%s).",
                settings.LLM_MODEL,
            )
        return self._client

    async def call(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> tuple[str, int]:
        """Gọi OpenAI chat completion, retry tối đa 2 lần khi rate limit, trả về (content, tokens_used)."""
        _max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS
        _temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        client = self._get_client()

        total_prompt_chars = sum(len(m.get("content", "")) for m in messages)
        logger.info(
            "[LLMService] Calling LLM — model=%s, max_completion_tokens=%d, prompt_chars≈%d.",
            settings.LLM_MODEL,
            _max_tokens,
            total_prompt_chars,
        )

        last_exc: Exception | None = None

        for attempt in range(1, _MAX_RETRY + 2):  
            try:
                response = await client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=messages,  # type: ignore[arg-type]
                    max_completion_tokens=_max_tokens,
                    temperature=_temperature,
                    response_format={"type": "json_object"},
                )

                choice = response.choices[0] if response.choices else None
                finish_reason = choice.finish_reason if choice else "no_choice"

                content = (
                    choice.message.content
                    if choice and choice.message.content
                    else ""
                )
                content = content.strip()

                if not content:
                    logger.error(
                        "[LLMService] Content rỗng — finish_reason=%s, refusal=%s, choices_count=%d.",
                        finish_reason,
                        getattr(choice.message, "refusal", None) if choice else None,
                        len(response.choices),
                    )
                    raise LLMInvalidResponseError(
                        message="LLM trả về nội dung rỗng",
                        details={
                            "model": settings.LLM_MODEL,
                            "attempt": attempt,
                            "finish_reason": finish_reason,
                        },
                    )

                tokens_used = (
                    response.usage.total_tokens if response.usage else 0
                )

                logger.info(
                    "[LLMService] Synthesis thành công (model=%s, tokens=%d, attempt=%d).",
                    settings.LLM_MODEL,
                    tokens_used,
                    attempt,
                )

                return content, tokens_used

            except RateLimitError as exc:
                last_exc = exc
                if attempt > _MAX_RETRY:
                    break
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))  # 1s, 2s
                logger.warning(
                    "[LLMService] RateLimitError (lần %d/%d). Chờ %.1fs...",
                    attempt,
                    _MAX_RETRY,
                    delay,
                )
                await asyncio.sleep(delay)

            except (APIConnectionError, APITimeoutError) as exc:
                raise LLMServiceUnavailableError(
                    message="Không thể kết nối đến OpenAI API",
                    details={"error": str(exc)[:200], "model": settings.LLM_MODEL},
                ) from exc

            except (LLMInvalidResponseError,):
                raise

            except Exception as exc:
                raise LLMServiceUnavailableError(
                    message="Lỗi không xác định khi gọi OpenAI API",
                    details={"error": str(exc)[:200], "model": settings.LLM_MODEL},
                ) from exc

        logger.error(
            "[LLMService] Hết %d retry do RateLimitError. Model=%s.",
            _MAX_RETRY,
            settings.LLM_MODEL,
        )
        raise LLMRateLimitError(
            details={"model": settings.LLM_MODEL, "retries": _MAX_RETRY},
        ) from last_exc
