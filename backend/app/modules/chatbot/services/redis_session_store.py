from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

import redis.asyncio as aioredis

from app.core.config import settings
from app.modules.chatbot.schemas.chat_schemas import MessageItem

logger = logging.getLogger(__name__)

_REDIS_PREFIX = "chatbot"


class ChatRedisSessionStore:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    def meta_key(self, session_id: UUID) -> str:
        return f"{_REDIS_PREFIX}:session:{session_id}:meta"

    def msgs_key(self, session_id: UUID) -> str:
        return f"{_REDIS_PREFIX}:session:{session_id}:msgs"

    async def create_session(
        self,
        user_id: UUID,
        session_id: UUID,
        now: datetime,
    ) -> None:
        ttl = settings.CHATBOT_REDIS_TTL_HOURS * 3600
        pipe = self._redis.pipeline()
        pipe.hset(
            self.meta_key(session_id),
            mapping={
                "user_id": str(user_id),
                "created_at": now.isoformat(),
                "message_count": "0",
                "status": "active",
                "last_message_at": "",
            },
        )
        pipe.expire(self.meta_key(session_id), ttl)
        await pipe.execute()

    async def get_session(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> dict[str, str] | None:
        meta = await self._redis.hgetall(self.meta_key(session_id))
        if not meta:
            return None
        if meta.get("user_id") != str(user_id):
            return None
        return meta

    async def get_messages(self, session_id: UUID) -> list[MessageItem]:
        raw_list = await self._redis.lrange(self.msgs_key(session_id), 0, -1)
        items: list[MessageItem] = []
        for raw in raw_list:
            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                logger.warning(
                    "[ChatRedisSessionStore] Skipping corrupt Redis message: %r",
                    raw[:200],
                )
                continue
            items.append(
                MessageItem(
                    role=data["role"],
                    content=data["content"],
                    created_at=datetime.fromisoformat(data["created_at"]),
                )
            )
        return items

    async def save_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        now: datetime,
    ) -> None:
        ttl = settings.CHATBOT_REDIS_TTL_HOURS * 3600
        msg_json = json.dumps(
            {
                "role": role,
                "content": content,
                "created_at": now.isoformat(),
            },
            ensure_ascii=False,
        )

        pipe = self._redis.pipeline()
        pipe.rpush(self.msgs_key(session_id), msg_json)
        pipe.expire(self.msgs_key(session_id), ttl)
        await pipe.execute()

    async def increment_count(self, session_id: UUID) -> None:
        ttl = settings.CHATBOT_REDIS_TTL_HOURS * 3600
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        pipe = self._redis.pipeline()
        pipe.hincrby(self.meta_key(session_id), "message_count", 1)
        pipe.hset(self.meta_key(session_id), "last_message_at", now.isoformat())
        pipe.expire(self.meta_key(session_id), ttl)
        await pipe.execute()

    async def delete_session(self, session_id: UUID) -> bool:
        deleted = await self._redis.delete(
            self.meta_key(session_id),
            self.msgs_key(session_id),
        )
        return deleted > 0
