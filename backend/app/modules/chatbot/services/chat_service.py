from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from uuid import UUID, uuid4

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.chatbot.exceptions import (
    ChatAnalysisNotFoundError,
    ChatLLMError,
    ChatMessageLimitError,
    ChatSessionNotFoundError,
)
from app.modules.chatbot.models.chat_messages import ChatMessage
from app.modules.chatbot.models.chat_sessions import ChatSession
from app.modules.chatbot.repository.chat_repository import ChatRepository
from app.modules.chatbot.schemas.chat_schemas import (
    ChatMessageResponse,
    CreateSessionResponse,
    MessageItem,
)
from app.modules.chatbot.services.chat_prompt_builder import ChatPromptBuilder
from app.modules.chatbot.services.rag_retriever import ChatRagRetriever
from app.modules.chatbot.services.redis_session_store import ChatRedisSessionStore
from app.modules.chatbot.services.wound_context_loader import WoundContextLoader
from app.modules.llm.services.config_resolver import resolve_llm_config
from app.modules.llm.services.llm_service import LLMService

logger = logging.getLogger(__name__)

_MAX_MESSAGES = settings.CHATBOT_MAX_MESSAGES


class ChatService:
    def __init__(
        self,
        db: AsyncSession,
        redis: aioredis.Redis,
        llm_service: LLMService,
        prompt_builder: ChatPromptBuilder,
    ) -> None:
        self._db = db
        self._redis_store = ChatRedisSessionStore(redis)
        self._wound_context = WoundContextLoader(db)
        self._rag = ChatRagRetriever()
        self._llm = llm_service
        self._pb = prompt_builder
        self._repo = ChatRepository(db)

    async def create_session(
        self,
        user_id: UUID,
        analysis_id: UUID | None,
    ) -> CreateSessionResponse:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if analysis_id:
            return await self._create_wound_advisor_session(user_id, analysis_id, now)
        return await self._create_app_guide_session(user_id, now)

    async def send_message(
        self,
        user_id: UUID,
        session_id: UUID,
        message: str,
    ) -> ChatMessageResponse:
        start_ms = time.monotonic()

        db_session = await self._repo.get_session(session_id, user_id)
        if db_session:
            return await self._reply_wound_advisor(
                db_session,
                session_id,
                message,
                start_ms,
            )

        redis_meta = await self._redis_store.get_session(session_id, user_id)
        if redis_meta:
            return await self._reply_app_guide(
                redis_meta,
                session_id,
                message,
                start_ms,
            )

        raise ChatSessionNotFoundError(details={"session_id": str(session_id)})

    async def _reply_wound_advisor(
        self,
        db_session: ChatSession,
        session_id: UUID,
        message: str,
        start_ms: float,
    ) -> ChatMessageResponse:
        if db_session.message_count >= _MAX_MESSAGES:
            raise ChatMessageLimitError(
                details={"session_id": str(session_id), "limit": _MAX_MESSAGES},
        )

        history = await self._get_db_messages_as_history(session_id)
        wound_type, severity, sub_type, firstaid_snapshot = (
            await self._wound_context.load_wound_context(
                db_session.analysis_id,
            )
        )
        rag_chunks = await self._rag.query(wound_type, severity, message)
        system_prompt = self._pb.build_wound_advisor_prompt(
            wound_type=wound_type,
            severity=severity,
            sub_type=sub_type,
            firstaid_snapshot=firstaid_snapshot,
            rag_chunks=rag_chunks,
        )
        llm_messages = self._pb.build_messages(system_prompt, history, message)
        llm_cfg = await resolve_llm_config(self._db, "chatbot_advisor")
        reply, tokens_used = await self._call_llm(
            llm_messages,
            max_tokens=llm_cfg.max_tokens,
            temperature=llm_cfg.temperature,
            config_key="chatbot_advisor",
            model=llm_cfg.model_name,
        )

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self._save_db_exchange(session_id, message, reply, tokens_used, now)

        new_count = db_session.message_count + 1
        elapsed = int((time.monotonic() - start_ms) * 1000)
        logger.info(
            "[ChatService] Wound Advisor reply - session=%s, msg=%d/%d, tokens=%d, ms=%d.",
            session_id,
            new_count,
            _MAX_MESSAGES,
            tokens_used,
            elapsed,
        )

        return ChatMessageResponse(
            session_id=session_id,
            reply=reply,
            tokens_used=tokens_used,
            message_count=new_count,
            remaining_messages=max(0, _MAX_MESSAGES - new_count),
            created_at=now,
        )

    async def _reply_app_guide(
        self,
        redis_meta: dict[str, str],
        session_id: UUID,
        message: str,
        start_ms: float,
    ) -> ChatMessageResponse:
        count = int(redis_meta.get("message_count", 0))
        if count >= _MAX_MESSAGES:
            raise ChatMessageLimitError(
                details={"session_id": str(session_id), "limit": _MAX_MESSAGES},
            )

        history = await self._redis_store.get_messages(session_id)
        system_prompt = self._pb.build_app_guide_prompt()
        llm_messages = self._pb.build_messages(system_prompt, history, message)
        llm_cfg = await resolve_llm_config(self._db, "chatbot_guide")
        reply, tokens_used = await self._call_llm(
            llm_messages,
            max_tokens=llm_cfg.max_tokens,
            temperature=llm_cfg.temperature,
            config_key="chatbot_guide",
            model=llm_cfg.model_name,
        )

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self._redis_store.save_message(session_id, "user", message, now)
        await self._redis_store.save_message(session_id, "assistant", reply, now)
        await self._redis_store.increment_count(session_id)

        new_count = count + 1
        elapsed = int((time.monotonic() - start_ms) * 1000)
        logger.info(
            "[ChatService] App Guide reply - session=%s, msg=%d/%d, tokens=%d, ms=%d.",
            session_id,
            new_count,
            _MAX_MESSAGES,
            tokens_used,
            elapsed,
        )

        return ChatMessageResponse(
            session_id=session_id,
            reply=reply,
            tokens_used=tokens_used,
            message_count=new_count,
            remaining_messages=max(0, _MAX_MESSAGES - new_count),
            created_at=now,
        )

    async def _create_wound_advisor_session(
        self,
        user_id: UUID,
        analysis_id: UUID,
        now: datetime,
    ) -> CreateSessionResponse:
        analysis = await self._wound_context.load_analysis(analysis_id, user_id)
        if not analysis:
            raise ChatAnalysisNotFoundError(
                details={"analysis_id": str(analysis_id)},
            )

        session = ChatSession(
            user_id=user_id,
            analysis_id=analysis_id,
            message_count=0,
            status="active",
            created_at=now,
            updated_at=now,
        )
        session = await self._repo.create_session(session)

        return CreateSessionResponse(
            session_id=session.session_id,
            analysis_id=analysis_id,
            session_type="wound_advisor",
            max_messages=_MAX_MESSAGES,
            created_at=now,
        )

    async def _create_app_guide_session(
        self,
        user_id: UUID,
        now: datetime,
    ) -> CreateSessionResponse:
        session_id = uuid4()
        await self._redis_store.create_session(user_id, session_id, now)

        return CreateSessionResponse(
            session_id=session_id,
            analysis_id=None,
            session_type="app_guide",
            max_messages=_MAX_MESSAGES,
            created_at=now,
        )

    async def _get_db_messages_as_history(self, session_id: UUID) -> list[MessageItem]:
        messages = await self._repo.get_messages(session_id)
        return [
            MessageItem(role=m.role, content=m.content, created_at=m.created_at)
            for m in messages
        ]

    async def _save_db_exchange(
        self,
        session_id: UUID,
        user_message: str,
        assistant_reply: str,
        tokens_used: int,
        created_at: datetime,
    ) -> None:
        await self._repo.save_message(
            ChatMessage(
                session_id=session_id,
                role="user",
                content=user_message,
                tokens_used=0,
                created_at=created_at,
            )
        )
        await self._repo.save_message(
            ChatMessage(
                session_id=session_id,
                role="assistant",
                content=assistant_reply,
                tokens_used=tokens_used,
                created_at=created_at,
            )
        )
        await self._repo.increment_message_count(session_id)

    async def _call_llm(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        config_key: str = "chatbot_advisor",
        model: str | None = None,
    ) -> tuple[str, int]:
        try:
            return await self._llm.call(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=None,
                config_key=config_key,
                model=model,
            )
        except Exception as exc:
            raise ChatLLMError(
                message="Không thể tạo phản hồi từ AI",
                details={"error": str(exc)[:200]},
            ) from exc
