"""
Profile Module

This module handles user profile management including:
- Profile CRUD operations
- Avatar management
- Personal information updates
- Profile privacy settings
"""

from .models import UserProfile
from .services import ProfileService
from .controllers import ProfileController
from .schemas import UserProfileResponse, UserProfileUpdate, UserProfileBase
from .routes import router

__all__ = [
    "UserProfile",
    "ProfileService",
    "ProfileController",
    "UserProfileResponse",
    "UserProfileUpdate",
    "UserProfileBase",
    "router"
]
