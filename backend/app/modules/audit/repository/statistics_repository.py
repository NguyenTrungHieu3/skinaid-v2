from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select, desc, and_, or_, cast, Date, true, false
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models.user import User
from app.modules.audit.models.audit_log import AuditLog
from app.modules.ai.models.analysis import Analysis
from app.modules.ai.models.detection import Detection


class StatisticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_total_users(self, start_date: datetime) -> int:
        query = select(func.count()).select_from(User).where(User.is_active == true())
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
        query = select(func.count()).select_from(Analysis)
        if start_date != datetime.min:
            query = query.where(Analysis.created_at >= start_date)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_total_detections(self, start_date: datetime) -> int:
        query = select(func.count()).select_from(Detection).join(
            Analysis, Detection.analysis_id == Analysis.analysis_id
        )
        if start_date != datetime.min:
            query = query.where(Analysis.created_at >= start_date)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_detections_in_range(self, start_date: datetime, end_date: datetime) -> int:
        query = select(func.count()).select_from(Detection).join(
            Analysis, Detection.analysis_id == Analysis.analysis_id
        ).where(
            Analysis.created_at >= start_date,
            Analysis.created_at < end_date
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_severe_detections(self, start_date: datetime) -> int:
        query = select(func.count()).select_from(Detection).join(
            Analysis, Detection.analysis_id == Analysis.analysis_id
        ).where(
            func.lower(Detection.severity) == 'severe'
        )
        if start_date != datetime.min:
            query = query.where(Analysis.created_at >= start_date)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_avg_confidence(self, start_date: datetime, end_date: datetime = None) -> float:
        query = select(func.avg(Detection.confidence)).select_from(Detection).join(
            Analysis, Detection.analysis_id == Analysis.analysis_id
        )
        if start_date != datetime.min:
            query = query.where(Analysis.created_at >= start_date)
        if end_date:
            query = query.where(Analysis.created_at < end_date)
        result = await self.db.execute(query)
        return result.scalar() or 0.0

    async def get_high_confidence_count(self, start_date: datetime, threshold: float = 0.8) -> int:
        query = select(func.count()).select_from(Detection).join(
            Analysis, Detection.analysis_id == Analysis.analysis_id
        ).where(
            Detection.confidence > threshold
        )
        if start_date != datetime.min:
            query = query.where(Analysis.created_at >= start_date)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_wound_type_distribution(self, start_date: datetime) -> List[Tuple[str, int]]:
        query = select(
            Detection.wound_type,
            func.count().label('count')
        ).select_from(Detection).join(
            Analysis, Detection.analysis_id == Analysis.analysis_id
        ).group_by(
            Detection.wound_type
        ).order_by(desc('count'))
        if start_date != datetime.min:
            query = query.where(Analysis.created_at >= start_date)
        result = await self.db.execute(query)
        return result.fetchall()

    async def get_daily_uploads(self, start_date: datetime) -> List[Tuple[Any, int]]:
        date_col = cast(AuditLog.timestamp, Date).label('date')
        query = select(date_col, func.count().label('uploads')).select_from(AuditLog).where(
            AuditLog.action.in_(['image_upload', 'upload_image']),
            AuditLog.success == True,
            AuditLog.timestamp >= start_date
        ).group_by(date_col).order_by(date_col.asc())
        result = await self.db.execute(query)
        return result.fetchall()

    async def get_daily_analyses(self, start_date: datetime) -> List[Tuple[Any, int]]:
        date_col = cast(Analysis.created_at, Date).label('date')
        query = select(date_col, func.count().label('analyses')).select_from(Analysis).where(
            Analysis.created_at >= start_date
        ).group_by(date_col).order_by(date_col.asc())
        result = await self.db.execute(query)
        return result.fetchall()

    async def get_recent_admin_logs(self, limit: int) -> List[Any]:
        """Get recent admin logs from AuditLog table (admin info stored in details JSONB)."""
        query = select(
            AuditLog.timestamp,
            AuditLog.action,
            AuditLog.resource_type,
            AuditLog.resource_id,
            AuditLog.details,
            AuditLog.success,
            AuditLog.error_message
        ).where(
            AuditLog.details.op('->>')('admin_role').isnot(None)
        ).order_by(AuditLog.timestamp.desc()).limit(limit)
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
        ).order_by(AuditLog.timestamp.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.fetchall()

    async def get_recent_analyses(self, limit: int) -> List[Any]:
        query = select(
            Analysis.created_at,
            func.count(Detection.detection_id).label('total_detections')
        ).outerjoin(
            Detection, Detection.analysis_id == Analysis.analysis_id
        ).group_by(
            Analysis.analysis_id, Analysis.created_at
        ).order_by(
            Analysis.created_at.desc()
        ).limit(limit)
        result = await self.db.execute(query)
        return result.fetchall()

    async def get_unresolved_errors_count(self) -> int:
        one_day_ago = datetime.now() - timedelta(hours=24)
        audit_query = select(func.count()).select_from(AuditLog).where(
            AuditLog.action.in_(['image_upload', 'upload_image']),
            AuditLog.success == False,
            AuditLog.timestamp >= one_day_ago
        )
        audit_count = (await self.db.execute(audit_query)).scalar() or 0
        admin_query = select(func.count()).select_from(AuditLog).where(
            AuditLog.details.op('->>')('admin_role').isnot(None),
            AuditLog.success == False,
            AuditLog.timestamp >= one_day_ago
        )
        admin_count = (await self.db.execute(admin_query)).scalar() or 0
        return audit_count + admin_count

    async def get_severity_distribution(self, start_date: datetime) -> List[Tuple[str, int]]:
        query = select(
            func.lower(Detection.severity).label('severity_level'),
            func.count().label('count')
        ).select_from(Detection).join(
            Analysis, Detection.analysis_id == Analysis.analysis_id
        ).group_by(
            func.lower(Detection.severity)
        ).order_by(desc('count'))
        if start_date != datetime.min:
            query = query.where(Analysis.created_at >= start_date)
        result = await self.db.execute(query)
        return result.fetchall()
