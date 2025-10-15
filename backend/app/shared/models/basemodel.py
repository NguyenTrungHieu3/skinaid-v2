from sqlmodel import Field
from datetime import datetime, timezone

def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class TimestampMixin:
    created_at: datetime = Field(
        default_factory=utcnow,
        nullable=False
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        nullable=False
    )
