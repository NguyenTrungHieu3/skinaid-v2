from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.chatbot.models.chat_messages import ChatMessage
from app.modules.chatbot.models.chat_sessions import ChatSession

logger = logging.getLogger(__name__)


class ChatRepository:
    """DB repository cho chat_sessions + chat_messages."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_session(self, session: ChatSession) -> ChatSession:
        """Tạo session mới, flush để lấy PK."""
        self._db.add(session)
        await self._db.flush()
        await self._db.refresh(session)
        return session

    async def get_session(
        self, session_id: UUID, user_id: UUID,
    ) -> ChatSession | None:
        """Lấy session theo id + user ownership."""
        stmt = select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_session_with_analysis(
        self, session_id: UUID, user_id: UUID,
    ) -> ChatSession | None:
        """Lấy session kèm eager-load Analysis + Detections."""
        from app.modules.ai.models.analysis import Analysis

        stmt = (
            select(ChatSession)
            .where(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user_id,
            )
        )
        result = await self._db.execute(stmt)
        session = result.scalar_one_or_none()

        if session and session.analysis_id:
            analysis_stmt = (
                select(Analysis)
                .options(selectinload(Analysis.wound_detections))  # type: ignore[attr-defined]
                .where(Analysis.analysis_id == session.analysis_id)
            )
            analysis_result = await self._db.execute(analysis_stmt)
            session._loaded_analysis = analysis_result.scalar_one_or_none()  # type: ignore[attr-defined]

        return session

    async def get_messages(
        self, session_id: UUID,
    ) -> list[ChatMessage]:
        """Lấy tất cả messages theo thứ tự thời gian."""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def save_message(self, msg: ChatMessage) -> ChatMessage:
        """Lưu một message, flush để lấy PK."""
        self._db.add(msg)
        await self._db.flush()
        return msg

    async def increment_message_count(self, session_id: UUID) -> None:
        """Tăng message_count + cập nhật last_message_at."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        stmt = (
            update(ChatSession)
            .where(ChatSession.session_id == session_id)
            .values(
                message_count=ChatSession.message_count + 1,
                last_message_at=now,
                updated_at=now,
            )
        )
        await self._db.execute(stmt)

    async def list_user_sessions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[ChatSession], int]:
        """Danh sách sessions của user (DB), paginated."""
        count_stmt = (
            select(func.count())
            .select_from(ChatSession)
            .where(ChatSession.user_id == user_id)
        )
        count_result = await self._db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        sessions = list(result.scalars().all())
        return sessions, total

    async def end_session(self, session_id: UUID) -> None:
        """Soft close — set status='ended'."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        stmt = (
            update(ChatSession)
            .where(ChatSession.session_id == session_id)
            .values(status="ended", updated_at=now)
        )
        await self._db.execute(stmt)
