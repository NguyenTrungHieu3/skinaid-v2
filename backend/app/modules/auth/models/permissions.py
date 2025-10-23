from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UUID
import uuid
from typing import Optional
from typing import List, TYPE_CHECKING
from datetime import datetime, timezone
if TYPE_CHECKING:
    from app.modules.auth.models.role_permissions import RolePermission

class Permission(SQLModel, table=True):
    __tablename__ = "permissions"

    permission_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )
    permission_name: str = Field(max_length=100, nullable=False, unique=True, index=True)
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    role_permissions: List["RolePermission"] = Relationship(
        back_populates="permission",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
