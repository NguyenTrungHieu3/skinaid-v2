import uuid
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models.user import User
from app.modules.auth.schemas.user_schemas import UserCreate

# Import domain services
from .user_service import UserService
from .password_service import PasswordService
from .authentication_service import AuthenticationService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)
        self.password_service = PasswordService(db, user_service=self.user_service)
        self.auth_service = AuthenticationService(db, user_service=self.user_service)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self.user_service.get_user_by_email(email)

    async def get_user_by_username(self, user_name: str) -> Optional[User]:
        return await self.user_service.get_user_by_username(user_name)

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return await self.user_service.get_user_by_id(user_id)

    async def create_user(self, user_data: UserCreate) -> User:
        return await self.user_service.create_user(user_data)

    async def initiate_password_reset(self, email: str) -> bool:
        return await self.password_service.initiate_password_reset(email)

    async def reset_password(
        self,
        email: str,
        token: str,
        new_password: str,
    ) -> bool:
        return await self.password_service.reset_password(email, token, new_password)

    async def change_password(
        self,
        user_id: uuid.UUID,
        old_password: str,
        new_password: str,
    ) -> bool:
        return await self.password_service.change_password(user_id, old_password, new_password)

    async def authenticate_user(self, user_name: str, password: str) -> User:
        return await self.auth_service.authenticate_user(user_name, password)

    async def get_user_token_version(self, user_id: uuid.UUID) -> Optional[int]:
        return await self.auth_service.get_user_token_version(user_id)

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> dict:
        return await self.auth_service.revoke_all_user_tokens(user_id)
