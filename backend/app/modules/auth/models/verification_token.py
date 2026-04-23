from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey, UUID
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID

if TYPE_CHECKING:
    from app.modules.users.models import User

class VerificationToken(SQLModel, table=True):
    __tablename__ = "verification_tokens"  # type: ignore

    token_id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(
        sa_column=Column(
            ForeignKey("users.email", ondelete="CASCADE")
        )
    )
    token: str = Field(unique=True)
    token_type: str  # 'email_verify' | 'password_reset' | 'phone_verify'

    max_uses: int = Field(default=1)
    use_count: int = Field(default=0)
    expires_at: datetime
    is_used: bool = Field(default=False)

    created_ip: Optional[str] = Field(default=None, max_length=45)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    # updated_at intentionally omitted — token is immutable after creation (no trigger needed)

    @property
    def is_expired(self) -> bool:
        """Kiểm tra xem token đã hết hạn chưa."""
        return datetime.now(timezone.utc).replace(tzinfo=None) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Kiểm tra xem token có hợp lệ không (chưa hết hạn và chưa sử dụng)."""
        return not self.is_expired and not self.is_used

    @classmethod
    def create_token(
        cls,
        email: str,
        token_type: str,
        expires_in_hours: int = 24,
        expires_in_minutes: Optional[int] = None,
    ) -> "VerificationToken":
        """Tạo token xác thực mới."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        if expires_in_minutes is not None:
            delta = timedelta(minutes=expires_in_minutes)
        else:
            delta = timedelta(hours=expires_in_hours)
        return cls(
            email=email,
            token=cls._generate_token(),
            token_type=token_type,
            expires_at=current_time + delta,
            is_used=False,
            created_at=current_time,
        )

    @staticmethod
    def _generate_token() -> str:
        """Tạo token ngẫu nhiên an toàn."""
        import secrets
        return secrets.token_urlsafe(32)