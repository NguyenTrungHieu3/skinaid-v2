# Admin Module - Dashboard and System Management
"""
Admin module cung cấp các API cho admin dashboard
- Dashboard overview statistics
- Wound type distribution
- Weekly activity tracking
- System logs monitoring
- User Management
"""

from app.modules.admin.services.admin_audit_service import AdminAuditService
from app.modules.admin.services.admin_user_service import AdminUserService
from app.modules.admin.services.statistics_service import StatisticsService

__all__ = ["AdminAuditService", "AdminUserService", "StatisticsService"]
