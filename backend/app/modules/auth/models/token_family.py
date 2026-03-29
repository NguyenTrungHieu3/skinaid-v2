from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID

# Refresh Token Rotation
class TokenFamily(SQLModel, table=True): 
    """
        Quy trình: 
        1. Đăng nhập → Tạo token family (refresh_jti + access_jti)
        2. Làm mới → Tạo family mới (với liên kết parent_jti)
        3. Đăng xuất → Thu hồi toàn bộ family (cả access + refresh)
        4. Phát hiện tái sử dụng → Nếu refresh token được sử dụng hai lần, thu hồi toàn bộ chuỗi
    """
    __tablename__ ="token_families"

    family_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.user_id", nullable=False, index= True)

    # JTIs
    refresh_token_jti: str = Field(unique=True, index=True, nullable=False)
    access_token_jti: Optional[str] = Field(default=None, index=True)
    parent_jti: Optional[str] = Field(default=None, index=True) # Tạo ra chuỗi refresh token 

    # Status
    is_revoked: bool = Field(default=False, index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    expires_at: datetime = Field(nullable=False)

    class Config: 
        from_attributes = True