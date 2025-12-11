from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func, and_, cast, Date
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple
import logging

from app.modules.auth.models.user import User
from app.modules.ai.models.wound_analysis import WoundAnalysis
from app.modules.ai.models.wound_detection import WoundDetection
from app.modules.guest.models.guest_session import GuestSession
from app.modules.audit.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class StatisticsService:
    """Service để thu thập thống kê cho dashboard"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_overview(self, period: str = 'month') -> Dict[str, Any]:
        """
        Lấy thống kê tổng quan cho dashboard admin
        Trả về dữ liệu cho tất cả 4 thẻ chính
        """
        try:
            start_date, prev_start_date = self._get_date_range(period)

            # Get user statistics
            user_stats = await self._get_user_statistics(start_date, prev_start_date)
            
            # Get image/upload statistics
            image_stats = await self._get_image_statistics(start_date, prev_start_date)
            
            # Get detection statistics
            detection_stats = await self._get_detection_statistics(start_date, prev_start_date)
            
            # Get model accuracy statistics
            accuracy_stats = await self._get_model_accuracy_statistics(start_date, prev_start_date)

            return {
                **user_stats,
                **image_stats,
                **detection_stats,
                **accuracy_stats
            }

        except Exception as e:
            logger.error(f"Thất bại khi lấy tổng quan dashboard: {e}")
            return self._get_default_overview()

    async def _get_user_statistics(self, start_date: datetime, prev_start_date: datetime) -> Dict[str, Any]:
        """Lấy thống kê liên quan đến người dùng"""
        try:
            # Total users (created in this period)
            if start_date == datetime.min:
                total_users_query = text("SELECT COUNT(*) as total FROM users WHERE is_active = true")
                total_result = await self.db.execute(total_users_query)
            else:
                total_users_query = text("SELECT COUNT(*) as total FROM users WHERE created_at >= :start_date AND is_active = true")
                total_result = await self.db.execute(total_users_query, {"start_date": start_date})
            
            total_users = total_result.scalar() or 0

            # New users in this period (same as total if filtered, but keeping logic for consistency)
            # If period is 'all', this might be same as total
            new_users_this_month = total_users

            # Users from previous period (for growth calculation)
            if prev_start_date == datetime.min:
                prev_new_users = 0
            else:
                prev_users_query = text("""
                    SELECT COUNT(*) as total 
                    FROM users 
                    WHERE created_at >= :prev_start 
                    AND created_at < :start_date 
                    AND is_active = true
                """)
                prev_result = await self.db.execute(prev_users_query, {
                    "prev_start": prev_start_date,
                    "start_date": start_date
                })
                prev_new_users = prev_result.scalar() or 0

            # Calculate growth rate: ((current - previous) / previous) * 100
            if prev_new_users > 0:
                growth_rate = ((new_users_this_month - prev_new_users) / prev_new_users) * 100
            else:
                growth_rate = 100.0 if new_users_this_month > 0 else 0.0

            return {
                "total_users": total_users,
                "new_users_this_month": new_users_this_month,
                "growth_rate": round(growth_rate, 1)
            }

        except Exception as e:
            logger.error(f"Thất bại khi lấy thống kê người dùng: {e}")
            return {
                "total_users": 0,
                "new_users_this_month": 0,
                "growth_rate": 0.0
            }

    async def _get_image_statistics(self, start_date: datetime, prev_start_date: datetime) -> Dict[str, Any]:
        """Lấy thống kê hình ảnh/upload"""
        try:
            # Total uploads in period
            if start_date == datetime.min:
                total_uploads_query = text("""SELECT COUNT(*) as total FROM audit_logs 
                    WHERE action IN ('image_upload', 'upload_image') AND success = true""")
                total_result = await self.db.execute(total_uploads_query)
            else:
                total_uploads_query = text("""SELECT COUNT(*) as total FROM audit_logs 
                    WHERE action IN ('image_upload', 'upload_image') AND success = true
                    AND timestamp >= :start_date""")
                total_result = await self.db.execute(total_uploads_query, {"start_date": start_date})
            
            total_images = total_result.scalar() or 0

            # Analyzed images (successful analyses) in period
            if start_date == datetime.min:
                analyzed_query = text("""
                    SELECT COUNT(*) as total 
                    FROM wound_analyses 
                    WHERE is_deleted = false
                """)
                analyzed_result = await self.db.execute(analyzed_query)
            else:
                analyzed_query = text("""
                    SELECT COUNT(*) as total 
                    FROM wound_analyses 
                    WHERE is_deleted = false
                    AND analyzed_at >= :start_date
                """)
                analyzed_result = await self.db.execute(analyzed_query, {"start_date": start_date})
            
            analyzed_images = analyzed_result.scalar() or 0

            # Uploads from previous period (for growth calculation)
            if prev_start_date == datetime.min:
                prev_uploads = 0
            else:
                prev_uploads_query = text("""
                    SELECT COUNT(*) as total 
                    FROM audit_logs 
                    WHERE action IN ('image_upload', 'upload_image') AND success = true
                    AND timestamp >= :prev_start 
                    AND timestamp < :start_date
                """)
                prev_result = await self.db.execute(prev_uploads_query, {
                    "prev_start": prev_start_date,
                    "start_date": start_date
                })
                prev_uploads = prev_result.scalar() or 0

            # Ensure total_images is at least equal to analyzed_images
            # This handles cases where audit logs might be missing or actions are named differently
            if total_images < analyzed_images:
                total_images = analyzed_images

            # Calculate growth rate
            if prev_uploads > 0:
                image_growth_rate = ((total_images - prev_uploads) / prev_uploads) * 100
            else:
                image_growth_rate = 100.0 if total_images > 0 else 0.0

            # Calculate new uploads in last 7 days (always last 7 days regardless of period)
            week_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)
            week_uploads_query = text("""
                SELECT COUNT(*) as total 
                FROM audit_logs 
                WHERE action IN ('image_upload', 'upload_image') AND success = true
                AND timestamp >= :week_start
            """)
            week_result = await self.db.execute(week_uploads_query, {"week_start": week_start})
            new_uploads_week = week_result.scalar() or 0

            return {
                "total_images": total_images,
                "analyzed_images": analyzed_images,
                "image_growth_rate": round(image_growth_rate, 1),
                "new_uploads_week": new_uploads_week
            }

        except Exception as e:
            logger.error(f"Thất bại khi lấy thống kê hình ảnh: {e}")
            return {
                "total_images": 0,
                "analyzed_images": 0,
                "image_growth_rate": 0.0,
                "new_uploads_week": 0
            }

    async def _get_detection_statistics(self, start_date: datetime, prev_start_date: datetime) -> Dict[str, Any]:
        """Lấy thống kê phát hiện vết thương"""
        try:
            # Total detections in period
            if start_date == datetime.min:
                detection_query = text("""
                    SELECT COUNT(*) as total 
                    FROM wound_detections wd
                    JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                    WHERE wa.is_deleted = false
                """)
                detection_result = await self.db.execute(detection_query)
            else:
                detection_query = text("""
                    SELECT COUNT(*) as total 
                    FROM wound_detections wd
                    JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                    WHERE wa.is_deleted = false
                    AND wa.analyzed_at >= :start_date
                """)
                detection_result = await self.db.execute(detection_query, {"start_date": start_date})
            
            total_detections = detection_result.scalar() or 0

            # Detections in previous period (for growth calculation)
            if prev_start_date == datetime.min:
                prev_detections = 0
            else:
                prev_detection_query = text("""
                    SELECT COUNT(*) as total 
                    FROM wound_detections wd
                    JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                    WHERE wa.is_deleted = false
                    AND wa.analyzed_at >= :prev_start
                    AND wa.analyzed_at < :start_date
                """)
                prev_result = await self.db.execute(prev_detection_query, {
                    "prev_start": prev_start_date,
                    "start_date": start_date
                })
                prev_detections = prev_result.scalar() or 0

            # Calculate growth rate
            if prev_detections > 0:
                detection_growth_rate = ((total_detections - prev_detections) / prev_detections) * 100
            else:
                detection_growth_rate = 100.0 if total_detections > 0 else 0.0

            # Get severe detections count
            if start_date == datetime.min:
                severe_query = text("""
                    SELECT COUNT(*) as total 
                    FROM wound_detections wd
                    JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                    WHERE wa.is_deleted = false
                    AND LOWER(wd.severity) = 'severe'
                """)
                severe_result = await self.db.execute(severe_query)
            else:
                severe_query = text("""
                    SELECT COUNT(*) as total 
                    FROM wound_detections wd
                    JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                    WHERE wa.is_deleted = false
                    AND wa.analyzed_at >= :start_date
                    AND LOWER(wd.severity) = 'severe'
                """)
                severe_result = await self.db.execute(severe_query, {"start_date": start_date})
            
            severe_detections = severe_result.scalar() or 0

            # Calculate new detections in last 7 days (always last 7 days regardless of period)
            week_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)
            week_detections_query = text("""
                SELECT COUNT(*) as total 
                FROM wound_detections wd
                JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                WHERE wa.is_deleted = false
                AND wa.analyzed_at >= :week_start
            """)
            week_det_result = await self.db.execute(week_detections_query, {"week_start": week_start})
            new_detections_week = week_det_result.scalar() or 0

            return {
                "total_detections": total_detections,
                "detection_growth_rate": round(detection_growth_rate, 1),
                "severe_detections": severe_detections,
                "new_detections_week": new_detections_week
            }

        except Exception as e:
            logger.error(f"Thất bại khi lấy thống kê phát hiện: {e}")
            return {
                "total_detections": 0,
                "detection_growth_rate": 0.0,
                "severe_detections": 0,
                "new_detections_week": 0
            }

    async def _get_model_accuracy_statistics(self, start_date: datetime, prev_start_date: datetime) -> Dict[str, Any]:
        """Lấy thống kê độ chính xác của mô hình AI dựa trên điểm tin cậy"""
        try:
            # Average confidence score from wound_detections in period
            if start_date == datetime.min:
                avg_confidence_query = text("""
                    SELECT AVG(wd.confidence_score) as avg_score
                    FROM wound_detections wd
                    JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                    WHERE wa.is_deleted = false
                """)
                avg_result = await self.db.execute(avg_confidence_query)
            else:
                avg_confidence_query = text("""
                    SELECT AVG(wd.confidence_score) as avg_score
                    FROM wound_detections wd
                    JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                    WHERE wa.is_deleted = false
                    AND wa.analyzed_at >= :start_date
                """)
                avg_result = await self.db.execute(avg_confidence_query, {"start_date": start_date})
            
            avg_confidence = avg_result.scalar() or 0.0
            # Convert to percentage
            avg_confidence_percent = round(avg_confidence * 100, 1)

            # Average confidence in previous period
            if prev_start_date == datetime.min:
                prev_avg_confidence_percent = 0.0
            else:
                prev_avg_query = text("""
                    SELECT AVG(wd.confidence_score) as avg_score
                    FROM wound_detections wd
                    JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                    WHERE wa.is_deleted = false
                    AND wa.analyzed_at >= :prev_start
                    AND wa.analyzed_at < :start_date
                """)
                prev_result = await self.db.execute(prev_avg_query, {
                    "prev_start": prev_start_date,
                    "start_date": start_date
                })
                prev_avg_confidence = prev_result.scalar() or 0.0
                prev_avg_confidence_percent = prev_avg_confidence * 100

            # Calculate accuracy trend (absolute difference, not percentage growth)
            if prev_avg_confidence_percent > 0:
                accuracy_trend = avg_confidence_percent - prev_avg_confidence_percent
            else:
                accuracy_trend = 0.0

            # Count high-confidence detections (confidence > 0.8)
            if start_date == datetime.min:
                high_conf_query = text("""
                    SELECT COUNT(*) as total
                    FROM wound_detections wd
                    JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                    WHERE wa.is_deleted = false
                    AND wd.confidence_score > 0.8
                """)
                high_conf_result = await self.db.execute(high_conf_query)
            else:
                high_conf_query = text("""
                    SELECT COUNT(*) as total
                    FROM wound_detections wd
                    JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                    WHERE wa.is_deleted = false
                    AND wd.confidence_score > 0.8
                    AND wa.analyzed_at >= :start_date
                """)
                high_conf_result = await self.db.execute(high_conf_query, {"start_date": start_date})
            
            high_confidence_count = high_conf_result.scalar() or 0

            return {
                "model_accuracy": avg_confidence_percent,
                "accuracy_trend": round(accuracy_trend, 1),
                "high_confidence_detections": high_confidence_count
            }

        except Exception as e:
            logger.error(f"Thất bại khi lấy thống kê độ chính xác mô hình: {e}")
            return {
                "model_accuracy": 0.0,
                "accuracy_trend": 0.0,
                "high_confidence_detections": 0
            }

    async def get_wound_type_distribution(self, period: str = 'month') -> Dict[str, Any]:
        """
        Lấy phân bố các loại vết thương cho biểu đồ tròn
        """
        try:
            start_date, _ = self._get_date_range(period)

            # Query wound types from detections
            if start_date == datetime.min:
                distribution_query = text("""
                    SELECT 
                        wound_type,
                        COUNT(*) as count
                    FROM wound_detections wd
                    JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                    WHERE wa.is_deleted = false
                    GROUP BY wound_type
                    ORDER BY count DESC
                """)
                result = await self.db.execute(distribution_query)
            else:
                distribution_query = text("""
                    SELECT 
                        wound_type,
                        COUNT(*) as count
                    FROM wound_detections wd
                    JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                    WHERE wa.is_deleted = false
                    AND wa.analyzed_at >= :start_date
                    GROUP BY wound_type
                    ORDER BY count DESC
                """)
                result = await self.db.execute(distribution_query, {"start_date": start_date})
            rows = result.fetchall()

            # Color mapping for wound types
            color_map = {
                "abrasion": "#06b6d4",
                "burn": "#3b82f6",
                "bruise": "#ec4899",
                "laceration": "#8b5cf6",
                "puncture": "#f59e0b"
            }

            distribution = []
            total_detections = 0

            for row in rows:
                wound_type = row[0]
                count = row[1]
                total_detections += count

                # Capitalize first letter
                display_name = wound_type.capitalize()
                color = color_map.get(wound_type.lower(), "#64748b")

                distribution.append({
                    "name": display_name,
                    "value": count,
                    "color": color
                })

            return {
                "distribution": distribution,
                "total_detections": total_detections
            }

        except Exception as e:
            logger.error(f"Thất bại khi lấy phân bố loại vết thương: {e}")
            return {
                "distribution": [],
                "total_detections": 0
            }

    async def get_weekly_activity(self) -> Dict[str, Any]:
        """
        Lấy thống kê hoạt động hàng tuần cho biểu đồ cột
        """
        try:
            # Get data for last 7 days
            end_date = datetime.now(timezone.utc).replace(tzinfo=None)
            start_date = end_date - timedelta(days=6)  # 7 days including today

            # Get daily uploads
            uploads_query = text("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as uploads
                FROM audit_logs
                WHERE action IN ('image_upload', 'upload_image') AND success = true
                AND timestamp >= :start_date
                GROUP BY DATE(timestamp)
                ORDER BY date ASC
            """)
            
            uploads_result = await self.db.execute(uploads_query, {
                "start_date": start_date
            })
            uploads_data = {row[0]: row[1] for row in uploads_result.fetchall()}

            # Get daily analyses
            analyses_query = text("""
                SELECT 
                    DATE(analyzed_at) as date,
                    COUNT(*) as analyses
                FROM wound_analyses
                WHERE analyzed_at >= :start_date
                AND is_deleted = false
                GROUP BY DATE(analyzed_at)
                ORDER BY date ASC
            """)
            
            analyses_result = await self.db.execute(analyses_query, {
                "start_date": start_date
            })
            analyses_data = {row[0]: row[1] for row in analyses_result.fetchall()}

            # Build daily stats for 7 days
            daily_stats = []
            day_names = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
            total_uploads = 0
            total_analyses = 0

            for i in range(7):
                current_date = start_date + timedelta(days=i)
                date_only = current_date.date()
                day_name = day_names[current_date.weekday()]

                uploads = uploads_data.get(date_only, 0)
                analyses = analyses_data.get(date_only, 0)

                total_uploads += uploads
                total_analyses += analyses

                daily_stats.append({
                    "date": day_name,
                    "uploads": uploads,
                    "analyses": analyses
                })

            return {
                "daily_stats": daily_stats,
                "total_uploads": total_uploads,
                "total_analyses": total_analyses
            }

        except Exception as e:
            logger.error(f"Thất bại khi lấy hoạt động hàng tuần: {e}")
            return self._get_default_weekly_activity()

    async def get_system_logs(self, limit: int = 10) -> Dict[str, Any]:
        """
        Lấy logs hệ thống và cảnh báo gần đây
        """
        try:
            logs = []

            # 1. Get recent admin actions from admin_audit_logs
            admin_logs_query = text("""
                SELECT 
                    created_at,
                    action,
                    resource_type,
                    resource_id,
                    admin_email,
                    status,
                    error_message,
                    description
                FROM admin_audit_logs
                ORDER BY created_at DESC
                LIMIT :limit
            """)
            
            admin_result = await self.db.execute(admin_logs_query, {"limit": limit})
            
            for row in admin_result.fetchall():
                created_at = row[0]
                action = row[1]
                resource_type = row[2]
                resource_id = row[3]
                admin_email = row[4]
                log_status = row[5]
                error_message = row[6]
                description = row[7]
                
                time_ago = self._get_time_ago(created_at)
                
                # Determine log type based on status and action
                if log_status == "error" or log_status == "failed":
                    log_type = "error"
                    severity = "high"
                elif log_status == "warning":
                    log_type = "warning"
                    severity = "medium"
                elif action.startswith("DELETE") or action.startswith("REMOVE"):
                    log_type = "warning"
                    severity = "medium"
                elif action.startswith("CREATE") or action.startswith("UPDATE"):
                    log_type = "success"
                    severity = "low"
                else:
                    log_type = "info"
                    severity = "low"
                
                # Build message
                if description:
                    message = description
                else:
                    message = f"{action} on {resource_type}"
                    if resource_id:
                        message += f" #{resource_id[:8]}"
                    message += f" by {admin_email}"
                
                if error_message:
                    message += f" - {error_message}"
                
                logs.append({
                    "type": log_type,
                    "message": message,
                    "time": time_ago,
                    "severity": severity,
                    "timestamp": created_at,
                    "source": "admin"
                })

            # 2. Get recent failed uploads from audit_logs (user/guest actions)
            failed_uploads_query = text("""
                SELECT 
                    timestamp,
                    error_message,
                    user_id
                FROM audit_logs
                WHERE action IN ('image_upload', 'upload_image') AND success = false
                ORDER BY timestamp DESC
                LIMIT :limit
            """)
            
            failed_result = await self.db.execute(failed_uploads_query, {"limit": limit // 2})
            
            for row in failed_result.fetchall():
                created_at = row[0]
                error_message = row[1] or "Upload thất bại"
                user_id = row[2]
                
                time_ago = self._get_time_ago(created_at)
                
                logs.append({
                    "type": "error",
                    "message": f"Upload hình ảnh thất bại" + (f" từ user #{str(user_id)[:8]}" if user_id else ""),
                    "time": time_ago,
                    "severity": "high",
                    "timestamp": created_at,
                    "source": "user"
                })

            # 3. Get recent successful analyses (as info logs)
            recent_analyses_query = text("""
                SELECT 
                    analyzed_at,
                    ai_model_version,
                    total_detections
                FROM wound_analyses
                WHERE is_deleted = false
                ORDER BY analyzed_at DESC
                LIMIT :limit
            """)
            
            analyses_result = await self.db.execute(recent_analyses_query, {"limit": limit // 2})
            
            for row in analyses_result.fetchall():
                analyzed_at = row[0]
                model_version = row[1]
                total_detections = row[2]
                
                time_ago = self._get_time_ago(analyzed_at)
                
                logs.append({
                    "type": "success" if total_detections > 0 else "info",
                    "message": f"Phân tích hoàn tất với {total_detections} phát hiện",
                    "time": time_ago,
                    "severity": "low",
                    "timestamp": analyzed_at,
                    "source": "system"
                })

            # Sort by timestamp and limit
            logs.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
            logs = logs[:limit]

            # Count unresolved errors (from both tables)
            unresolved_query = text("""
                SELECT 
                    (SELECT COUNT(*) FROM audit_logs 
                     WHERE action IN ('image_upload', 'upload_image') AND success = false
                     AND timestamp >= NOW() - INTERVAL '24 hours') +
                    (SELECT COUNT(*) FROM admin_audit_logs 
                     WHERE status IN ('error', 'failed')
                     AND created_at >= NOW() - INTERVAL '24 hours') as total
            """)
            unresolved_result = await self.db.execute(unresolved_query)
            unresolved_errors = unresolved_result.scalar() or 0

            return {
                "logs": logs,
                "total_logs": len(logs),
                "unresolved_errors": unresolved_errors
            }

        except Exception as e:
            logger.error(f"Thất bại khi lấy logs hệ thống: {e}")
            # Return empty logs instead of mock data
            return {
                "logs": [],
                "total_logs": 0,
                "unresolved_errors": 0
            }

    def _get_time_ago(self, timestamp: datetime) -> str:
        """Chuyển đổi timestamp sang dạng thời gian trôi qua dễ đọc"""
        try:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            diff = now - timestamp

            if diff.days > 0:
                return f"{diff.days} ngày trước"
            elif diff.seconds >= 3600:
                hours = diff.seconds // 3600
                return f"{hours} giờ trước"
            elif diff.seconds >= 60:
                minutes = diff.seconds // 60
                return f"{minutes} phút trước"
            else:
                return "Vừa xong"
        except:
            return "Không xác định"

    def _get_date_range(self, period: str) -> Tuple[datetime, datetime]:
        """
        Tính toán ngày bắt đầu và ngày bắt đầu của kỳ trước dựa trên khoảng thời gian
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        if period == 'day':
            start = now - timedelta(days=1)
            prev = start - timedelta(days=1)
        elif period == 'week':
            start = now - timedelta(days=7)
            prev = start - timedelta(days=7)
        elif period == 'month':
            start = now - timedelta(days=30)
            prev = start - timedelta(days=30)
        elif period == 'year':
            start = now - timedelta(days=365)
            prev = start - timedelta(days=365)
        else: # 'all'
            start = datetime.min
            prev = datetime.min
            
        return start, prev

    def _get_default_overview(self) -> Dict[str, Any]:
        """Giá trị mặc định khi truy vấn cơ sở dữ liệu thất bại"""
        return {
            "total_users": 0,
            "new_users_this_month": 0,
            "growth_rate": 0.0,
            "total_images": 0,
            "analyzed_images": 0,
            "image_growth_rate": 0.0,
            "new_uploads_week": 0,
            "total_detections": 0,
            "detection_growth_rate": 0.0,
            "severe_detections": 0,
            "new_detections_week": 0,
            "model_accuracy": 0.0,
            "accuracy_trend": 0.0,
            "high_confidence_detections": 0
        }

    def _get_default_weekly_activity(self) -> Dict[str, Any]:
        """Dữ liệu hoạt động hàng tuần mặc định"""
        return {
            "daily_stats": [
                {"date": "T2", "uploads": 0, "analyses": 0},
                {"date": "T3", "uploads": 0, "analyses": 0},
                {"date": "T4", "uploads": 0, "analyses": 0},
                {"date": "T5", "uploads": 0, "analyses": 0},
                {"date": "T6", "uploads": 0, "analyses": 0},
                {"date": "T7", "uploads": 0, "analyses": 0},
                {"date": "CN", "uploads": 0, "analyses": 0}
            ],
            "total_uploads": 0,
            "total_analyses": 0
        }



    async def get_severity_stats(self, period: str = 'month') -> Dict[str, Any]:
        """
        Lấy thống kê mức độ nghiêm trọng từ các phát hiện vết thương
        Trả về phân bố của các vết thương Nhẹ, Trung bình và Nặng
        Luôn trả về tất cả 3 mức độ nghiêm trọng ngay cả khi số lượng là 0
        """
        try:
            start_date, _ = self._get_date_range(period)

            # Query severity distribution from wound_detections table
            if start_date == datetime.min:
                severity_query = text("""
                    SELECT 
                        LOWER(severity) as severity_level,
                        COUNT(*) as count
                    FROM wound_detections wd
                    JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                    WHERE wa.is_deleted = false
                    GROUP BY LOWER(severity)
                    ORDER BY count DESC
                """)
                result = await self.db.execute(severity_query)
            else:
                severity_query = text("""
                    SELECT 
                        LOWER(severity) as severity_level,
                        COUNT(*) as count
                    FROM wound_detections wd
                    JOIN wound_analyses wa ON wd.analysis_id = wa.analysis_id
                    WHERE wa.is_deleted = false
                    AND wa.analyzed_at >= :start_date
                    GROUP BY LOWER(severity)
                    ORDER BY count DESC
                """)
                result = await self.db.execute(severity_query, {"start_date": start_date})
            rows = result.fetchall()

            # Color mapping for severity levels
            color_map = {
                "mild": "#10b981",      # Green
                "moderate": "#f59e0b",  # Orange
                "severe": "#ef4444"     # Red
            }

            # Normalize severity names
            name_map = {
                "mild": "Nhẹ",
                "moderate": "Trung bình",
                "severe": "Nặng"
            }

            # Initialize all severity levels with 0
            severity_data = {
                "mild": {"name": "Nhẹ", "value": 0, "color": "#10b981"},
                "moderate": {"name": "Trung bình", "value": 0, "color": "#f59e0b"},
                "severe": {"name": "Nặng", "value": 0, "color": "#ef4444"}
            }

            total_detections = 0

            # Update with actual data from database
            for row in rows:
                severity_level = row[0]  # Already lowercase from query
                count = row[1]
                total_detections += count

                if severity_level in severity_data:
                    severity_data[severity_level]["value"] = count
                else:
                    # Handle unexpected severity levels
                    logger.warning(f"Phát hiện mức độ nghiêm trọng không mong đợi: {severity_level}")
                    display_name = name_map.get(severity_level, severity_level.capitalize())
                    color = color_map.get(severity_level, "#6b7280")
                    severity_data[severity_level] = {
                        "name": display_name,
                        "value": count,
                        "color": color
                    }

            # Convert to list and sort by severity order: Mild -> Moderate -> Severe
            severity_order = {"mild": 0, "moderate": 1, "severe": 2}
            stats = sorted(
                severity_data.values(),
                key=lambda x: severity_order.get(x["name"].lower(), 999)
            )

            return {
                "stats": stats,
                "total_detections": total_detections
            }

        except Exception as e:
            logger.error(f"Thất bại khi lấy thống kê mức độ nghiêm trọng: {e}")
            # Return default data with all 3 levels on error
            return {
                "stats": [
                    {"name": "Mild", "value": 0, "color": "#10b981"},
                    {"name": "Moderate", "value": 0, "color": "#f59e0b"},
                    {"name": "Severe", "value": 0, "color": "#ef4444"}
                ],
                "total_detections": 0
            }
