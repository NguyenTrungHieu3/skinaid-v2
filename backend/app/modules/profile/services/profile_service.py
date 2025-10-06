from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text
from typing import Optional
import uuid
import logging
from datetime import datetime, timezone

from app.modules.profile.models.user_profile import UserProfile
from app.modules.profile.schemas.user_profile import UserProfileUpdate, UserProfileResponse
from app.utils.exceptions.base_exceptions import AppBaseException
from app.utils.constants.error_codes import USER_INVALID_DATA, USER_NOT_FOUND

logger = logging.getLogger(__name__)

class ProfileService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_profile_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """
        Lấy profile của user theo user_id
        
        Args:
            user_id: ID của user
            
        Returns:
            UserProfile object hoặc None nếu không tìm thấy
        """
        try:
            # Convert to string if it's a UUID object
            if isinstance(user_id, uuid.UUID):
                user_id = str(user_id)
                
            sql = text("""
                SELECT * FROM user_profiles 
                WHERE user_id = :user_id
            """)
            
            result = await self.db.execute(sql, {"user_id": user_id})
            row = result.mappings().first()
            
            if row is None:
                return None
                
            return UserProfile.model_validate(dict(row))
            
        except Exception as e:
            logger.error(f"Error getting profile by user_id {user_id}: {str(e)}")
            return None
    
    async def update_profile(self, user_id: str, profile_data: UserProfileUpdate) -> UserProfile:
        """
        Cập nhật thông tin profile của user
        
        Args:
            user_id: ID của user
            profile_data: Dữ liệu profile cần cập nhật
            
        Returns:
            UserProfile object đã được cập nhật
            
        Raises:
            AppBaseException: Nếu user không tồn tại hoặc dữ liệu không hợp lệ
        """
        try:
            # Convert to string if it's a UUID object
            if isinstance(user_id, uuid.UUID):
                user_id = str(user_id)
            
            existing_profile = await self.get_profile_by_user_id(user_id)
            
            update_data = {}
            if profile_data.full_name is not None:
                update_data["full_name"] = profile_data.full_name
            if profile_data.phone is not None:
                update_data["phone"] = profile_data.phone
            if profile_data.date_of_birth is not None:
                update_data["date_of_birth"] = profile_data.date_of_birth
            if profile_data.gender is not None:
                update_data["gender"] = profile_data.gender
            if profile_data.address is not None:
                update_data["address"] = profile_data.address
            if profile_data.avatar_url is not None:
                update_data["avatar_url"] = profile_data.avatar_url
            
            if not update_data:
                if existing_profile:
                    return existing_profile
                else:
                    raise AppBaseException(message="Profile not found", error_code=USER_NOT_FOUND)
            
            update_data["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
            
            if existing_profile:
                update_parts = [f"{key} = :{key}" for key in update_data.keys()]
                update_data["user_id"] = user_id
                
                sql = text(f"""
                    UPDATE user_profiles 
                    SET {', '.join(update_parts)}
                    WHERE user_id = :user_id
                    RETURNING *
                """)
                
                result = await self.db.execute(sql, update_data)
                await self.db.commit()
                
            else:
                profile_id = str(uuid.uuid4())
                current_time = datetime.now(timezone.utc).replace(tzinfo=None)
                
                insert_data = {
                    "id": profile_id,
                    "user_id": user_id,
                    "created_at": current_time,
                    "updated_at": current_time,
                    **update_data
                }
                
                insert_data["updated_at"] = current_time
                
                columns = list(insert_data.keys())
                placeholders = [f":{col}" for col in columns]
                
                sql = text(f"""
                    INSERT INTO user_profiles ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                    RETURNING *
                """)
                
                result = await self.db.execute(sql, insert_data)
                await self.db.commit()
            
            row = result.mappings().first()
            if row is None:
                raise AppBaseException(message="Failed to update profile", error_code=USER_INVALID_DATA)
                
            return UserProfile.model_validate(dict(row))
            
        except AppBaseException:
            raise
        except Exception as e:
            logger.error(f"Error updating profile for user {user_id}: {str(e)}")
            raise AppBaseException(message="Failed to update profile due to internal error", error_code=USER_INVALID_DATA)
    
    async def create_profile_response(self, profile: UserProfile) -> UserProfileResponse:
        """
        Tạo UserProfileResponse từ UserProfile model
        
        Args:
            profile: UserProfile object
            
        Returns:
            UserProfileResponse object
        """
        return UserProfileResponse(
            full_name=profile.full_name,
            phone=profile.phone,
            date_of_birth=profile.date_of_birth,
            gender=profile.gender,
            address=profile.address,
            avatar_url=profile.avatar_url
        )