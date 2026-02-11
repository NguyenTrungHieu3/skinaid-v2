from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select, desc, and_, or_, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models.user import User
from app.modules.audit.models.audit_log import AuditLog
from app.modules.admin.models.audit_log import AdminAuditLog
from app.modules.ai.models.wound_analysis import WoundAnalysis
from app.modules.ai.models.wound_detection import WoundDetection


class StatisticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_total_users(self, start_date: datetime) -> int:
        query = select(func.count()).select_from(
            User).where(User.is_active == True)

        if start_date != datetime.min:
            query = query.where(User.created_at >= start_date)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_new_users(self, start_date: datetime, end_date: datetime) -> int:
        query = select(func.count()).select_from(User).where(
            User.is_active == True,
            User.created_at >= start_date,
            User.created_at < end_date
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_total_uploads(self, start_date: datetime) -> int:
        query = select(func.count()).select_from(AuditLog).where(
            AuditLog.action.in_(['image_upload', 'upload_image']),
            AuditLog.success == True
        )

        if start_date != datetime.min:
            query = query.where(AuditLog.timestamp >= start_date)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_uploads_in_range(self, start_date: datetime, end_date: datetime) -> int:
        query = select(func.count()).select_from(AuditLog).where(
            AuditLog.action.in_(['image_upload', 'upload_image']),
            AuditLog.success == True,
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp < end_date
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_analyzed_images(self, start_date: datetime) -> int:
        query = select(func.count()).select_from(WoundAnalysis).where(
            WoundAnalysis.is_deleted == False
        )

        if start_date != datetime.min:
            query = query.where(WoundAnalysis.analyzed_at >= start_date)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_total_detections(self, start_date: datetime) -> int:
        query = select(func.count()).select_from(WoundDetection).join(
            WoundAnalysis, WoundDetection.analysis_id == WoundAnalysis.analysis_id
        ).where(
            WoundAnalysis.is_deleted == False
        )

        if start_date != datetime.min:
            query = query.where(WoundAnalysis.analyzed_at >= start_date)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_detections_in_range(self, start_date: datetime, end_date: datetime) -> int:
        query = select(func.count()).select_from(WoundDetection).join(
            WoundAnalysis, WoundDetection.analysis_id == WoundAnalysis.analysis_id
        ).where(
            WoundAnalysis.is_deleted == False,
            WoundAnalysis.analyzed_at >= start_date,
            WoundAnalysis.analyzed_at < end_date
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_severe_detections(self, start_date: datetime) -> int:
        query = select(func.count()).select_from(WoundDetection).join(
            WoundAnalysis, WoundDetection.analysis_id == WoundAnalysis.analysis_id
        ).where(
            WoundAnalysis.is_deleted == False,
            func.lower(WoundDetection.severity) == 'severe'
        )

        if start_date != datetime.min:
            query = query.where(WoundAnalysis.analyzed_at >= start_date)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_avg_confidence(self, start_date: datetime, end_date: datetime = None) -> float:
        query = select(func.avg(WoundDetection.confidence_score)).select_from(WoundDetection).join(
            WoundAnalysis, WoundDetection.analysis_id == WoundAnalysis.analysis_id
        ).where(
            WoundAnalysis.is_deleted == False
        )

        if start_date != datetime.min:
            query = query.where(WoundAnalysis.analyzed_at >= start_date)

        if end_date:
            query = query.where(WoundAnalysis.analyzed_at < end_date)

        result = await self.db.execute(query)
        return result.scalar() or 0.0

    async def get_high_confidence_count(self, start_date: datetime, threshold: float = 0.8) -> int:
        query = select(func.count()).select_from(WoundDetection).join(
            WoundAnalysis, WoundDetection.analysis_id == WoundAnalysis.analysis_id
        ).where(
            WoundAnalysis.is_deleted == False,
            WoundDetection.confidence_score > threshold
        )

        if start_date != datetime.min:
            query = query.where(WoundAnalysis.analyzed_at >= start_date)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_wound_type_distribution(self, start_date: datetime) -> List[Tuple[str, int]]:
        query = select(
            WoundDetection.wound_type,
            func.count().label('count')
        ).select_from(WoundDetection).join(
            WoundAnalysis, WoundDetection.analysis_id == WoundAnalysis.analysis_id
        ).where(
            WoundAnalysis.is_deleted == False
        ).group_by(
            WoundDetection.wound_type
        ).order_by(
            desc('count')
        )

        if start_date != datetime.min:
            query = query.where(WoundAnalysis.analyzed_at >= start_date)

        result = await self.db.execute(query)
        return result.fetchall()

    async def get_daily_uploads(self, start_date: datetime) -> List[Tuple[Any, int]]:
        # Casting timestamp to Date for grouping
        date_col = cast(AuditLog.timestamp, Date).label('date')
        query = select(
            date_col,
            func.count().label('uploads')
        ).select_from(AuditLog).where(
            AuditLog.action.in_(['image_upload', 'upload_image']),
            AuditLog.success == True,
            AuditLog.timestamp >= start_date
        ).group_by(
            date_col
        ).order_by(
            date_col.asc()
        )

        result = await self.db.execute(query)
        return result.fetchall()

    async def get_daily_analyses(self, start_date: datetime) -> List[Tuple[Any, int]]:
        date_col = cast(WoundAnalysis.analyzed_at, Date).label('date')
        query = select(
            date_col,
            func.count().label('analyses')
        ).select_from(WoundAnalysis).where(
            WoundAnalysis.analyzed_at >= start_date,
            WoundAnalysis.is_deleted == False
        ).group_by(
            date_col
        ).order_by(
            date_col.asc()
        )

        result = await self.db.execute(query)
        return result.fetchall()

    async def get_recent_admin_logs(self, limit: int) -> List[Any]:
        # Return full objects or specific columns? Original returned columns.
        # Original: created_at, action, resource_type, resource_id, admin_email, status, error_message, description
        query = select(
            AdminAuditLog.created_at,
            AdminAuditLog.action,
            AdminAuditLog.resource_type,
            AdminAuditLog.resource_id,
            AdminAuditLog.admin_email,
            AdminAuditLog.status,
            AdminAuditLog.error_message,
            AdminAuditLog.description
        ).order_by(
            AdminAuditLog.created_at.desc()
        ).limit(limit)

        result = await self.db.execute(query)
        return result.fetchall()

    async def get_recent_failed_uploads(self, limit: int) -> List[Any]:
        query = select(
            AuditLog.timestamp,
            AuditLog.error_message,
            AuditLog.user_id
        ).where(
            AuditLog.action.in_(['image_upload', 'upload_image']),
            AuditLog.success == False
        ).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit)

        result = await self.db.execute(query)
        return result.fetchall()

    async def get_recent_analyses(self, limit: int) -> List[Any]:
        query = select(
            WoundAnalysis.analyzed_at,
            WoundAnalysis.ai_model_version,
            WoundAnalysis.total_detections
        ).where(
            WoundAnalysis.is_deleted == False
        ).order_by(
            WoundAnalysis.analyzed_at.desc()
        ).limit(limit)

        result = await self.db.execute(query)
        return result.fetchall()

    async def get_unresolved_errors_count(self) -> int:
        # 24 hours ago
        one_day_ago = datetime.now() - timedelta(hours=24)

        # AuditLog count
        audit_query = select(func.count()).select_from(AuditLog).where(
            AuditLog.action.in_(['image_upload', 'upload_image']),
            AuditLog.success == False,
            AuditLog.timestamp >= one_day_ago
        )
        audit_count = (await self.db.execute(audit_query)).scalar() or 0

        # AdminAuditLog count
        admin_query = select(func.count()).select_from(AdminAuditLog).where(
            AdminAuditLog.status.in_(['error', 'failed']),
            AdminAuditLog.created_at >= one_day_ago
        )
        admin_count = (await self.db.execute(admin_query)).scalar() or 0

        return audit_count + admin_count

    async def get_severity_distribution(self, start_date: datetime) -> List[Tuple[str, int]]:
        query = select(
            func.lower(WoundDetection.severity).label('severity_level'),
            func.count().label('count')
        ).select_from(WoundDetection).join(
            WoundAnalysis, WoundDetection.analysis_id == WoundAnalysis.analysis_id
        ).where(
            WoundAnalysis.is_deleted == False
        ).group_by(
            func.lower(WoundDetection.severity)
        ).order_by(
            desc('count')
        )

        if start_date != datetime.min:
            query = query.where(WoundAnalysis.analyzed_at >= start_date)

        result = await self.db.execute(query)
        return result.fetchall()
