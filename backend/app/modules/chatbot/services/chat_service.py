from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.modules.ai.models.analysis import Analysis
from app.modules.chatbot.exceptions import (
    ChatAnalysisNotFoundError,
    ChatLLMError,
    ChatMessageLimitError,
    ChatSessionExpiredError,
    ChatSessionNotFoundError,
)
from app.modules.chatbot.models.chat_messages import ChatMessage
from app.modules.chatbot.models.chat_sessions import ChatSession
from app.modules.chatbot.repository.chat_repository import ChatRepository
from app.modules.chatbot.schemas.chat_schemas import (
    ChatMessageResponse,
    CreateSessionResponse,
    MessageItem,
    SessionDetailResponse,
    SessionSummaryResponse,
)
from app.modules.chatbot.services.chat_prompt_builder import ChatPromptBuilder
from app.modules.llm.services.llm_service import LLMService

logger = logging.getLogger(__name__)

_REDIS_PREFIX = "chatbot"
_MAX_MESSAGES = settings.CHATBOT_MAX_MESSAGES


class ChatService:
    """Main orchestrator cho chatbot — 2 mode: Wound Advisor + App Guide."""

    def __init__(
        self,
        db: AsyncSession,
        redis: aioredis.Redis,
        llm_service: LLMService,
        prompt_builder: ChatPromptBuilder,
    ) -> None:
        self._db = db
        self._redis = redis
        self._llm = llm_service
        self._pb = prompt_builder
        self._repo = ChatRepository(db)

    # ── Public API ───────────────────────────────────────────────────────

    async def create_session(
        self, user_id: UUID, analysis_id: UUID | None,
    ) -> CreateSessionResponse:
        """Tạo session mới — DB (wound_advisor) hoặc Redis (app_guide)."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if analysis_id:
            # Validate analysis ownership + status
            analysis = await self._load_analysis(analysis_id, user_id)
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

        # App Guide — Redis session
        session_id = uuid4()
        await self._create_redis_session(user_id, session_id, now)

        return CreateSessionResponse(
            session_id=session_id,
            analysis_id=None,
            session_type="app_guide",
            max_messages=_MAX_MESSAGES,
            created_at=now,
        )

    async def send_message(
        self,
        user_id: UUID,
        session_id: UUID,
        message: str,
    ) -> ChatMessageResponse:
        """Gửi message + nhận AI reply. Resolve mode → build prompt → LLM → save."""
        start_ms = time.monotonic()

        # Step 1: Resolve session
        db_session = await self._repo.get_session(session_id, user_id)
        if db_session:
            return await self._handle_wound_advisor(
                db_session, user_id, session_id, message, start_ms,
            )

        redis_meta = await self._get_redis_session(session_id, user_id)
        if redis_meta:
            return await self._handle_app_guide(
                redis_meta, user_id, session_id, message, start_ms,
            )

        raise ChatSessionNotFoundError(details={"session_id": str(session_id)})

    async def get_session_detail(
        self, user_id: UUID, session_id: UUID,
    ) -> SessionDetailResponse:
        """Lấy chi tiết session + messages."""
        # Check DB first
        db_session = await self._repo.get_session(session_id, user_id)
        if db_session:
            msgs = await self._repo.get_messages(session_id)
            items = [
                MessageItem(role=m.role, content=m.content, created_at=m.created_at)
                for m in msgs
            ]
            return SessionDetailResponse(
                session_id=db_session.session_id,
                analysis_id=db_session.analysis_id,
                session_type="wound_advisor" if db_session.analysis_id else "app_guide",
                messages=items,
                message_count=db_session.message_count,
                remaining_messages=max(0, _MAX_MESSAGES - db_session.message_count),
                status=db_session.status,
                created_at=db_session.created_at,
            )

        # Check Redis
        redis_meta = await self._get_redis_session(session_id, user_id)
        if redis_meta:
            items = await self._get_redis_messages(session_id)
            count = int(redis_meta.get("message_count", 0))
            return SessionDetailResponse(
                session_id=session_id,
                analysis_id=None,
                session_type="app_guide",
                messages=items,
                message_count=count,
                remaining_messages=max(0, _MAX_MESSAGES - count),
                status=redis_meta.get("status", "active"),
                created_at=datetime.fromisoformat(redis_meta["created_at"]),
            )

        raise ChatSessionNotFoundError(details={"session_id": str(session_id)})

    async def list_sessions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        include_general: bool = False,
    ) -> tuple[list[SessionSummaryResponse], int]:
        """Danh sách sessions. Mặc định chỉ DB (wound_advisor)."""
        sessions, total = await self._repo.list_user_sessions(user_id, skip, limit)

        summaries = [
            SessionSummaryResponse(
                session_id=s.session_id,
                analysis_id=s.analysis_id,
                session_type="wound_advisor" if s.analysis_id else "app_guide",
                message_count=s.message_count,
                last_message_at=s.last_message_at,
                status=s.status,
                created_at=s.created_at,
            )
            for s in sessions
        ]

        if include_general:
            redis_summaries = await self._list_redis_sessions(user_id)
            summaries.extend(redis_summaries)
            total += len(redis_summaries)

        return summaries, total

    async def delete_session(self, user_id: UUID, session_id: UUID) -> None:
        """Kết thúc session — DB soft close / Redis DEL."""
        db_session = await self._repo.get_session(session_id, user_id)
        if db_session:
            await self._repo.end_session(session_id)
            return

        redis_meta = await self._get_redis_session(session_id, user_id)
        if redis_meta:
            await self._delete_redis_session(user_id, session_id)
            return

        raise ChatSessionNotFoundError(details={"session_id": str(session_id)})

    # ── Mode Handlers ────────────────────────────────────────────────────

    async def _handle_wound_advisor(
        self,
        db_session: ChatSession,
        user_id: UUID,
        session_id: UUID,
        message: str,
        start_ms: float,
    ) -> ChatMessageResponse:
        """Wound Advisor: load wound context + RAG → strict prompt → LLM."""
        if db_session.message_count >= _MAX_MESSAGES:
            raise ChatMessageLimitError(
                details={"session_id": str(session_id), "limit": _MAX_MESSAGES},
            )

        # Load history
        db_messages = await self._repo.get_messages(session_id)
        history = [
            MessageItem(role=m.role, content=m.content, created_at=m.created_at)
            for m in db_messages
        ]

        # Load analysis context
        wound_type, severity, sub_type, firstaid_snapshot = await self._load_wound_context(
            db_session.analysis_id,
        )

        # RAG query (graceful fallback)
        rag_chunks = await self._query_rag(wound_type, severity, message)

        # Build prompt
        system_prompt = self._pb.build_wound_advisor_prompt(
            wound_type=wound_type,
            severity=severity,
            sub_type=sub_type,
            firstaid_snapshot=firstaid_snapshot,
            rag_chunks=rag_chunks,
        )
        llm_messages = self._pb.build_messages(system_prompt, history, message)

        # Call LLM
        reply, tokens_used = await self._call_llm(
            llm_messages,
            max_tokens=settings.CHATBOT_ADVISOR_MAX_TOKENS,
            temperature=settings.CHATBOT_ADVISOR_TEMPERATURE,
        )

        # Save messages
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self._repo.save_message(ChatMessage(
            session_id=session_id, role="user", content=message,
            tokens_used=0, created_at=now,
        ))
        await self._repo.save_message(ChatMessage(
            session_id=session_id, role="assistant", content=reply,
            tokens_used=tokens_used, created_at=now,
        ))
        await self._repo.increment_message_count(session_id)

        new_count = db_session.message_count + 1
        elapsed = int((time.monotonic() - start_ms) * 1000)
        logger.info(
            "[ChatService] Wound Advisor reply — session=%s, msg=%d/%d, tokens=%d, ms=%d.",
            session_id, new_count, _MAX_MESSAGES, tokens_used, elapsed,
        )

        return ChatMessageResponse(
            reply=reply,
            session_id=session_id,
            tokens_used=tokens_used,
            message_count=new_count,
            remaining_messages=max(0, _MAX_MESSAGES - new_count),
            created_at=now,
        )

    async def _handle_app_guide(
        self,
        redis_meta: dict[str, str],
        user_id: UUID,
        session_id: UUID,
        message: str,
        start_ms: float,
    ) -> ChatMessageResponse:
        """App Guide: hardcoded prompt → LLM. No RAG."""
        count = int(redis_meta.get("message_count", 0))
        if count >= _MAX_MESSAGES:
            raise ChatMessageLimitError(
                details={"session_id": str(session_id), "limit": _MAX_MESSAGES},
            )

        # Load history from Redis
        history = await self._get_redis_messages(session_id)

        # Build prompt
        system_prompt = self._pb.build_app_guide_prompt()
        llm_messages = self._pb.build_messages(system_prompt, history, message)

        # Call LLM
        reply, tokens_used = await self._call_llm(
            llm_messages,
            max_tokens=settings.CHATBOT_GUIDE_MAX_TOKENS,
            temperature=settings.CHATBOT_GUIDE_TEMPERATURE,
        )

        # Save to Redis
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self._save_redis_message(session_id, "user", message, now)
        await self._save_redis_message(session_id, "assistant", reply, now)
        await self._increment_redis_count(session_id)

        new_count = count + 1
        elapsed = int((time.monotonic() - start_ms) * 1000)
        logger.info(
            "[ChatService] App Guide reply — session=%s, msg=%d/%d, tokens=%d, ms=%d.",
            session_id, new_count, _MAX_MESSAGES, tokens_used, elapsed,
        )

        return ChatMessageResponse(
            reply=reply,
            session_id=session_id,
            tokens_used=tokens_used,
            message_count=new_count,
            remaining_messages=max(0, _MAX_MESSAGES - new_count),
            created_at=now,
        )

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _load_analysis(self, analysis_id: UUID, user_id: UUID) -> Analysis | None:
        """Load analysis, verify ownership and completed status."""
        stmt = (
            select(Analysis)
            .options(selectinload(Analysis.wound_detections))  # type: ignore[attr-defined]
            .where(Analysis.analysis_id == analysis_id)
        )
        result = await self._db.execute(stmt)
        analysis = result.scalar_one_or_none()

        if not analysis:
            return None
        if analysis.user_id != user_id:
            return None
        if analysis.status != "completed":
            return None
        return analysis

    async def _load_wound_context(
        self, analysis_id: UUID | None,
    ) -> tuple[str, str, str | None, dict[str, Any] | None]:
        """Load wound context từ Analysis + first Detection."""
        if not analysis_id:
            return "unknown", "unknown", None, None

        stmt = (
            select(Analysis)
            .options(selectinload(Analysis.wound_detections))  # type: ignore[attr-defined]
            .where(Analysis.analysis_id == analysis_id)
        )
        result = await self._db.execute(stmt)
        analysis = result.scalar_one_or_none()

        if not analysis or not analysis.wound_detections:
            return "unknown", "unknown", None, None

        # Lấy detection có confidence cao nhất
        det = max(analysis.wound_detections, key=lambda d: d.confidence or 0)
        return (
            det.wound_type or "unknown",
            det.severity or "unknown",
            det.sub_type,
            det.firstaid_snapshot,
        )

    async def _query_rag(
        self, wound_type: str, severity: str, user_message: str,
    ) -> list[Any]:
        """RAG hybrid search — graceful fallback nếu fail."""
        try:
            from app.modules.rag.services.qdrant_service import qdrant_service

            query = f"{wound_type} {severity} {user_message}"
            chunks = await qdrant_service.hybrid_search(query=query, top_k=3)
            return chunks
        except Exception as exc:
            logger.warning(
                "[ChatService] RAG search failed, continuing without RAG: %s",
                str(exc)[:200],
            )
            return []

    async def _call_llm(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> tuple[str, int]:
        """Gọi LLMService — text mode (không JSON)."""
        try:
            return await self._llm.call(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=None,  # text mode
            )
        except Exception as exc:
            raise ChatLLMError(
                message="Không thể tạo phản hồi từ AI",
                details={"error": str(exc)[:200]},
            ) from exc

    # ── Redis Operations ─────────────────────────────────────────────────

    def _meta_key(self, session_id: UUID) -> str:
        return f"{_REDIS_PREFIX}:session:{session_id}:meta"

    def _msgs_key(self, session_id: UUID) -> str:
        return f"{_REDIS_PREFIX}:session:{session_id}:msgs"

    def _user_sessions_key(self, user_id: UUID) -> str:
        return f"{_REDIS_PREFIX}:user:{user_id}:sessions"

    async def _create_redis_session(
        self, user_id: UUID, session_id: UUID, now: datetime,
    ) -> None:
        ttl = settings.CHATBOT_REDIS_TTL_HOURS * 3600
        meta_key = self._meta_key(session_id)
        pipe = self._redis.pipeline()
        pipe.hset(meta_key, mapping={
            "user_id": str(user_id),
            "created_at": now.isoformat(),
            "message_count": "0",
            "status": "active",
            "last_message_at": "",
        })
        pipe.expire(meta_key, ttl)
        pipe.sadd(self._user_sessions_key(user_id), str(session_id))
        pipe.expire(self._user_sessions_key(user_id), ttl)
        await pipe.execute()

    async def _get_redis_session(
        self, session_id: UUID, user_id: UUID,
    ) -> dict[str, str] | None:
        meta = await self._redis.hgetall(self._meta_key(session_id))
        if not meta:
            return None
        if meta.get("user_id") != str(user_id):
            return None
        return meta

    async def _get_redis_messages(self, session_id: UUID) -> list[MessageItem]:
        raw_list = await self._redis.lrange(self._msgs_key(session_id), 0, -1)
        items: list[MessageItem] = []
        for raw in raw_list:
            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                logger.warning("[ChatService] Skipping corrupt Redis message: %r", raw[:200])
                continue
            items.append(MessageItem(
                role=data["role"],
                content=data["content"],
                created_at=datetime.fromisoformat(data["created_at"]),
            ))
        return items

    async def _save_redis_message(
        self, session_id: UUID, role: str, content: str, now: datetime,
    ) -> None:
        ttl = settings.CHATBOT_REDIS_TTL_HOURS * 3600
        msg_json = json.dumps({
            "role": role,
            "content": content,
            "created_at": now.isoformat(),
        }, ensure_ascii=False)

        msgs_key = self._msgs_key(session_id)
        pipe = self._redis.pipeline()
        pipe.rpush(msgs_key, msg_json)
        pipe.expire(msgs_key, ttl)
        await pipe.execute()

    async def _increment_redis_count(self, session_id: UUID) -> None:
        ttl = settings.CHATBOT_REDIS_TTL_HOURS * 3600
        meta_key = self._meta_key(session_id)
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        pipe = self._redis.pipeline()
        pipe.hincrby(meta_key, "message_count", 1)
        pipe.hset(meta_key, "last_message_at", now.isoformat())
        pipe.expire(meta_key, ttl)
        await pipe.execute()

    async def _delete_redis_session(self, user_id: UUID, session_id: UUID) -> None:
        pipe = self._redis.pipeline()
        pipe.delete(self._meta_key(session_id))
        pipe.delete(self._msgs_key(session_id))
        pipe.srem(self._user_sessions_key(user_id), str(session_id))
        await pipe.execute()

    async def _list_redis_sessions(self, user_id: UUID) -> list[SessionSummaryResponse]:
        members = await self._redis.smembers(self._user_sessions_key(user_id))
        summaries: list[SessionSummaryResponse] = []
        for sid_str in members:
            meta = await self._redis.hgetall(f"{_REDIS_PREFIX}:session:{sid_str}:meta")
            if not meta:
                continue
            last_msg = meta.get("last_message_at", "")
            summaries.append(SessionSummaryResponse(
                session_id=UUID(sid_str),
                analysis_id=None,
                session_type="app_guide",
                message_count=int(meta.get("message_count", 0)),
                last_message_at=datetime.fromisoformat(last_msg) if last_msg else None,
                status=meta.get("status", "active"),
                created_at=datetime.fromisoformat(meta["created_at"]),
            ))
        return summaries
