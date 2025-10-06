from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING, List
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from app.modules.profile.models.user_profile import UserProfile

class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    display_name: Optional[str] = None
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    # Relationship to profile
    profile: Optional["UserProfile"] = Relationship(back_populates="user")