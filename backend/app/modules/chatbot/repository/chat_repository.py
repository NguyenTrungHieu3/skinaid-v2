from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chatbot.models.chat_messages import ChatMessage
from app.modules.chatbot.models.chat_sessions import ChatSession


class ChatRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_session(self, session: ChatSession) -> ChatSession:
        self._db.add(session)
        await self._db.flush()
        await self._db.refresh(session)
        return session

    async def get_session(
        self, session_id: UUID, user_id: UUID,
    ) -> ChatSession | None:
        stmt = select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_messages(
        self, session_id: UUID,
    ) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def save_message(self, msg: ChatMessage) -> ChatMessage:
        self._db.add(msg)
        await self._db.flush()
        return msg

    async def increment_message_count(self, session_id: UUID) -> None:
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
