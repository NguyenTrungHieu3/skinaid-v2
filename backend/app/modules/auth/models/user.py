from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UUID
from typing import Optional, TYPE_CHECKING, List
import uuid
from datetime import datetime, timezone

if TYPE_CHECKING:
    from app.modules.profile.models.user_profile import UserProfile
    from app.modules.auth.models.user_roles import UserRole
    from app.modules.auth.models.verification_token import VerificationToken

class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore

    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_name: str = Field(unique=True, index=True, nullable=False)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    token_version: int = Field(default=0, nullable=False)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    profile: Optional["UserProfile"] = Relationship(back_populates="user")
    user_roles: List["UserRole"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "foreign_keys": "[UserRole.user_id]"
        }
    )
