from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import date
from app.shared.models.basemodel import TimestampMixin
import uuid

if TYPE_CHECKING:
    from app.modules.auth.models.user import User

class UserProfile(SQLModel, TimestampMixin, table=True):
    __tablename__ = "user_profiles"  # type: ignore

    profile_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.user_id", unique=True)
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None  # 'male', 'female', 'other'
    address: Optional[str] = None
    avatar_url: Optional[str] = None

    # Relationship back to user
    user: Optional["User"] = Relationship(back_populates="profile")