from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
from app.modules.auth.schemas.user_schemas import UserResponse


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None

class TokenResponse(Token):
    user: UserResponse

