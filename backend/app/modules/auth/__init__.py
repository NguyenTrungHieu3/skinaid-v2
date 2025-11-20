from .models.user import User
from .models.verification_token import VerificationToken
from .models.roles import Role
from .models.permissions import Permission
from .models.user_roles import UserRole
from .models.role_permissions import RolePermission

# Dịch vụ
from .services.auth_service import AuthService
from .services.user_service import UserService

# Controllers
from .controllers.auth_controller import AuthController

# Schemas
from .schemas.user_schemas import (
    UserBase, UserCreate, UserLogin, UserResponse,
    PasswordResetRequest, PasswordResetConfirm, PasswordResetResponse,
    ChangePasswordRequest, ChangePasswordResponse,
    # EmailVerificationRequest, EmailVerificationResponse
)

# Routes
from .routes.auth_router import router as auth_router

__all__ = [
    "User", "VerificationToken",
    "Role", "Permission", "UserRole", "RolePermission",

    "AuthService", "UserService",

    "AuthController",

    "UserBase", "UserCreate", "UserLogin", "UserResponse",
    "PasswordResetRequest", "PasswordResetConfirm", "PasswordResetResponse",
    "ChangePasswordRequest", "ChangePasswordResponse",
    # "EmailVerificationRequest", "EmailVerificationResponse",

    "auth_router"
]