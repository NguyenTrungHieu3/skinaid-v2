from fastapi import HTTPException, status, UploadFile 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, Dict, Any, List
import uuid
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from app.modules.profile.models.user_profile import UserProfile
from app.modules.profile.schemas.user_profile_schemas import UserProfileUpdate, UserProfileResponse, ProfileStatisticsResponse
from app.utils.constants.error_codes import USER_INVALID_DATA, USER_NOT_FOUND
from app.shared.validators.file_validator import FileValidator
from app.shared.services.file_service import FileService

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
            logger.error(f"Lỗi khi lấy hồ sơ theo user_id {user_id}: {str(e)}")
            return None
    
    async def update_profile(
        self, 
        user_id: uuid.UUID, 
        profile_data: UserProfileUpdate
    ) -> UserProfile:
        """
        Cập nhật thông tin profile của user (SQL injection safe).
        
        Args:
            user_id: ID của user
            profile_data: Dữ liệu profile cần cập nhật
            
        Returns:
            UserProfile object đã được cập nhật
            
        Raises:
            HTTPException: Nếu user không tồn tại hoặc dữ liệu không hợp lệ
        """
        try:
            existing_profile = await self.get_profile_by_user_id(user_id)
            current_time = datetime.now(timezone.utc).replace(tzinfo=None)
            # Xây dựng dữ liệu cập nhật
            update_fields = {}
            if profile_data.full_name is not None:
                update_fields["full_name"] = profile_data.full_name
            if profile_data.phone is not None:
                update_fields["phone"] = profile_data.phone
            if profile_data.date_of_birth is not None:
                update_fields["date_of_birth"] = profile_data.date_of_birth
            if profile_data.gender is not None:
                update_fields["gender"] = profile_data.gender
            if profile_data.address is not None:
                update_fields["address"] = profile_data.address
            if profile_data.avatar_url is not None:
                update_fields["avatar_url"] = profile_data.avatar_url
            if not update_fields:
                if existing_profile:
                    return existing_profile
                else:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không tìm thấy hồ sơ")
            if existing_profile:
                set_clauses = []
                params = {"user_id": user_id, "updated_at": current_time}
                
                # Ánh xạ từng trường một cách rõ ràng
                if "full_name" in update_fields:
                    set_clauses.append("full_name = :full_name")
                    params["full_name"] = update_fields["full_name"]
                if "phone" in update_fields:
                    set_clauses.append("phone = :phone")
                    params["phone"] = update_fields["phone"]
                if "date_of_birth" in update_fields:
                    set_clauses.append("date_of_birth = :date_of_birth")
                    params["date_of_birth"] = update_fields["date_of_birth"]
                if "gender" in update_fields:
                    set_clauses.append("gender = :gender")
                    params["gender"] = update_fields["gender"]
                if "address" in update_fields:
                    set_clauses.append("address = :address")
                    params["address"] = update_fields["address"]
                if "avatar_url" in update_fields:
                    set_clauses.append("avatar_url = :avatar_url")
                    params["avatar_url"] = update_fields["avatar_url"]
                
                set_clauses.append("updated_at = :updated_at")
                
                sql = text(f"""
                    UPDATE user_profiles
                    SET {', '.join(set_clauses)}
                    WHERE user_id = :user_id
                    RETURNING *
                """)
                result = await self.db.execute(sql, params)
                await self.db.commit()
            else:
                # Tạo profile mới
                insert_data = {
                    "user_id": user_id,
                    "created_at": current_time,
                    "updated_at": current_time,
                    **update_fields
                }
                sql = text("""
                    INSERT INTO user_profiles (
                        user_id, full_name, phone, date_of_birth,
                        gender, address, avatar_url, created_at, updated_at
                    )
                    VALUES (
                        :user_id, :full_name, :phone, :date_of_birth,
                        :gender, :address, :avatar_url, :created_at, :updated_at
                    )
                    RETURNING *
                """)
                params = {
                    "user_id": insert_data.get("user_id"),
                    "full_name": insert_data.get("full_name"),
                    "phone": insert_data.get("phone"),
                    "date_of_birth": insert_data.get("date_of_birth"),
                    "gender": insert_data.get("gender"),
                    "address": insert_data.get("address"),
                    "avatar_url": insert_data.get("avatar_url"),
                    "created_at": insert_data.get("created_at"),
                    "updated_at": insert_data.get("updated_at"),
                }
                result = await self.db.execute(sql, params)
                await self.db.commit()
            row = result.mappings().first()
            if row is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể cập nhật hồ sơ")
            return UserProfile.model_validate(dict(row))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật hồ sơ cho user {user_id}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể cập nhật hồ sơ do lỗi nội bộ")
        
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
            logger.error(f"Không thể lấy thống kê hồ sơ: {e}")
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
            logger.error(f"Không thể tìm kiếm hồ sơ: {e}")
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
            logger.error(f"Không thể lấy gợi ý hoàn thiện cho {user_id}: {e}")
            return {"suggestions": [], "missing_fields": []}
    
    async def upload_avatar(
        self,
        user_id: uuid.UUID,
        file: UploadFile
    ) -> Dict[str, Any]:
        """
        Upload và lưu avatar cho user.

        Workflow:
        1. Xác minh user tồn tại trong database
        2. Validate file (loại, kích thước, đuôi mở rộng)
        3. Xóa avatar cũ nếu tồn tại (dọn dẹp)
        4. Lưu file mới vào storage
        5. Cập nhật avatar_url trong UserProfile
        6. Commit transaction và trả về dữ liệu response
        """
        logger.info(f"[UPLOAD_AVATAR] Bắt đầu upload avatar cho user: {user_id}")
        print(f"\n[DEBUG] upload_avatar được gọi cho {user_id}")

        # [STEP 1] Kiểm tra user có tồn tại không
        profile = await self.get_profile_by_user_id(user_id)
        if profile:
            print(f"[DEBUG] Tìm thấy hồ sơ. avatar_url: {profile.avatar_url} (type: {type(profile.avatar_url)})")
        else:
            print("[DEBUG] Không tìm thấy hồ sơ")

        if not profile:
            logger.warning(f"[UPLOAD_AVATAR] User {user_id} không tồn tại")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy user"
            )

        # [STEP 2] Validate file sử dụng FileValidator
        validation_result = await FileValidator.validate_upload_file(
            file=file,
            max_size=5 * 1024 * 1024,  
            allowed_types=['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        )

        if not validation_result['valid']:
            logger.warning(
                f"[UPLOAD_AVATAR] Validate file thất bại cho user {user_id}: "
                f"{validation_result['error']}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result['error']
            )

        # Lấy nội dung file và kích thước từ kết quả validation
        file_content = validation_result['content']
        file_size = validation_result['size']

        logger.debug(
            f"[UPLOAD_AVATAR] Validate file thành công - "
            f"Type: {validation_result['mime_type']}, Size: {file_size} bytes"
        )

        try:
            # [STEP 3] Xóa avatar cũ nếu tồn tại
            if profile.avatar_url:
                old_file_path = self._get_file_path_from_url_debug(profile.avatar_url)
                if old_file_path and os.path.exists(old_file_path):
                    logger.info(
                        f"[UPLOAD_AVATAR] Xóa avatar cũ: {old_file_path} "
                        f"for user {user_id}"
                    )
                    await FileService.delete_file(old_file_path)

            # [STEP 4] Lưu file mới vào storage
            file_result = await FileService.save_file(
                file_content=file_content,
                filename=file.filename,
                subfolder="avatars"  # Lưu vào /uploads/avatars/
            )

            logger.debug(
                f"[UPLOAD_AVATAR] Lưu file thành công - "
                f"URL: {file_result['file_url']}"
            )

            # [STEP 5] Cập nhật avatar_url trong UserProfile
            update_query = text("""
                UPDATE user_profiles
                SET avatar_url = :avatar_url,
                    updated_at = :updated_at
                WHERE user_id = :user_id
            """)

            current_time = datetime.now(timezone.utc).replace(tzinfo=None)

            await self.db.execute(
                update_query,
                {
                    "avatar_url": file_result["file_url"],
                    "updated_at": current_time,
                    "user_id": user_id
                }
            )

            # [STEP 6] Commit transaction
            await self.db.commit()

            logger.info(
                f"[UPLOAD_AVATAR] Upload avatar thành công cho user {user_id} - "
                f"URL: {file_result['file_url']}"
            )

            # Return response data
            return {
                "avatar_url": file_result["file_url"],
                "file_name": file_result["filename"],
                "file_size": file_size,
                "uploaded_at": current_time
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"[UPLOAD_AVATAR] Lỗi khi upload avatar cho user {user_id}",
                exc_info=True
            )
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi khi lưu avatar: {str(e)}"
            )

    async def delete_avatar(
        self,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Xóa avatar của user.

        Workflow:
        1. Xác minh user tồn tại
        2. Kiểm tra user có avatar hay không
        3. Xóa file từ storage
        4. Cập nhật avatar_url = NULL trong database
        5. Commit transaction và trả về xác nhận
        """
        logger.info(f"[DELETE_AVATAR] Bắt đầu xóa avatar cho user: {user_id}")

        # [STEP 1] Kiểm tra user có tồn tại không
        profile = await self.get_profile_by_user_id(user_id)
        if not profile:
            logger.warning(f"[DELETE_AVATAR] User {user_id} không tồn tại")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy user"
            )

        # [STEP 2] Kiểm tra user có avatar không
        if not profile.avatar_url:
            logger.warning(f"[DELETE_AVATAR] User {user_id} không có avatar")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User chưa có avatar để xóa"
            )

        try:
            # [STEP 3] Xóa file từ storage
            file_path = self._get_file_path_from_url_debug(profile.avatar_url)

            if file_path and os.path.exists(file_path):
                logger.info(f"[DELETE_AVATAR] Xóa file: {file_path}")
                file_deleted = await FileService.delete_file(file_path)

                if not file_deleted:
                    logger.warning(
                        f"[DELETE_AVATAR] Không thể xóa file {file_path}, "
                        f"nhưng vẫn tiếp tục cập nhật database"
                    )
            else:
                logger.warning(
                    f"[DELETE_AVATAR] File không tồn tại: {file_path}, "
                    f"chỉ update database"
                )

            # [STEP 4] Cập nhật avatar_url = NULL trong database
            update_query = text("""
                UPDATE user_profiles
                SET avatar_url = NULL,
                    updated_at = :updated_at
                WHERE user_id = :user_id
            """)

            current_time = datetime.now(timezone.utc).replace(tzinfo=None)

            await self.db.execute(
                update_query,
                {
                    "updated_at": current_time,
                    "user_id": user_id
                }
            )

            # [STEP 5] Commit transaction
            await self.db.commit()

            logger.info(f"[DELETE_AVATAR] Xóa avatar thành công cho user {user_id}")

            return {
                "deleted": True,
                "message": "Avatar đã được xóa thành công",
                "deleted_at": current_time
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"[DELETE_AVATAR] Lỗi khi xóa avatar cho user {user_id}",
                exc_info=True
            )
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi khi xóa avatar: {str(e)}"
            )


    async def get_public_avatar(
        self,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Lấy avatar của user (public endpoint - không cần authentication).

        Workflow:
        1. Truy vấn user profile từ database
        2. Trả về avatar_url và cờ has_avatar
        3. Không raise exception nếu user không tồn tại, trả về has_avatar=False
        """
        logger.debug(f"[GET_PUBLIC_AVATAR] Lấy avatar cho user: {user_id}")

        # [STEP 1] Query user profile
        profile = await self.get_profile_by_user_id(user_id)

        # [STEP 2] Xây dựng response
        if not profile:
            logger.debug(f"[GET_PUBLIC_AVATAR] User {user_id} không tồn tại")
            return {
                "user_id": user_id,
                "avatar_url": None,
                "has_avatar": False
            }

        logger.debug(
            f"[GET_PUBLIC_AVATAR] User {user_id} có avatar: "
            f"{bool(profile.avatar_url)}"
        )

        return {
            "user_id": user_id,
            "avatar_url": profile.avatar_url,
            "has_avatar": bool(profile.avatar_url)
        }


    def _get_file_path_from_url_debug(self, file_url: str) -> Optional[str]:
        """
        Chuyển đổi file URL thành đường dẫn file tuyệt đối
        """
        try:
            if not file_url:
                return None
            
            if not isinstance(file_url, str):
                logger.warning(f"[WARNING] file_url không phải là chuỗi: {file_url} (type: {type(file_url)})")
                return None

            relative_path = file_url.lstrip("/").removeprefix("uploads/")
            from app.core.config import settings
            absolute_path = Path(settings.UPLOAD_DIR) / relative_path

            return str(absolute_path)
        except Exception as e:
            logger.error(f"[ERROR] Lỗi trong _get_file_path_from_url: {e}", exc_info=True)
            # Re-raise với thông tin debug để thấy trong output test
            raise Exception(f"DEBUG_ERROR: file_url='{file_url}', type={type(file_url)}, error={e}")
