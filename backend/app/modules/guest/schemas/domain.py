from typing import Optional
from pydantic import BaseModel, Field


class GuestSessionBase(BaseModel):
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None
