from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from app.shared.models.basemodel import utcnow

if TYPE_CHECKING:
    from app.modules.auth.models.user import User
    from app.modules.auth.models.roles import Role


class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"
    
    user_id: str = Field(
        sa_column=Column(
            ForeignKey("users.user_id", ondelete="CASCADE"),
            primary_key=True
        )
    )
    
    role_id: str = Field(
        sa_column=Column(
            ForeignKey("roles.role_id", ondelete="CASCADE"),
            primary_key=True
        )
    )
    
    assigned_by: Optional[str] = Field(
        default=None,
        sa_column=Column(
            ForeignKey("users.user_id", ondelete="SET NULL")
        )
    )
    
    assigned_at: datetime = Field(
        default_factory=utcnow,
        nullable=False
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Role expiry date. NULL = permanent"
    )
    user: "User" = Relationship(back_populates="user_roles")
    
    role: "Role" = Relationship(back_populates="user_roles")
    
    @property
    def is_expired(self) -> bool:
        """Check if temporary role has expired"""
        if self.expires_at is None:
            return False
        return utcnow() > self.expires_at