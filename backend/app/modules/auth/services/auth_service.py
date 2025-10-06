from sqlmodel import text, select
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models.user import User
from app.modules.auth.models.verification_token import VerificationToken
from app.modules.profile.models.user_profile import UserProfile
import uuid 
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

from app.core.security import hash_password, verify_password
from app.modules.auth.schemas.user import UserCreate
from datetime import datetime, timedelta, timezone

class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]: 
        """
        Get a user by email using parameterized SQL query.
        
        Args:
            email: User's email address
            
        Returns:
            User object if found, None otherwise
            
        Raises:
            AppBaseException: If email format is invalid
        """
        try:
            email_error = validate_email(email)
            if email_error:
                raise AppBaseException(message=f"Invalid email format: {email_error}", error_code=USER_INVALID_DATA)
            
            statement = select(User).where(User.email == email)
            result = await self.db.execute(statement)
            user = result.scalars().first()

            if user is None:
                return None

            return user
            
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            raise



    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID with profile using optimized SQL query.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            User object with profile if found, None otherwise
        """
        try:
            sql = text("""
                SELECT
                    u.*,
                    p.id as profile_id,
                    p.full_name,
                    p.phone,
                    p.date_of_birth,
                    p.gender,
                    p.address,
                    p.avatar_url,
                    p.created_at as profile_created_at,
                    p.updated_at as profile_updated_at
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                WHERE u.id = :user_id
            """)

            result = await self.db.execute(sql, {"user_id": user_id})
            row = result.mappings().first()

            if not row: 
                return None 
            
            # Create user object
            user_data = {
                "id": row["id"],
                "email": row["email"],
                "hashed_password": row["hashed_password"],
                "is_active": row["is_active"],
                "is_verified": row["is_verified"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
            user = User.model_validate(user_data)

            if row["profile_id"]:
                profile_data = {
                    "id": row["profile_id"],
                    "user_id": row["id"],
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
        Create a new user with profile using proper transaction management.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created User object with profile
            
        Raises:
            AppBaseException: If validation fails, email exists, or password is weak
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
            
            hashed_password = hash_password(user_data.password)
            user_id = uuid.uuid4()
            current_time = datetime.now(timezone.utc).replace(tzinfo=None) 

            user_sql = text("""
                INSERT INTO users (id, email, hashed_password, display_name, is_active, is_verified, created_at, updated_at)
                VALUES (:id, :email, :hashed_password, :display_name, :is_active, :is_verified, :created_at, :updated_at)
                RETURNING *
            """)

            user_params = {
                "id": str(user_id),
                "email": user_data.email,
                "hashed_password": hashed_password,
                "display_name": user_data.email.split('@')[0],  # Use email prefix as display name
                "is_active": True,
                "is_verified": False,
                "created_at": current_time,
                "updated_at": current_time
            }

            user_result = await self.db.execute(user_sql, user_params)
            user_mapping = user_result.mappings().first()
            if user_mapping is None:
                raise AppBaseException(message="Failed to create user", error_code=USER_INVALID_DATA)
            user = User.model_validate(dict(user_mapping))
            
            profile_id = uuid.uuid4()
            profile_sql = text("""
                INSERT INTO user_profiles (id, user_id, created_at, updated_at)
                VALUES(:id, :user_id, :created_at, :updated_at)
                RETURNING *
            """)

            profile_params = {
                "id": str(profile_id),
                "user_id": str(user.id),
                "created_at": current_time,
                "updated_at": current_time
            }

            profile_result = await self.db.execute(profile_sql, profile_params)
            profile_mapping = profile_result.mappings().first()
            if profile_mapping is None:
                raise AppBaseException(message="Failed to create profile", error_code=USER_INVALID_DATA)
            profile = UserProfile.model_validate(dict(profile_mapping))
            user.profile = profile

            verification_token = email_service.generate_verification_token()

            token_sql = text("""
                INSERT INTO verification_tokens (id, email, token, token_type, expires_at, is_used, created_at)
                VALUES (:id, :email, :token, :token_type, :expires_at, :is_used, :created_at)
                RETURNING *
            """)

            token_params = {
                "id": str(uuid.uuid4()),
                "email": user_data.email,
                "token": verification_token,
                "token_type": "email_verification",
                "expires_at": current_time + timedelta(hours=24),
                "is_used": False,
                "created_at": current_time
            }

            await self.db.execute(token_sql, token_params)
            await self.db.commit()

            try:
                await email_service.send_verification_email(user_data.email, verification_token)
                logger.info(f"Verification email sent to: {user_data.email}")
            except Exception as e:
                logger.error(f"Failed to send verification email to {user_data.email}: {str(e)}")
                
            logger.info(f"Successfully created user with email: {user_data.email}")
            return user
                
        except AppBaseException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating user: {str(e)}")
            raise AppBaseException(message="Failed to create user due to internal error", error_code=USER_INVALID_DATA)
    
    async def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate user with proper error handling.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Authenticated User object with profile
            
        Raises:
            AppBaseException: If credentials are invalid, account is deactivated, or verification is required
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
                WHERE id = :user_id
            """)
            
            await self.db.execute(
                update_sql,
                {"updated_at": datetime.now(timezone.utc).replace(tzinfo=None), "user_id": user.id}
            )
            await self.db.commit()
            
            updated_user = await self.get_user_by_id(str(user.id))
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
        Verify user email using verification token

        Args:
            email: User email
            token: Verification token

        Returns:
            True if verification successful

        Raises:
            AppBaseException: If token is invalid, expired, or already used
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
                WHERE id = :token_id
            """)

            await self.db.execute(update_token_sql, {
                "token_id": verification_token.id,
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
                    await email_service.send_welcome_email(email, user.display_name)
                    logger.info(f"Welcome email sent to: {email}")
            except Exception as e:
                logger.error(f"Failed to send welcome email to {email}: {str(e)}")

            logger.info(f"Email verification successful for: {email}")
            return True
            
        except AppBaseException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during email verification: {str(e)}")
            raise AppBaseException(message="Email verification failed due to internal error", error_code=AUTH_INVALID_CREDENTIALS)

    async def initiate_password_reset(self, email: str) -> bool:
        """
        Initiate password reset process by sending reset token

        Args:
            email: User's email address

        Returns:
            True if reset token sent successfully

        Raises:
            AppBaseException: If user not found or email sending fails
        """
        try:
            user = await self.get_user_by_email(email)
            if not user:
                return True

            reset_token = email_service.generate_verification_token()

            token_sql = text("""
                INSERT INTO verification_tokens (id, email, token, token_type, expires_at, is_used, created_at)
                VALUES (:id, :email, :token, :token_type, :expires_at, :is_used, :created_at)
                RETURNING *
            """)

            current_time = datetime.now(timezone.utc).replace(tzinfo=None)
            token_params = {
                "id": str(uuid.uuid4()),
                "email": email,
                "token": reset_token,
                "token_type": "password_reset",
                "expires_at": current_time + timedelta(hours=1),
                "is_used": False,
                "created_at": current_time
            }

            await self.db.execute(token_sql, token_params)
            await self.db.commit()

            try:
                await email_service.send_password_reset_email(email, reset_token)
                logger.info(f"Password reset email sent to: {email}")
            except Exception as e:
                logger.error(f"Failed to send password reset email to {email}: {str(e)}")
                raise AppBaseException(message="Failed to send password reset email", error_code=AUTH_INVALID_CREDENTIALS)

            return True
            
        except AppBaseException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during password reset initiation: {str(e)}")
            raise AppBaseException(message="Password reset initiation failed due to internal error", error_code=AUTH_INVALID_CREDENTIALS)

    async def reset_password(self, email: str, token: str, new_password: str) -> bool:
        """
        Reset user password using verification token

        Args:
            email: User's email
            token: Password reset token
            new_password: New password

        Returns:
            True if password reset successful

        Raises:
            AppBaseException: If token is invalid, expired, already used, or password is weak
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
                WHERE id = :token_id
            """)

            await self.db.execute(update_token_sql, {
                "token_id": verification_token.id,
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
        """Resend verification email to user."""
        try:
            user = await self.get_user_by_email(email)
            if not user:

                return True
            
            if user.is_verified:
                return True
            
            verification_token = email_service.generate_verification_token()
            
            token_sql = text("""
                INSERT INTO verification_tokens (id, email, token, token_type, expires_at, is_used, created_at)
                VALUES (:id, :email, :token, :token_type, :expires_at, :is_used, :created_at)
            """)
            
            current_time = datetime.now(timezone.utc).replace(tzinfo=None)
            token_params = {
                "id": str(uuid.uuid4()),
                "email": email,
                "token": verification_token,
                "token_type": "email_verification",
                "expires_at": current_time + timedelta(hours=24),
                "is_used": False,
                "created_at": current_time
            }
            
            await self.db.execute(token_sql, token_params)
            await self.db.commit()
            
            try:
                await email_service.send_verification_email(email, verification_token)
                logger.info(f"Verification email resent to: {email}")
                return True
            except Exception as e:
                logger.error(f"Failed to resend verification email to {email}: {str(e)}")
                raise AppBaseException(message="Failed to send verification email", error_code=AUTH_INVALID_CREDENTIALS)
                
        except AppBaseException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during resend verification: {str(e)}")
            raise AppBaseException(message="Resend verification failed due to internal error", error_code=AUTH_INVALID_CREDENTIALS)