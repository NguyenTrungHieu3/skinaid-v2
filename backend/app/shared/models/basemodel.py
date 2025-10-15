from sqlmodel import Field
from datetime import datetime, timezone

def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
class TimestampMixin:
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )
