from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING, List
from app.shared.models.basemodel import TimestampMixin
import uuid

if TYPE_CHECKING:
    from app.modules.profile.models.user_profile import UserProfile
    from app.modules.auth.models.user_roles import UserRole

class User(SQLModel, TimestampMixin, table=True):
    __tablename__ = "users"  # type: ignore

    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    display_name: Optional[str] = None
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)

    # Relationship to profile
    profile: Optional["UserProfile"] = Relationship(back_populates="user")
    user_roles: List["UserRole"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )