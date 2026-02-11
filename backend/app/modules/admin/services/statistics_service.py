from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple
import logging

from app.modules.admin.repository.statistics_repository import StatisticsRepository

logger = logging.getLogger(__name__)


class StatisticsService:
    """Service to gather dashboard statistics."""

    def __init__(self, db: AsyncSession):
        self.repository = StatisticsRepository(db)

    async def get_dashboard_overview(self, period: str = 'month') -> Dict[str, Any]:
        """Get dashboard overview stats."""
        try:
            start_date, prev_start_date = self._get_date_range(period)

            user_stats = await self._get_user_statistics(start_date, prev_start_date)
            image_stats = await self._get_image_statistics(start_date, prev_start_date)
            detection_stats = await self._get_detection_statistics(start_date, prev_start_date)
            accuracy_stats = await self._get_model_accuracy_statistics(start_date, prev_start_date)

            return {
                **user_stats,
                **image_stats,
                **detection_stats,
                **accuracy_stats
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard overview: {e}")
            return self._get_default_overview()

    async def _get_user_statistics(self, start_date: datetime, prev_start_date: datetime) -> Dict[str, Any]:
        try:
            total_users = await self.repository.get_total_users(start_date)

            # For 'this month' new users calculation
            # If start_date is min (all time), new users is total users
            if start_date == datetime.min:
                new_users_this_period = total_users
            else:
                # Logic in original service was:
                # If filtered by date, "total" query uses that date.
                # And "new users this month" was set to "total users" from that query.
                # So we can just use total_users here as it respects the start_date filter from repository method.
                new_users_this_period = total_users

            # Previous period
            prev_new_users = 0
            if prev_start_date != datetime.min:
                prev_new_users = await self.repository.get_new_users(prev_start_date, start_date)

            # Growth rate
            if prev_new_users > 0:
                growth_rate = (
                    (new_users_this_period - prev_new_users) / prev_new_users) * 100
            else:
                growth_rate = 100.0 if new_users_this_period > 0 else 0.0

            return {
                "total_users": total_users,
                "new_users_this_month": new_users_this_period,
                "growth_rate": round(growth_rate, 1)
            }
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {"total_users": 0, "new_users_this_month": 0, "growth_rate": 0.0}

    async def _get_image_statistics(self, start_date: datetime, prev_start_date: datetime) -> Dict[str, Any]:
        try:
            total_images = await self.repository.get_total_uploads(start_date)
            analyzed_images = await self.repository.get_analyzed_images(start_date)

            prev_uploads = 0
            if prev_start_date != datetime.min:
                prev_uploads = await self.repository.get_uploads_in_range(prev_start_date, start_date)

            if total_images < analyzed_images:
                total_images = analyzed_images

            if prev_uploads > 0:
                image_growth_rate = (
                    (total_images - prev_uploads) / prev_uploads) * 100
            else:
                image_growth_rate = 100.0 if total_images > 0 else 0.0

            week_start = datetime.now(timezone.utc).replace(
                tzinfo=None) - timedelta(days=7)
            new_uploads_week = await self.repository.get_total_uploads(week_start)

            return {
                "total_images": total_images,
                "analyzed_images": analyzed_images,
                "image_growth_rate": round(image_growth_rate, 1),
                "new_uploads_week": new_uploads_week
            }
        except Exception as e:
            logger.error(f"Failed to get image stats: {e}")
            return {"total_images": 0, "analyzed_images": 0, "image_growth_rate": 0.0, "new_uploads_week": 0}

    async def _get_detection_statistics(self, start_date: datetime, prev_start_date: datetime) -> Dict[str, Any]:
        try:
            total_detections = await self.repository.get_total_detections(start_date)

            prev_detections = 0
            if prev_start_date != datetime.min:
                prev_detections = await self.repository.get_detections_in_range(prev_start_date, start_date)

            if prev_detections > 0:
                detection_growth_rate = (
                    (total_detections - prev_detections) / prev_detections) * 100
            else:
                detection_growth_rate = 100.0 if total_detections > 0 else 0.0

            severe_detections = await self.repository.get_severe_detections(start_date)

            week_start = datetime.now(timezone.utc).replace(
                tzinfo=None) - timedelta(days=7)
            new_detections_week = await self.repository.get_total_detections(week_start)

            return {
                "total_detections": total_detections,
                "detection_growth_rate": round(detection_growth_rate, 1),
                "severe_detections": severe_detections,
                "new_detections_week": new_detections_week
            }
        except Exception as e:
            logger.error(f"Failed to get detection stats: {e}")
            return {"total_detections": 0, "detection_growth_rate": 0.0, "severe_detections": 0, "new_detections_week": 0}

    async def _get_model_accuracy_statistics(self, start_date: datetime, prev_start_date: datetime) -> Dict[str, Any]:
        try:
            avg_confidence = await self.repository.get_avg_confidence(start_date)
            avg_confidence_percent = round(avg_confidence * 100, 1)

            prev_avg_confidence = 0.0
            if prev_start_date != datetime.min:
                prev_avg_confidence = await self.repository.get_avg_confidence(prev_start_date, start_date)
            prev_avg_confidence_percent = prev_avg_confidence * 100

            if prev_avg_confidence_percent > 0:
                accuracy_trend = avg_confidence_percent - prev_avg_confidence_percent
            else:
                accuracy_trend = 0.0

            high_confidence_count = await self.repository.get_high_confidence_count(start_date, 0.8)

            return {
                "model_accuracy": avg_confidence_percent,
                "accuracy_trend": round(accuracy_trend, 1),
                "high_confidence_detections": high_confidence_count
            }
        except Exception as e:
            logger.error(f"Failed to get accuracy stats: {e}")
            return {"model_accuracy": 0.0, "accuracy_trend": 0.0, "high_confidence_detections": 0}

    async def get_wound_type_distribution(self, period: str = 'month') -> Dict[str, Any]:
        try:
            start_date, _ = self._get_date_range(period)
            rows = await self.repository.get_wound_type_distribution(start_date)

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
            logger.error(f"Failed to get wound distribution: {e}")
            return {"distribution": [], "total_detections": 0}

    async def get_weekly_activity(self) -> Dict[str, Any]:
        try:
            end_date = datetime.now(timezone.utc).replace(tzinfo=None)
            start_date = end_date - timedelta(days=6)

            uploads_rows = await self.repository.get_daily_uploads(start_date)
            uploads_data = {row[0]: row[1] for row in uploads_rows}

            analyses_rows = await self.repository.get_daily_analyses(start_date)
            analyses_data = {row[0]: row[1] for row in analyses_rows}

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
            logger.error(f"Failed to get weekly activity: {e}")
            return self._get_default_weekly_activity()

    async def get_system_logs(self, limit: int = 10) -> Dict[str, Any]:
        try:
            logs = []

            # Admin logs
            admin_rows = await self.repository.get_recent_admin_logs(limit)
            for row in admin_rows:
                # Unpack row
                created_at, action, resource_type, resource_id, admin_email, log_status, error_message, description = row

                time_ago = self._get_time_ago(created_at)

                if log_status in ("error", "failed"):
                    log_type, severity = "error", "high"
                elif log_status == "warning" or action.startswith(("DELETE", "REMOVE")):
                    log_type, severity = "warning", "medium"
                elif action.startswith(("CREATE", "UPDATE")):
                    log_type, severity = "success", "low"
                else:
                    log_type, severity = "info", "low"

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

            # Failed uploads
            failed_uploads = await self.repository.get_recent_failed_uploads(limit // 2)
            for row in failed_uploads:
                created_at, error_message, user_id = row
                time_ago = self._get_time_ago(created_at)
                logs.append({
                    "type": "error",
                    "message": f"Upload hình ảnh thất bại" + (f" từ user #{str(user_id)[:8]}" if user_id else ""),
                    "time": time_ago,
                    "severity": "high",
                    "timestamp": created_at,
                    "source": "user"
                })

            # Analyses
            analyses = await self.repository.get_recent_analyses(limit // 2)
            for row in analyses:
                analyzed_at, model_version, total_detections = row
                time_ago = self._get_time_ago(analyzed_at)
                logs.append({
                    "type": "success" if total_detections > 0 else "info",
                    "message": f"Phân tích hoàn tất với {total_detections} phát hiện",
                    "time": time_ago,
                    "severity": "low",
                    "timestamp": analyzed_at,
                    "source": "system"
                })

            logs.sort(key=lambda x: x.get(
                "timestamp", datetime.min), reverse=True)
            logs = logs[:limit]

            unresolved_errors = await self.repository.get_unresolved_errors_count()

            return {
                "logs": logs,
                "total_logs": len(logs),
                "unresolved_errors": unresolved_errors
            }
        except Exception as e:
            logger.error(f"Failed to get system logs: {e}")
            return {"logs": [], "total_logs": 0, "unresolved_errors": 0}

    async def get_severity_stats(self, period: str = 'month') -> Dict[str, Any]:
        try:
            start_date, _ = self._get_date_range(period)
            rows = await self.repository.get_severity_distribution(start_date)

            severity_map = {row[0]: row[1] for row in rows}
            total = sum(severity_map.values())

            # Ensure all levels present
            for level in ['mild', 'moderate', 'severe']:
                if level not in severity_map:
                    severity_map[level] = 0

            return {
                "distribution": severity_map,
                "total": total
            }
        except Exception as e:
            logger.error(f"Failed to get severity stats: {e}")
            return {"distribution": {"mild": 0, "moderate": 0, "severe": 0}, "total": 0}

    def _get_time_ago(self, timestamp: datetime) -> str:
        try:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            diff = now - timestamp
            if diff.days > 0:
                return f"{diff.days} ngày trước"
            elif diff.seconds >= 3600:
                return f"{diff.seconds // 3600} giờ trước"
            elif diff.seconds >= 60:
                return f"{diff.seconds // 60} phút trước"
            else:
                return "Vừa xong"
        except:
            return "Không xác định"

    def _get_date_range(self, period: str) -> Tuple[datetime, datetime]:
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
        else:
            start = datetime.min
            prev = datetime.min
        return start, prev

    def _get_default_overview(self) -> Dict[str, Any]:
        return {
            "total_users": 0, "new_users_this_month": 0, "growth_rate": 0.0,
            "total_images": 0, "analyzed_images": 0, "image_growth_rate": 0.0, "new_uploads_week": 0,
            "total_detections": 0, "detection_growth_rate": 0.0, "severe_detections": 0, "new_detections_week": 0,
            "model_accuracy": 0.0, "accuracy_trend": 0.0, "high_confidence_detections": 0
        }

    def _get_default_weekly_activity(self) -> Dict[str, Any]:
        return {
            "daily_stats": [{"date": d, "uploads": 0, "analyses": 0} for d in ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]],
            "total_uploads": 0, "total_analyses": 0
        }
