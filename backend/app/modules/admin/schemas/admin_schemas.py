from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class DashboardOverviewResponse(BaseModel):
    # User Statistics
    total_users: int
    new_users_this_month: int = Field(description="Number of new users registered this month")
    growth_rate: float 
    
    # Upload Statistics
    total_images: int
    analyzed_images: int
    image_growth_rate: float
    new_uploads_week: int = Field(description="Number of new uploads in the last 7 days")
    
    # Detection Statistics (replaced Active Users)
    total_detections: int = Field(description="Total number of detected wounds")
    detection_growth_rate: float = Field(description="Detection growth percentage")
    severe_detections: int = Field(description="Number of severe wound detections")
    new_detections_week: int = Field(description="Number of new detections in the last 7 days")
    
    # Model Accuracy Statistics (replaces Session Statistics)
    model_accuracy: float = Field(description="Average model confidence score percentage")
    accuracy_trend: float = Field(description="Accuracy trend compared to previous period")
    high_confidence_detections: int = Field(description="Number of high-confidence detections (>80%)")

    class Config:
        json_schema_extra = {
            "example": {
                "total_users": 5247,
                "new_users_this_month": 628,
                "growth_rate": 12.0,
                "total_images": 12483,
                "analyzed_images": 11956,
                "image_growth_rate": 8.0,
                "new_uploads_week": 145,
                "total_detections": 15230,
                "detection_growth_rate": 15.5,
                "severe_detections": 120,
                "new_detections_week": 210,
                "model_accuracy": 87.5,
                "accuracy_trend": 2.3,
                "high_confidence_detections": 12000
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
