from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text
from sqlalchemy import UUID
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta, timezone
import uuid

class GuestSessionService: 

    @staticmethod
    async def create_session(
        db: AsyncSession,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> uuid.UUID:
        """Tạo guest session mới"""
        session_id = uuid.uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        expires_at = expires_at.replace(tzinfo=None)
        
        query = text("""
            INSERT INTO guest_sessions (
                session_id, ip_address, user_agent, 
                created_at, expires_at, last_activity_at,
                upload_count, analysis_count, is_active
            ) VALUES (
                :session_id, :ip_address, :user_agent,
                NOW(), :expires_at, NOW(),
                0, 0, true
            )
            RETURNING session_id
        """)
        
        await db.execute(query, {
            "session_id": session_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "expires_at": expires_at
        })
        
        await db.commit()
        
        return session_id
    
    @staticmethod
    async def get_session(
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> Optional[Dict]:
        """Lấy thông tin session"""
        query = text("""
            SELECT * FROM guest_sessions
            WHERE session_id = :session_id
            
        """)
        result = await db.execute(query, {
            "session_id": session_id
        })
        row = result.mappings().first

        return dict(row) if row else None
    
    @staticmethod
    async def is_valid_session(
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> bool:
        """kiểm tra sessiong có hợp lệ không"""
        query = text("""
            SELECT session_id FROM guest_sessions
            WHERE session_id = :session_id
            AND is_active = true
            AND expires_at > NOW()
        """)

        result = await db.execute(query, {
            "session_id": session_id, 
        })
        return result.first() is not None 
    
    async def update_activity(
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> bool:
        """Cập nhật last_activity_at"""
        query = text("""
            UPDATE guest_sessions
            SET last_activity_at = NOW()
            WHERE session_id = :session_id
            AND is_active = true
            AND expires_at > NOW()
            RETURNING session_id
        """)
        
        result = await db.execute(query, {"session_id": session_id})
        await db.commit()
        
        return result.first() is not None
    
    @staticmethod
    async def can_upload(
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> Tuple[bool, Optional[str]]:
        """
        Kiểm tra session còn được upload không
        """
        from app.shared.role_permission_enum import GUEST_LIMITS
        
        query = text("""
            SELECT upload_count, is_active, expires_at
            FROM guest_sessions
            WHERE session_id = :session_id
        """)
        
        result = await db.execute(query, {"session_id": session_id})
        row = result.first()
        
        if not row:
            return False, "Session not found"
        
        upload_count, is_active, expires_at = row
        
        if not is_active:
            return False, "Session is inactive"
        
        if datetime.now(timezone.utc).replace(tzinfo=None) > expires_at:
            return False, "Session has expired"
        
        max_uploads = GUEST_LIMITS["max_uploads_per_session"]
        if upload_count >= max_uploads:
            return False, f"Upload limit reached ({max_uploads} per session)"
        
        return True, None
    
    @staticmethod
    async def can_analyze(
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> Tuple[bool, Optional[str]]:
        """
        Kiểm tra session còn được analyze không
        """
        from app.shared.role_permission_enum import GUEST_LIMITS
        
        query = text("""
            SELECT analysis_count, is_active, expires_at
            FROM guest_sessions
            WHERE session_id = :session_id
        """)
        
        result = await db.execute(query, {"session_id": session_id})
        row = result.first()
        
        if not row:
            return False, "Session not found"
        
        analysis_count, is_active, expires_at = row
        
        if not is_active:
            return False, "Session is inactive"
        
        if datetime.now(timezone.utc).replace(tzinfo=None) > expires_at:
            return False, "Session has expired"
        
        max_analyses = GUEST_LIMITS["max_analyses_per_session"]
        if analysis_count >= max_analyses:
            return False, f"Analysis limit reached ({max_analyses} per session)"
        
        return True, None
    
    @staticmethod
    async def increment_upload_count(
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> int:
        """Tăng upload counter"""
        query = text("""
            UPDATE guest_sessions
            SET upload_count = upload_count + 1
            WHERE session_id = :session_id
            RETURNING upload_count
        """)
        
        result = await db.execute(query, {"session_id": session_id})
        await db.commit()
        
        row = result.first()
        return row[0] if row else 0
    
    @staticmethod
    async def increment_analysis_count(
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> int:
        """Tăng analysis counter"""
        query = text("""
            UPDATE guest_sessions
            SET analysis_count = analysis_count + 1
            WHERE session_id = :session_id
            RETURNING analysis_count
        """)
        
        result = await db.execute(query, {"session_id": session_id})
        await db.commit()
        
        row = result.first()
        return row[0] if row else 0
    
    @staticmethod
    async def log_upload(
        db: AsyncSession,
        session_id: uuid.UUID,
        file_path: str,
        file_name: str,
        file_size: int,
        mime_type: Optional[str] = None
    ) -> uuid.UUID:
        """Log guest upload"""
        upload_id = uuid.uuid4()
        
        query = text("""
            INSERT INTO guest_uploads (
                upload_id, session_id, file_path, file_name,
                file_size, mime_type, created_at, is_deleted
            ) VALUES (
                :upload_id, :session_id, :file_path, :file_name,
                :file_size, :mime_type, NOW(), false
            )
            RETURNING upload_id
        """)
        
        await db.execute(query, {
            "upload_id": upload_id,
            "session_id": session_id,
            "file_path": file_path,
            "file_name": file_name,
            "file_size": file_size,
            "mime_type": mime_type
        })
        
        await db.commit()
        
        return upload_id
    
    @staticmethod
    async def log_analysis(
        db: AsyncSession,
        session_id: uuid.UUID,
        upload_id: Optional[uuid.UUID],
        wound_type: str,
        severity: str,
        confidence: float,
        result_json: dict
    ) -> uuid.UUID:
        """Log guest analysis"""
        import json

        analysis_id = uuid.uuid4()
        
        query = text("""
            INSERT INTO guest_analyses (
                analysis_id, session_id, upload_id,
                wound_type, severity, confidence, result_json,
                created_at, is_deleted
            ) VALUES (
                :analysis_id, :session_id, :upload_id,
                :wound_type, :severity, :confidence, :result_json,
                NOW(), false
            )
            RETURNING analysis_id
        """)
        
        await db.execute(query, {
            "analysis_id": analysis_id,
            "session_id": session_id,
            "upload_id": upload_id,
            "wound_type": wound_type,
            "severity": severity,
            "confidence": confidence,
            "result_json": json.dumps(result_json)
        })
        
        await db.commit()
        
        return analysis_id
    
    @staticmethod
    async def get_session_history(
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> Dict:
        """Lấy lịch sử uploads và analyses của session"""
        # Get uploads
        uploads_query = text("""
            SELECT 
                upload_id, file_name, file_size, mime_type, created_at
            FROM guest_uploads
            WHERE session_id = :session_id
            AND is_deleted = false
            ORDER BY created_at DESC
        """)
        
        uploads_result = await db.execute(uploads_query, {"session_id": session_id})
        uploads = [dict(row._mapping) for row in uploads_result]
        
        # Get analyses
        analyses_query = text("""
            SELECT 
                analysis_id, upload_id, wound_type, severity, 
                confidence, created_at
            FROM guest_analyses
            WHERE session_id = :session_id
            AND is_deleted = false
            ORDER BY created_at DESC
        """)
        
        analyses_result = await db.execute(analyses_query, {"session_id": session_id})
        analyses = [dict(row._mapping) for row in analyses_result]
        
        return {
            "uploads": uploads,
            "analyses": analyses,
            "total_uploads": len(uploads),
            "total_analyses": len(analyses)
        }
    
    @staticmethod
    async def get_session_stats(
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> Dict:
        """Lấy thống kê của session"""
        from app.shared.role_permission_enum import GUEST_LIMITS
        
        session = await GuestSessionService.get_session(db, session_id)
        
        if not session:
            return {}
        
        max_uploads = GUEST_LIMITS["max_uploads_per_session"]
        max_analyses = GUEST_LIMITS["max_analyses_per_session"]
        
        return {
            "session_id": session_id,
            "is_active": session["is_active"],
            "is_expired": datetime.now(timezone.utc).replace(tzinfo=None) > session["expires_at"],
            "created_at": session["created_at"],
            "expires_at": session["expires_at"],
            "upload_count": session["upload_count"],
            "analysis_count": session["analysis_count"],
            "remaining_uploads": max(0, max_uploads - session["upload_count"]),
            "remaining_analyses": max(0, max_analyses - session["analysis_count"]),
            "max_uploads": max_uploads,
            "max_analyses": max_analyses,
        }


    



        