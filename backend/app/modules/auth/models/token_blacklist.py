from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
import uuid
from typing import Optional

class TokenBlacklist(SQLModel, table=True):
    __tablename__ = "token_blacklist"

    tokenblacklist_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    jti: str = Field(index=True, nullable=False, unique=True)
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.user_id")
    token_type: str = Field(default="access",nullable=False) # "access" or "refresh"
    revoked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # thời gian token bị thu hồi
    expires_at: datetime = Field(nullable=False) # thời gian hết hạn của token