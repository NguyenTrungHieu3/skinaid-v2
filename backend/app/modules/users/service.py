from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.modules.users.schemas import (
    UserListResponse,
    UserListItem,
    UserDetailResponse,
    UpdateUserStatusRequest,
    UpdateUserStatusResponse,
    ScanHistoryItem
)
from app.modules.users.repository import UserRepository
from app.modules.users.exceptions import UserManagementNotFoundError
from app.shared.exceptions import BadRequestError
from app.modules.audit.services.audit_service import AuditService


def _best_active_at(user: User) -> Optional[datetime]:
    """Lấy mốc thời gian hoạt động mới nhất có thể xác định được."""
    candidates = [
        ts for ts in [user.last_active_at, user.last_login_at]
        if ts is not None
    ]
    return max(candidates) if candidates else None

class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
        self.db = db

    async def get_users(
        self,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None
    ) -> UserListResponse:
        
        users, total = await self.repository.get_users_list(
            page=page, page_size=page_size, search=search, role=role, status=status
        )

        items = []
        for user in users:
            upload_count = await self.repository.get_user_upload_count(user.user_id)
            roles = [ur.role.role_name for ur in user.user_roles if ur.role]
            main_role = roles[0] if roles else "user"
            
            items.append(UserListItem(
                id=str(user.user_id),
                full_name=user.profile.full_name if user.profile else None,
                email=user.email,
                role=main_role,
                status="active" if user.is_active else "inactive",
                uploads_count=upload_count,
                join_date=user.created_at,
                last_active_at=_best_active_at(user)
            ))

        return UserListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )

    async def get_user_detail(self, user_id: UUID) -> Optional[UserDetailResponse]:
        user = await self.repository.get_user_detail(user_id)
        if not user:
            return None

        upload_count = await self.repository.get_user_upload_count(user.user_id)
        roles = [ur.role.role_name for ur in user.user_roles if ur.role]
        main_role = roles[0] if roles else "user"
        
        history = await self.repository.get_scan_history(user.user_id)
        
        history_items = []
        for item in history:
            wound_type = item.wound_type
            severity = item.severity
            
            # Fallback to the first detection if analysis level fields are empty
            if not wound_type and getattr(item, 'wound_detections', None):
                if len(item.wound_detections) > 0:
                    wound_type = item.wound_detections[0].wound_type
                    severity = item.wound_detections[0].severity

            history_items.append(
                ScanHistoryItem(
                    id=item.analysis_id,
                    created_at=item.created_at,
                    wound_type=wound_type,
                    severity=severity,
                    image_url=item.image_url
                )
            )

        return UserDetailResponse(
            id=str(user.user_id),
            full_name=user.profile.full_name if user.profile else None,
            email=user.email,
            role=main_role,
            status="active" if user.is_active else "inactive",
            uploads_count=upload_count,
            join_date=user.created_at,
            last_active_at=_best_active_at(user),
            scan_history=history_items
        )

    async def update_user_status(
        self,
        user_id: UUID,
        status_data: UpdateUserStatusRequest,
        current_admin: User,
        audit_service: AuditService,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UpdateUserStatusResponse:
        
        target_user = await self.repository.get_user_detail(user_id)
        if not target_user:
            raise UserManagementNotFoundError(message=f"Không tìm thấy user {user_id}")

        if target_user.user_id == current_admin.user_id and status_data.status == "inactive":
            raise BadRequestError(message="Không thể tự vô hiệu hóa tài khoản của chính mình.")

        is_active_target = status_data.status == "active"
        
        if not is_active_target:
            roles = [ur.role.role_name for ur in target_user.user_roles if ur.role]
            if "admin" in roles:
                active_admins = await self.repository.count_active_admins()
                if active_admins <= 1:
                    raise BadRequestError(message="Không thể vô hiệu hóa admin cuối cùng của hệ thống.")

        before_status = "active" if target_user.is_active else "inactive"
        after_status = status_data.status

        target_user.is_active = is_active_target
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        target_user.updated_at = current_time
        
        await self.db.commit()
        await self.db.refresh(target_user)

        # Ghi log Audit Backbone
        base_action = "activate_user" if is_active_target else "deactivate_user"
        await audit_service.log_event(
            action=base_action,
            user_id=current_admin.user_id,
            success=True,
            resource_type="user",
            resource_id=str(target_user.user_id),
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "target_email": target_user.email,
                "before": before_status,
                "after": after_status,
                "reason": status_data.reason if hasattr(status_data, 'reason') else "Admin changed status"
            }
        )

        return UpdateUserStatusResponse(
            id=str(target_user.user_id),
            status="active" if target_user.is_active else "inactive",
            updated_at=target_user.updated_at or current_time
        )
