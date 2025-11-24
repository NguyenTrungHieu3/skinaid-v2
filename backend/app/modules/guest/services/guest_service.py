from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text
import uuid
from datetime import datetime, timedelta, timezone

from app.modules.guest.models.guest_session import GuestSession

class GuestService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_guest_session(self, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        expires_at = current_time + timedelta(hours=1)

        sql = text("""
            INSERT INTO guest_sessions (session_id, ip_address, user_agent, created_at, expires_at, last_activity_at, upload_count, analysis_count, is_active, is_converted_to_user)
            VALUES (:session_id, :ip_address, :user_agent, :created_at, :expires_at, :last_activity_at, :upload_count, :analysis_count, :is_active, :is_converted_to_user)
            RETURNING *,
                   CASE WHEN expires_at < (NOW() AT TIME ZONE 'UTC') THEN true ELSE false END as is_expired,
                   CASE WHEN expires_at >= (NOW() AT TIME ZONE 'UTC') AND is_active = true AND upload_count < 5 THEN true ELSE false END as can_upload,
                   CASE WHEN expires_at >= (NOW() AT TIME ZONE 'UTC') AND is_active = true AND analysis_count < 3 THEN true ELSE false END as can_analyze,
                   (5 - upload_count) as remaining_uploads,
                   (3 - analysis_count) as remaining_analyses
        """)

        session_id = uuid.uuid4()
        params = {
            "session_id": session_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": current_time,
            "expires_at": expires_at,
            "last_activity_at": current_time,
            "upload_count": 0,
            "analysis_count": 0,
            "is_active": True,
            "is_converted_to_user": False
        }

        result = await self.db.execute(sql, params)
        await self.db.commit()
        row = result.mappings().first()
        return dict(row) if row else None

    async def get_guest_session(self, session_id: uuid.UUID):
        sql = text("""
            SELECT *,
                   CASE WHEN expires_at < (NOW() AT TIME ZONE 'UTC') THEN true ELSE false END as is_expired,
                   CASE WHEN expires_at >= (NOW() AT TIME ZONE 'UTC') AND is_active = true AND upload_count < 5 THEN true ELSE false END as can_upload,
                   CASE WHEN expires_at >= (NOW() AT TIME ZONE 'UTC') AND is_active = true AND analysis_count < 3 THEN true ELSE false END as can_analyze,
                   (5 - upload_count) as remaining_uploads,
                   (3 - analysis_count) as remaining_analyses
            FROM guest_sessions
            WHERE session_id = :session_id
        """)

        result = await self.db.execute(sql, {"session_id": session_id})
        row = result.mappings().first()
        return dict(row) if row else None

    async def get_guest_statistics(self):
        total_sessions_sql = text("SELECT COUNT(*) as total FROM guest_sessions")
        total_sessions_result = await self.db.execute(total_sessions_sql)
        total_sessions = total_sessions_result.scalar() or 0

        active_sessions_sql = text("""
            SELECT COUNT(*) as active
            FROM guest_sessions
            WHERE is_active = true AND expires_at >= (NOW() AT TIME ZONE 'UTC')
        """)
        active_sessions_result = await self.db.execute(active_sessions_sql)
        active_sessions = active_sessions_result.scalar() or 0

        # Total uploads (sum of upload_count from all sessions)
        total_uploads_sql = text("SELECT COALESCE(SUM(upload_count), 0) as total FROM guest_sessions")
        total_uploads_result = await self.db.execute(total_uploads_sql)
        total_uploads = total_uploads_result.scalar() or 0

        # Total analyses (sum of analysis_count from all sessions)
        total_analyses_sql = text("SELECT COALESCE(SUM(analysis_count), 0) as total FROM guest_sessions")
        total_analyses_result = await self.db.execute(total_analyses_sql)
        total_analyses = total_analyses_result.scalar() or 0

        # Converted users
        converted_users_sql = text("SELECT COUNT(*) as converted FROM guest_sessions WHERE is_converted_to_user = true")
        converted_users_result = await self.db.execute(converted_users_sql)
        converted_users = converted_users_result.scalar() or 0

        # Calculate average session duration (in hours)
        avg_duration_sql = text("""
            SELECT AVG(EXTRACT(EPOCH FROM (COALESCE(last_activity_at, NOW()) - created_at)) / 3600) as avg_hours
            FROM guest_sessions
        """)
        avg_duration_result = await self.db.execute(avg_duration_sql)
        avg_duration = avg_duration_result.scalar() or 0.0

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_uploads": int(total_uploads),
            "total_analyses": int(total_analyses),
            "converted_users": converted_users,
            "average_session_duration": round(avg_duration, 2)
        }