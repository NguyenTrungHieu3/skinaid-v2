from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey, UUID
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from uuid import uuid4, UUID

if TYPE_CHECKING:
    from app.modules.users.models import User
    from app.modules.auth.models.roles import Role


class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"
    
    user_id: UUID = Field(
        sa_column=Column(
            ForeignKey("users.user_id", ondelete="CASCADE"),
            primary_key=True
        )
    )
    
    role_id: UUID = Field(
        sa_column=Column(
            ForeignKey("roles.role_id", ondelete="CASCADE"),
            primary_key=True
        )
    )
    
    assigned_by: Optional[UUID] = Field(
        default=None,
        sa_column=Column(
            ForeignKey("users.user_id", ondelete="SET NULL")
        )
    )
    
    assigned_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Ngày hết hạn vai trò. NULL = vĩnh viễn"
    )
    user: "User" = Relationship(
        back_populates="user_roles",
        sa_relationship_kwargs={"foreign_keys": "[UserRole.user_id]"}
    )
    
    role: "Role" = Relationship(back_populates="user_roles")
    
    @property
    def is_expired(self) -> bool:
        """Kiểm tra xem vai trò tạm thời đã hết hạn chưa"""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc).replace(tzinfo=None) > self.expires_at