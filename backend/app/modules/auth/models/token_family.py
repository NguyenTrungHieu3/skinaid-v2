from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid 

# Refresh Token Rotation
class TokenFamily(SQLModel, table=True): 
    """
        WorkFlow: 
        1. Login → Create token family (refresh_jti + access_jti)
        2. Refresh → Create new family (with parent_jti link)
        3. Logout → Revoke entire family (both access + refresh)
        4. Reuse detection → If refresh token used twice, revoke whole chain
    """
    __tablename__ ="token_families"

    family_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False, index= True)

    # JTIs
    refresh_token_jti: str = Field(unique=True, index=True, nullable=False)
    access_token_jti: Optional[str] = Field(default=None, index=True)
    parent_jti: Optional[str] = Field(default=None, index=True) # Tạo ra chuỗi refresh token 

    # Status
    is_revoke: bool = Field(default=False, index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.nop(timezone.utc))
    expires_at: datetime = Field(nullable=False)

    class Config: 
        from_attributes = True