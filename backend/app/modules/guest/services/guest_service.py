from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text
import uuid
from datetime import datetime, timedelta, timezone

from app.modules.guest.models.guest_session import GuestSession
from app.modules.guest.models.guest_upload import GuestUpload
from app.modules.guest.models.guest_analysis import GuestAnalysis

class GuestService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_guest_session(self, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        expires_at = current_time + timedelta(hours=1)

        sql = text("""
            INSERT INTO guest_sessions (session_id, ip_address, user_agent, created_at, expires_at, last_activity_at, upload_count, analysis_count, is_active, is_converted_to_user)
            VALUES (:session_id, :ip_address, :user_agent, :created_at, :expires_at, :last_activity_at, :upload_count, :analysis_count, :is_active, :is_converted_to_user)
            RETURNING *
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
                   CASE WHEN expires_at < NOW() THEN true ELSE false END as is_expired,
                   CASE WHEN expires_at >= NOW() AND is_active = true AND upload_count < 5 THEN true ELSE false END as can_upload,
                   CASE WHEN expires_at >= NOW() AND is_active = true AND analysis_count < 3 THEN true ELSE false END as can_analyze,
                   (5 - upload_count) as remaining_uploads,
                   (3 - analysis_count) as remaining_analyses
            FROM guest_sessions
            WHERE session_id = :session_id
        """)

        result = await self.db.execute(sql, {"session_id": session_id})
        row = result.mappings().first()
        return dict(row) if row else None

    async def create_guest_upload(self, session_id: uuid.UUID, file_path: str, file_name: str, file_size: int, mime_type: Optional[str] = None):
        session = await self.get_guest_session(session_id)
        if not session or session.get("is_expired") or not session.get("can_upload"):
            return None

        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        sql = text("""
            INSERT INTO guest_uploads (upload_id, session_id, file_path, file_name, file_size, mime_type, created_at)
            VALUES (:upload_id, :session_id, :file_path, :file_name, :file_size, :mime_type, :created_at)
            RETURNING *
        """)

        upload_id = uuid.uuid4()
        params = {
            "upload_id": upload_id,
            "session_id": session_id,
            "file_path": file_path,
            "file_name": file_name,
            "file_size": file_size,
            "mime_type": mime_type,
            "created_at": current_time
        }

        result = await self.db.execute(sql, params)

        update_sql = text("""
            UPDATE guest_sessions
            SET upload_count = upload_count + 1, last_activity_at = :last_activity_at
            WHERE session_id = :session_id
        """)

        await self.db.execute(update_sql, {
            "session_id": session_id,
            "last_activity_at": current_time
        })

        await self.db.commit()
        row = result.mappings().first()
        return dict(row) if row else None

    async def create_guest_analysis(self, session_id: uuid.UUID, upload_id: Optional[uuid.UUID] = None, wound_type: Optional[str] = None, severity: Optional[str] = None, confidence: Optional[float] = None, result_json: Optional[Dict[str, Any]] = None):
        session = await self.get_guest_session(session_id)
        if not session or session.get("is_expired") or not session.get("can_analyze"):
            return None

        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        sql = text("""
            INSERT INTO guest_analyses (analysis_id, session_id, upload_id, wound_type, severity, confidence, result_json, created_at)
            VALUES (:analysis_id, :session_id, :upload_id, :wound_type, :severity, :confidence, :result_json, :created_at)
            RETURNING *
        """)

        analysis_id = uuid.uuid4()
        params = {
            "analysis_id": analysis_id,
            "session_id": session_id,
            "upload_id": upload_id,
            "wound_type": wound_type,
            "severity": severity,
            "confidence": confidence,
            "result_json": result_json,
            "created_at": current_time
        }

        result = await self.db.execute(sql, params)

        update_sql = text("""
            UPDATE guest_sessions
            SET analysis_count = analysis_count + 1, last_activity_at = :last_activity_at
            WHERE session_id = :session_id
        """)

        await self.db.execute(update_sql, {
            "session_id": session_id,
            "last_activity_at": current_time
        })

        await self.db.commit()
        row = result.mappings().first()
        return dict(row) if row else None

    async def get_guest_uploads(self, session_id: uuid.UUID, limit: int = 20, offset: int = 0):
        sql = text("""
            SELECT * FROM guest_uploads
            WHERE session_id = :session_id AND is_deleted = false
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await self.db.execute(sql, {
            "session_id": session_id,
            "limit": limit,
            "offset": offset
        })

        rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def get_guest_analyses(self, session_id: uuid.UUID, limit: int = 20, offset: int = 0):
        sql = text("""
            SELECT * FROM guest_analyses
            WHERE session_id = :session_id AND is_deleted = false
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await self.db.execute(sql, {
            "session_id": session_id,
            "limit": limit,
            "offset": offset
        })

        rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def get_guest_statistics(self):
        total_sessions_sql = text("SELECT COUNT(*) as total FROM guest_sessions")
        total_sessions_result = await self.db.execute(total_sessions_sql)
        total_sessions = total_sessions_result.scalar() or 0

        active_sessions_sql = text("""
            SELECT COUNT(*) as active
            FROM guest_sessions
            WHERE is_active = true AND expires_at >= NOW()
        """)
        active_sessions_result = await self.db.execute(active_sessions_sql)
        active_sessions = active_sessions_result.scalar() or 0

        total_uploads_sql = text("SELECT COUNT(*) as total FROM guest_uploads WHERE is_deleted = false")
        total_uploads_result = await self.db.execute(total_uploads_sql)
        total_uploads = total_uploads_result.scalar() or 0

        total_analyses_sql = text("SELECT COUNT(*) as total FROM guest_analyses WHERE is_deleted = false")
        total_analyses_result = await self.db.execute(total_analyses_sql)
        total_analyses = total_analyses_result.scalar() or 0

        converted_users_sql = text("SELECT COUNT(*) as converted FROM guest_sessions WHERE is_converted_to_user = true")
        converted_users_result = await self.db.execute(converted_users_sql)
        converted_users = converted_users_result.scalar() or 0

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_uploads": total_uploads,
            "total_analyses": total_analyses,
            "converted_users": converted_users
        }