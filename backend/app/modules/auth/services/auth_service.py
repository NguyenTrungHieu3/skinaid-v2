from sqlmodel import text, select
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models.user import User
from app.modules.auth.models.verification_token import VerificationToken
from app.modules.auth.models.user_profile import UserProfile
import uuid
import asyncio
import logging
from app.utils.exceptions.base_exceptions import AppBaseException
from app.utils.constants.error_codes import (
    AUTH_EMAIL_EXISTS,
    AUTH_PASSWORD_WEAK,
    AUTH_INVALID_CREDENTIALS,
    AUTH_ACCOUNT_INACTIVE,
    AUTH_VERIFICATION_REQUIRED,
    USER_INVALID_DATA,
    USER_NOT_FOUND
)
import os

logger = logging.getLogger(__name__)

use_mock_email = os.getenv("TESTING") == "true" or os.getenv("USE_MOCK_EMAIL") == "true"
if use_mock_email:
    from app.utils.mock_email_service import mock_email_service as email_service
    logger.info("Using MOCK email service")
else:
    from app.utils.email_service import email_service
    logger.info("Using REAL email service")

from app.utils.validators.auth_validators import validate_password_strength, validate_email

from app.core.Security.password import hash_password, verify_password
from app.modules.auth.schemas.user_schemas import UserCreate
from datetime import datetime, timedelta, timezone

class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Lấy thông tin người dùng theo email sử dụng truy vấn SQL có tham số.
        """
        try:
            email_error = validate_email(email)
            if email_error:
                raise AppBaseException(message=f"Invalid email format: {email_error}", error_code=USER_INVALID_DATA)

            sql = text("""
                SELECT * FROM users WHERE email = :email
            """)

            result = await self.db.execute(sql, {"email": email})
            row = result.mappings().first()

            if not row:
                return None

            return User.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            raise



    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Lấy thông tin người dùng theo ID kèm hồ sơ sử dụng truy vấn SQL tối ưu.
        """
        try:
            sql = text("""
                SELECT
                    u.*,
                    p.full_name,
                    p.phone,
                    p.date_of_birth,
                    p.gender,
                    p.address,
                    p.avatar_url,
                    p.created_at as profile_created_at,
                    p.updated_at as profile_updated_at
                FROM users u
                LEFT JOIN user_profiles p ON u.user_id = p.user_id
                WHERE u.user_id = :user_id
            """)

            result = await self.db.execute(sql, {"user_id": user_id})
            row = result.mappings().first()

            if not row:
                return None

            # Create user object
            user_data = {
                "user_id": row["user_id"],
                "email": row["email"],
                "hashed_password": row["hashed_password"],
                "display_name": row["display_name"],
                "is_active": row["is_active"],
                "is_verified": row["is_verified"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
            user = User.model_validate(user_data)

            if row["full_name"]:
                profile_data = {
                    "user_id": row["user_id"],
                    "full_name": row["full_name"],
                    "phone": row["phone"],
                    "date_of_birth": row["date_of_birth"],
                    "gender": row["gender"],
                    "address": row["address"],
                    "avatar_url": row["avatar_url"],
                    "created_at": row["profile_created_at"],
                    "updated_at": row["profile_updated_at"]
                }
                user.profile = UserProfile.model_validate(profile_data)

            return user
            
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {str(e)}")
            raise
        
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Tạo người dùng mới kèm hồ sơ sử dụng quản lý giao dịch phù hợp.
        """
        try:
            email_errors = validate_email(user_data.email)
            if email_errors:
                raise AppBaseException(message=f"Email validation failed: {email_errors}", error_code=USER_INVALID_DATA)

            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user:
                raise AppBaseException(message="Email is already registered", error_code=AUTH_EMAIL_EXISTS)

            password_errors = validate_password_strength(user_data.password)
            if password_errors:
                raise AppBaseException(message=password_errors, error_code=AUTH_PASSWORD_WEAK)

            user_id = str(uuid.uuid4())
            current_time = datetime.now(timezone.utc).replace(tzinfo=None)
            hashed_password = hash_password(user_data.password)
            verification_token = email_service.generate_verification_token()

            # Insert user
            await self.db.execute(text("""
                INSERT INTO users (user_id, email, hashed_password, display_name, is_active, is_verified, created_at, updated_at)
                VALUES (:user_id, :email, :hashed_password, :display_name, :is_active, :is_verified, :created_at, :updated_at)
            """), {
                "user_id": user_id,
                "email": user_data.email,
                "hashed_password": hashed_password,
                "display_name": user_data.email.split('@')[0],
                "is_active": True,
                "is_verified": False,
                "created_at": current_time,
                "updated_at": current_time
            })

            # Insert user profile
            await self.db.execute(text("""
                INSERT INTO user_profiles (user_id, created_at, updated_at)
                VALUES(:user_id, :created_at, :updated_at)
            """), {
                "user_id": user_id,
                "created_at": current_time,
                "updated_at": current_time
            })

            # Insert verification token
            await self.db.execute(text("""
                INSERT INTO verification_tokens (token_id, email, token, token_type, expires_at, is_used, created_at, updated_at)
                VALUES (:token_id, :email, :token, :token_type, :expires_at, :is_used, :created_at, :updated_at)
            """), {
                "token_id": str(uuid.uuid4()),
                "email": user_data.email,
                "token": verification_token,
                "token_type": "email_verification",
                "expires_at": current_time + timedelta(hours=24),
                "is_used": False,
                "created_at": current_time,
                "updated_at": current_time
            })

            try:
                await self.db.commit()
                logger.info(f"Database transaction committed for user: {user_data.email}")
            except Exception as commit_error:
                logger.error(f"Failed to commit transaction for user {user_data.email}: {str(commit_error)}")
                raise AppBaseException(message="Failed to save user to database", error_code=USER_INVALID_DATA)

            # Get created user
            user_result = await self.db.execute(text("""
                SELECT user_id, email, hashed_password, display_name, is_active, is_verified, created_at, updated_at
                FROM users WHERE user_id = :user_id
            """), {"user_id": user_id})
            user_mapping = user_result.mappings().first()
            if not user_mapping:
                logger.error(f"User not found after creation: {user_id}")
                raise AppBaseException(message="Failed to retrieve created user", error_code=USER_INVALID_DATA)

            user = User.model_validate(dict(user_mapping))

            try:
                asyncio.create_task(
                    email_service.send_verification_email_async(user_data.email, verification_token)
                )
                logger.info(f"Verification email queued for: {user_data.email}")
            except Exception as email_error:
                logger.error(f"Failed to queue verification email for {user_data.email}: {str(email_error)}")

            logger.info(f"Successfully created user with email: {user_data.email}")
            return user

        except AppBaseException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating user {user_data.email}: {str(e)}", exc_info=True)
            try:
                await self.db.rollback()
                logger.info("Transaction rolled back due to error")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback transaction: {str(rollback_error)}")

            raise AppBaseException(message="Failed to create user due to internal error", error_code=USER_INVALID_DATA)
    
    async def authenticate_user(self, email: str, password: str) -> User:
        """
        Xác thực người dùng với xử lý lỗi phù hợp.
        """
        try:
            email_error = validate_email(email)
            if email_error:
                raise AppBaseException(message="Invalid email format", error_code=AUTH_INVALID_CREDENTIALS)

            user = await self.get_user_by_email(email)
            if not user:
                raise AppBaseException(message="Invalid email or password", error_code=AUTH_INVALID_CREDENTIALS)

            if not user.is_active:
                raise AppBaseException(message="Account is deactivated", error_code=AUTH_ACCOUNT_INACTIVE)

            if not user.is_verified:
                raise AppBaseException(message="Account verification required", error_code=AUTH_VERIFICATION_REQUIRED)

            if not verify_password(password, user.hashed_password):
                raise AppBaseException(message="Invalid email or password", error_code=AUTH_INVALID_CREDENTIALS)
            
            update_sql = text("""
                UPDATE users
                SET updated_at = :updated_at
                WHERE user_id = :user_id
            """)

            await self.db.execute(
                update_sql,
                {"updated_at": datetime.now(timezone.utc).replace(tzinfo=None), "user_id": user.user_id}
            )

            await self.db.commit()
            updated_user = await self.get_user_by_id(str(user.user_id))
            if updated_user is None:
                raise AppBaseException(message="User not found after authentication", error_code=USER_NOT_FOUND)
            logger.info(f"User authenticated successfully: {email}")
            return updated_user
            
        except AppBaseException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            raise AppBaseException(message="Authentication failed due to internal error", error_code=AUTH_INVALID_CREDENTIALS)

    async def verify_email(self, email: str, token: str) -> bool:
        """
        Xác thực email người dùng sử dụng mã xác thực
        """
        try:
            logger.info(f"Starting email verification for {email} with token {token[:20]}...")
            
            token_sql = text("""
                SELECT * FROM verification_tokens
                WHERE email = :email AND token = :token AND is_used = false
            """)

            result = await self.db.execute(token_sql, {"email": email, "token": token})
            token_row = result.mappings().first()

            if not token_row:
                logger.error(f"Token not found or already used for email {email}")
                raise AppBaseException(message="Invalid or expired verification token", error_code=AUTH_INVALID_CREDENTIALS)

            verification_token = VerificationToken.model_validate(dict(token_row))
            logger.info(f"Token found for {email}, checking expiry...")

            if verification_token.is_expired:
                logger.error(f"Token expired for email {email}")
                raise AppBaseException(message="Verification token has expired", error_code=AUTH_INVALID_CREDENTIALS)

            logger.info(f"Token valid, updating token as used...")
            update_token_sql = text("""
                UPDATE verification_tokens
                SET is_used = true, updated_at = :updated_at
                WHERE token_id = :token_id
            """)

            await self.db.execute(update_token_sql, {
                "token_id": verification_token.token_id,
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
            })

            logger.info(f"Updating user verification status for {email}...")
            update_user_sql = text("""
                UPDATE users
                SET is_verified = true, updated_at = :updated_at
                WHERE email = :email
            """)

            await self.db.execute(update_user_sql, {
                "email": email,
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
            })

            await self.db.commit()
            logger.info(f"Database changes committed successfully for {email}")

            verification_check_sql = text("""
                SELECT is_verified FROM users WHERE email = :email
            """)
            check_result = await self.db.execute(verification_check_sql, {"email": email})
            check_row = check_result.mappings().first()
            
            if check_row and check_row['is_verified']:
                logger.info(f"Verification confirmed in database for {email}")
            else:
                logger.error(f"Verification failed to persist in database for {email}")
                raise AppBaseException(message="Email verification failed to save", error_code=AUTH_INVALID_CREDENTIALS)

            try:
                user = await self.get_user_by_email(email)
                if user and user.display_name:
                    asyncio.create_task(
                        email_service.send_welcome_email_async(email, user.display_name)
                    )
                    logger.info(f"Welcome email queued for: {email}")
            except Exception as e:
                logger.error(f"Failed to queue welcome email to {email}: {str(e)}")

            logger.info(f"Email verification successful for: {email}")
            return True
            
        except AppBaseException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during email verification: {str(e)}")
            raise AppBaseException(message="Email verification failed due to internal error", error_code=AUTH_INVALID_CREDENTIALS)

    async def initiate_password_reset(self, email: str) -> bool:
        """
        Khởi tạo quá trình đặt lại mật khẩu bằng cách gửi mã đặt lại
        """
        try:
            import random

            user = await self.get_user_by_email(email)
            if not user:
                delay = random.uniform(0.5, 2.0)
                await asyncio.sleep(delay)
                return True

            reset_token = email_service.generate_verification_token()

            token_sql = text("""
                INSERT INTO verification_tokens (token_id, email, token, token_type, expires_at, is_used, created_at, updated_at)
                VALUES (:token_id, :email, :token, :token_type, :expires_at, :is_used, :created_at, :updated_at)
                RETURNING *
            """)

            current_time = datetime.now(timezone.utc).replace(tzinfo=None)

            token_params = {
                "token_id": str(uuid.uuid4()),
                "email": email,
                "token": reset_token,
                "token_type": "password_reset",
                "expires_at": current_time + timedelta(hours=1),
                "is_used": False,
                "created_at": current_time,
                "updated_at": current_time
            }

            await self.db.execute(token_sql, token_params)

            try:
                asyncio.create_task(
                    email_service.send_password_reset_email_async(email, reset_token)
                )
                logger.info(f"Password reset email queued for: {email}")
            except Exception as e:
                logger.error(f"Failed to queue password reset email to {email}: {str(e)}")

            return True
            
        except AppBaseException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during password reset initiation: {str(e)}")
            raise AppBaseException(message="Password reset initiation failed due to internal error", error_code=AUTH_INVALID_CREDENTIALS)

    async def reset_password(self, email: str, token: str, new_password: str) -> bool:
        """
        Đặt lại mật khẩu người dùng sử dụng mã xác thực
        """
        try:
            password_errors = validate_password_strength(new_password)
            if password_errors:
                raise AppBaseException(message=password_errors, error_code=AUTH_PASSWORD_WEAK)

            token_sql = text("""
                SELECT * FROM verification_tokens
                WHERE email = :email AND token = :token AND token_type = 'password_reset' AND is_used = false
            """)

            result = await self.db.execute(token_sql, {"email": email, "token": token})
            token_row = result.mappings().first()

            if not token_row:
                raise AppBaseException(message="Invalid or expired password reset token", error_code=AUTH_INVALID_CREDENTIALS)

            verification_token = VerificationToken.model_validate(dict(token_row))

            if verification_token.is_expired:
                raise AppBaseException(message="Password reset token has expired", error_code=AUTH_INVALID_CREDENTIALS)

            update_token_sql = text("""
                UPDATE verification_tokens
                SET is_used = true, updated_at = :updated_at
                WHERE token_id = :token_id
            """)

            await self.db.execute(update_token_sql, {
                "token_id": verification_token.token_id,
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
            })

            hashed_password = hash_password(new_password)
            update_user_sql = text("""
                UPDATE users
                SET hashed_password = :hashed_password, updated_at = :updated_at
                WHERE email = :email
            """)

            await self.db.execute(update_user_sql, {
                "email": email,
                "hashed_password": hashed_password,
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
            })

            await self.db.commit()
            logger.info(f"Password reset successful for user: {email}")
            return True
            
        except AppBaseException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during password reset: {str(e)}")
            raise AppBaseException(message="Password reset failed due to internal error", error_code=AUTH_INVALID_CREDENTIALS)
    
    async def resend_verification_email(self, email: str) -> bool:
        """Gửi lại email xác thực cho người dùng."""
        try:
            user = await self.get_user_by_email(email)
            if not user:
                return True

            if user.is_verified:
                return True

            verification_token = email_service.generate_verification_token()

            token_sql = text("""
                INSERT INTO verification_tokens (token_id, email, token, token_type, expires_at, is_used, created_at, updated_at)
                VALUES (:token_id, :email, :token, :token_type, :expires_at, :is_used, :created_at, :updated_at)
            """)

            current_time = datetime.now(timezone.utc).replace(tzinfo=None)

            token_params = {
                "token_id": str(uuid.uuid4()),
                "email": email,
                "token": verification_token,
                "token_type": "email_verification",
                "expires_at": current_time + timedelta(hours=24),
                "is_used": False,
                "created_at": current_time,
                "updated_at": current_time
            }
            
            await self.db.execute(token_sql, token_params)
            
            try:
                asyncio.create_task(
                    email_service.send_verification_email_async(email, verification_token)
                )
                logger.info(f"Verification email resent to: {email}")
                return True
            except Exception as e:
                logger.error(f"Failed to queue resend verification email to {email}: {str(e)}")
                
        except AppBaseException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during resend verification: {str(e)}")
            raise AppBaseException(message="Resend verification failed due to internal error", error_code=AUTH_INVALID_CREDENTIALS)
        

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool: 
        try: 

            password_errors = validate_password_strength(new_password)
            if password_errors: 
                raise AppBaseException(
                    message= password_errors,
                    error_code= AUTH_PASSWORD_WEAK
                )
            
            if old_password == new_password: 
                raise AppBaseException(
                    message="Mật khẩu mới phải khác mật khẩu cũ",
                    error_code=AUTH_PASSWORD_WEAK
                )
            
            user = await self.get_user_by_id(user_id= user_id)
            if not user: 
                raise AppBaseException(
                    message="Không tìm thấy người dùng",
                    error_code=USER_NOT_FOUND
                )
            
            if not verify_password(old_password, user.hashed_password):
                raise AppBaseException(
                    message="Mật khẩu hiện tại không đúng",
                    error_code=AUTH_INVALID_CREDENTIALS
                )
            
            hashed_password = hash_password(new_password)

            update_sql = text("""
                UPDATE users
                SET hashed_password = :hashed_password, updated_at = :updated_at
                WHERE user_id = :user_id
            """ )

            await self.db.execute(update_sql, {
                "user_id": user_id,
                "hashed_password": hashed_password,
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
            })

            await self.db.commit()
            try:
                asyncio.create_task(
                    email_service.send_password_changed_notification_async(user.email, user.display_name or "")
                )
                logger.info(f"Password change notification queued for: {user.email}")
            except Exception as e:
                logger.error(f"Failed to queue password change notification to {user.email}: {str(e)}")
            
            logger.info(f"Password changed successfully for user: {user_id}")
            return True
            
        except AppBaseException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during password change: {str(e)}")
            raise AppBaseException(
                message="Password change failed due to internal error",
                error_code="PASSWORD_CHANGE_ERROR"
            )
