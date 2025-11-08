from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class DashboardOverviewResponse(BaseModel):
    # User Statistics
    total_users: int
    new_users_this_month: int = Field(description="Number of new users registered this month")
    growth_rate: float 
    
    # Image Statistics
    total_images: int
    analyzed_images: int
    image_growth_rate: float
    
    # Active Users Statistics (new)
    active_users: int = Field(description="Number of active users in the last 7 days")
    active_users_growth: float = Field(description="Active users growth percentage")
    online_now: int = Field(description="Number of users online right now")
    
    # Session Statistics
    total_sessions: int
    avg_session_duration_seconds: int
    session_growth_rate: float

    class Config:
        json_schema_extra = {
            "example": {
                "total_users": 5247,
                "new_users_this_month": 628,
                "growth_rate": 12.0,
                "total_images": 12483,
                "analyzed_images": 11956,
                "image_growth_rate": 8.0,
                "active_users": 1523,
                "active_users_growth": 15.5,
                "online_now": 28,
                "total_sessions": 28394,
                "avg_session_duration_seconds": 512,
                "session_growth_rate": 18.0
            }
        }


class WoundTypeDistributionItem(BaseModel):
    name: str
    value: int
    color: str

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Abrasion",
                "value": 145,
                "color": "#06b6d4"
            }
        }


class WoundTypeDistributionResponse(BaseModel):
    distribution: List[WoundTypeDistributionItem]
    total_detections: int

    class Config:
        json_schema_extra = {
            "example": {
                "distribution": [
                    {"name": "Abrasion", "value": 145, "color": "#06b6d4"},
                    {"name": "Burn", "value": 89, "color": "#3b82f6"},
                    {"name": "Bruise", "value": 98, "color": "#ec4899"}
                ],
                "total_detections": 332
            }
        }


class DailyActivityItem(BaseModel):
    date: str
    uploads: int
    analyses: int

    class Config:
        json_schema_extra = {
            "example": {
                "date": "Mon",
                "uploads": 45,
                "analyses": 42
            }
        }


class WeeklyActivityResponse(BaseModel):
    daily_stats: List[DailyActivityItem] 
    total_uploads: int
    total_analyses: int

    class Config:
        json_schema_extra = {
            "example": {
                "daily_stats": [
                    {"date": "Mon", "uploads": 45, "analyses": 42},
                    {"date": "Tue", "uploads": 52, "analyses": 48}
                ],
                "total_uploads": 335,
                "total_analyses": 315
            }
        }


class SystemLogItem(BaseModel):
    """Schema for system log entry"""
    type: str = Field(description="Log type: error, warning, info, success")
    message: str = Field(description="Log message")
    time: str = Field(description="Human readable time ago")
    severity: str = Field(description="Severity level: high, medium, low")
    timestamp: Optional[datetime] = Field(default=None, description="Actual timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "warning",
                "message": "High server load detected",
                "time": "5 minutes ago",
                "severity": "medium",
                "timestamp": "2024-10-25T14:25:00Z"
            }
        }


class SystemLogsResponse(BaseModel):
    """Schema for system logs response"""
    logs: List[SystemLogItem] = Field(description="List of system logs")
    total_logs: int = Field(description="Total number of logs")
    unresolved_errors: int = Field(default=0, description="Number of unresolved errors")

    class Config:
        json_schema_extra = {
            "example": {
                "logs": [
                    {
                        "type": "warning",
                        "message": "High server load detected",
                        "time": "5 minutes ago",
                        "severity": "medium"
                    }
                ],
                "total_logs": 234,
                "unresolved_errors": 12
            }
        }


class SeverityStatsItem(BaseModel):
    """Schema for severity level statistics item"""
    name: str = Field(description="Severity level name")
    value: int = Field(description="Count or percentage")
    color: str = Field(description="Display color for the severity level")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Mild",
                "value": 60,
                "color": "#10b981"
            }
        }


class SeverityStatsResponse(BaseModel):
    """Schema for severity level statistics response"""
    stats: List[SeverityStatsItem] = Field(description="List of severity statistics")
    total_detections: int = Field(description="Total number of wound detections")

    class Config:
        json_schema_extra = {
            "example": {
                "stats": [
                    {"name": "Mild", "value": 60, "color": "#10b981"},
                    {"name": "Moderate", "value": 30, "color": "#f59e0b"},
                    {"name": "Severe", "value": 10, "color": "#ef4444"}
                ],
                "total_detections": 1250
            }
        }
