from typing import Optional
from uuid import UUID

from fastapi import Cookie, Header

from app.shared.exceptions.base import BadRequestError


async def get_session_id(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> Optional[UUID]:
    session_str = session_id or x_session_id

    if session_str:
        try:
            return UUID(session_str)
        except ValueError:
            raise BadRequestError(
                message="Invalid session_id format",
                details={"provided_value": session_str},
            )

    return None
