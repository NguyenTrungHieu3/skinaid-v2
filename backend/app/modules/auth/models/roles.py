from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from app.shared.models.basemodel import TimestampMixin
import uuid

if TYPE_CHECKING:
    from models.user_roles import UserRole
    from models.role_permissions import RolePermission


class Role(SQLModel, TimestampMixin, table=True):
    __tablename__ = "roles"

    role_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )

    role_name: str = Field(
        max_length=50,
        unique=True,
        index=True
    )

    description: Optional[str] = None

    is_active: bool = Field(default=True)

    user_roles: list["UserRole"] = Relationship(
        back_populates="role", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    role_permissions: list["RolePermission"] = Relationship (
        back_populates="role",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
