from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone, timedelta
import uuid

if TYPE_CHECKING:
    from app.modules.auth.models.user import User

class VerificationToken(SQLModel, table=True):
    __tablename__ = "verification_tokens"  # type: ignore

    token_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(
        sa_column=Column(
            ForeignKey("users.email", ondelete="CASCADE")
        )
    )
    token: str = Field(unique=True)
    token_type: str  # 'email_verification', 'password_reset', etc.
    expires_at: datetime
    is_used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.now(timezone.utc).replace(tzinfo=None) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the token is valid (not expired and not used)."""
        return not self.is_expired and not self.is_used

    @classmethod
    def create_token(
        cls,
        email: str,
        token_type: str,
        expires_in_hours: int = 24
    ) -> "VerificationToken":
        """Create a new verification token."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        return cls(
            email=email,
            token=cls._generate_token(),
            token_type=token_type,
            expires_at=current_time + timedelta(hours=expires_in_hours),
            is_used=False,
            created_at=current_time,
            updated_at=current_time
        )

    @staticmethod
    def _generate_token() -> str:
        """Generate a secure random token."""
        import secrets
        return secrets.token_urlsafe(32)