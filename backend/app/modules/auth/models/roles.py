from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UUID
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from app.modules.auth.models.user_roles import UserRole
    from app.modules.auth.models.role_permissions import RolePermission


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    role_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )

    role_name: str = Field(
        max_length=50,
        unique=True,
        index=True
    )

    description: Optional[str] = None

    is_active: bool = Field(default=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    user_roles: list["UserRole"] = Relationship(
        back_populates="role", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    role_permissions: list["RolePermission"] = Relationship (
        back_populates="role",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
