from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

class VerificationToken(SQLModel, table=True):
    __tablename__ = "verification_tokens"  # type: ignore
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(index=True)
    token: str = Field(unique=True)
    token_type: str  # 'email_verification', 'password_reset', etc.
    expires_at: datetime
    is_used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: Optional[datetime] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.now(timezone.utc).replace(tzinfo=None) > self.expires_at