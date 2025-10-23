from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, UUID
from typing import Optional, Dict, Any, List
import uuid
import logging
from datetime import datetime, timezone

from app.modules.profile.models.user_profile import UserProfile
from app.modules.profile.schemas.user_profile_schemas import UserProfileUpdate, UserProfileResponse, ProfileStatisticsResponse
from app.utils.exceptions.base_exceptions import AppBaseException
from app.utils.constants.error_codes import USER_INVALID_DATA, USER_NOT_FOUND

logger = logging.getLogger(__name__)

class ProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_profile_by_user_id(self, user_id: uuid.UUID) -> Optional[UserProfile]:
        """
        Lấy profile của user theo user_id

        Args:
            user_id: ID của user

        Returns:
            UserProfile object hoặc None nếu không tìm thấy
        """
        try:
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
    
    async def update_profile(self, user_id: uuid.UUID, profile_data: UserProfileUpdate) -> UserProfile:
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

            current_time = datetime.now(timezone.utc).replace(tzinfo=None)

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
                current_time = datetime.now(timezone.utc).replace(tzinfo=None)

                insert_data = {
                    "user_id": user_id,
                    "created_at": current_time,
                    "updated_at": current_time,
                    **update_data
                }

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
    
    async def create_profile_response(self, profile) -> UserProfileResponse:
        """
        Tạo UserProfileResponse từ UserProfile model

        Args:
            profile: UserProfile object

        Returns:
            UserProfileResponse object
        """
        return UserProfileResponse(**profile.to_response_dict())

    async def get_profile_statistics(self) -> ProfileStatisticsResponse:
        """Lấy thống kê về user profiles."""
        try:
            # Tổng số users
            total_sql = "SELECT COUNT(*) as total FROM users"
            total_result = await self.db.execute(total_sql)
            total_users = total_result.scalar()

            # Users có profile
            profile_sql = "SELECT COUNT(DISTINCT user_id) as with_profile FROM user_profiles"
            profile_result = await self.db.execute(profile_sql)
            users_with_profile = profile_result.scalar()

            # Profiles hoàn chỉnh
            complete_sql = """
                SELECT COUNT(*) as complete FROM user_profiles
                WHERE full_name IS NOT NULL
                AND phone IS NOT NULL
                AND date_of_birth IS NOT NULL
                AND gender IS NOT NULL
            """
            complete_result = await self.db.execute(complete_sql)
            complete_profiles = complete_result.scalar()

            # Phân bố theo giới tính
            gender_sql = """
                SELECT gender, COUNT(*) as count FROM user_profiles
                WHERE gender IS NOT NULL
                GROUP BY gender
            """
            gender_result = await self.db.execute(gender_sql)
            gender_distribution = {row.gender: row.count for row in gender_result}

            # Phân bố theo độ tuổi
            age_sql = """
                SELECT
                    CASE
                        WHEN age < 18 THEN 'under_18'
                        WHEN age BETWEEN 18 AND 25 THEN '18_25'
                        WHEN age BETWEEN 26 AND 35 THEN '26_35'
                        WHEN age BETWEEN 36 AND 50 THEN '36_50'
                        WHEN age > 50 THEN 'over_50'
                        ELSE 'unknown'
                    END as age_group,
                    COUNT(*) as count
                FROM (
                    SELECT
                        EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth)) as age
                    FROM user_profiles
                    WHERE date_of_birth IS NOT NULL
                ) age_data
                GROUP BY age_group
            """
            age_result = await self.db.execute(age_sql)
            age_distribution = {row.age_group: row.count for row in age_result}

            return ProfileStatisticsResponse(
                total_users=total_users,
                users_with_profile=users_with_profile,
                complete_profiles=complete_profiles,
                average_completion=(complete_profiles / users_with_profile * 100) if users_with_profile > 0 else 0,
                gender_distribution=gender_distribution,
                age_distribution=age_distribution
            )

        except Exception as e:
            logger.error(f"Failed to get profile statistics: {e}")
            return ProfileStatisticsResponse(
                total_users=0,
                users_with_profile=0,
                complete_profiles=0,
                average_completion=0,
                gender_distribution={},
                age_distribution={}
            )

    async def search_profiles(
        self,
        full_name: Optional[str] = None,
        gender: Optional[str] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[UserProfile]:
        """Tìm kiếm profiles với bộ lọc."""
        try:
            where_conditions = []
            params = {"limit": limit, "offset": offset}

            if full_name:
                where_conditions.append("full_name ILIKE :full_name")
                params["full_name"] = f"%{full_name}%"

            if gender:
                where_conditions.append("gender = :gender")
                params["gender"] = gender

            if min_age is not None:
                where_conditions.append("EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth)) >= :min_age")
                params["min_age"] = min_age

            if max_age is not None:
                where_conditions.append("EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth)) <= :max_age")
                params["max_age"] = max_age

            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            sql = f"""
                SELECT * FROM user_profiles
                {where_clause}
                ORDER BY updated_at DESC
                LIMIT :limit OFFSET :offset
            """

            result = await self.db.execute(sql, params)
            rows = result.fetchall()

            profiles = []
            for row in rows:
                profile = UserProfile(
                    user_id=row.user_id,
                    full_name=row.full_name,
                    phone=row.phone,
                    date_of_birth=row.date_of_birth,
                    gender=row.gender,
                    address=row.address,
                    avatar_url=row.avatar_url,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                profiles.append(profile)

            return profiles

        except Exception as e:
            logger.error(f"Failed to search profiles: {e}")
            return []

    async def get_profile_completion_suggestions(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Gợi ý các trường cần điền để hoàn thiện profile."""
        try:
            profile = await self.get_profile_by_user_id(user_id)
            if not profile:
                return {"suggestions": [], "missing_fields": []}

            missing_fields = []
            suggestions = []

            if not profile.full_name:
                missing_fields.append("full_name")
                suggestions.append("Thêm họ tên đầy đủ để cá nhân hóa trải nghiệm")

            if not profile.phone:
                missing_fields.append("phone")
                suggestions.append("Thêm số điện thoại để hỗ trợ liên hệ")

            if not profile.date_of_birth:
                missing_fields.append("date_of_birth")
                suggestions.append("Thêm ngày sinh để phân tích sức khỏe tốt hơn")

            if not profile.gender:
                missing_fields.append("gender")
                suggestions.append("Thêm giới tính để nhận gợi ý phù hợp")

            if not profile.address:
                missing_fields.append("address")
                suggestions.append("Thêm địa chỉ để hỗ trợ dịch vụ địa phương")

            if not profile.avatar_url:
                missing_fields.append("avatar_url")
                suggestions.append("Thêm ảnh đại diện để cá nhân hóa profile")

            return {
                "missing_fields": missing_fields,
                "suggestions": suggestions,
                "current_completion": profile.profile_completion_percentage,
                "target_completion": 100
            }

        except Exception as e:
            logger.error(f"Failed to get completion suggestions for {user_id}: {e}")
            return {"suggestions": [], "missing_fields": []}