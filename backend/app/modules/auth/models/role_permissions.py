from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey, UUID
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
import uuid
if TYPE_CHECKING:
    from app.modules.auth.models.roles import Role
    from app.modules.auth.models.permissions import Permission


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"
    role_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("roles.role_id", ondelete="CASCADE"),
            primary_key=True
        )
    )
    
    permission_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("permissions.permission_id", ondelete="CASCADE"),
            primary_key=True
        )
    )
    
    granted_by: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            ForeignKey("users.user_id", ondelete="SET NULL")
        )
    )
    
    granted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False
    )
    
    role: "Role" = Relationship(back_populates="role_permissions")
    
    permission: "Permission" = Relationship(back_populates="role_permissions")