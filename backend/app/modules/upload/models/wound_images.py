from sqlmodel import SQLModel, Field, Column
from sqlalchemy import String
from typing import Optional
from datetime import datetime, timezone
import uuid

class ImageInformation(SQLModel, table=True):
    __tablename__ = "image_information"

    wound_images_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    woundhistory_id: str = Field(index=True)

    # Upload status
    upload_status: str = Field(
        default="pending",
        sa_column=Column(String(20))
    )

    # File information
    file_name: str
    file_path: str
    file_size: int = Field(gt=0)
    file_type: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)

    # Error handling
    error_message: Optional[str] = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    def __init__(self, **data):
        if 'upload_status' not in data:
            data['upload_status'] = 'pending'
        super().__init__(**data)

    @property
    def status_display(self) -> str:
        """Get upload status in Vietnamese."""
        status_map = {
            "pending": "Đang chờ",
            "processing": "Đang xử lý",
            "completed": "Hoàn thành",
            "failed": "Thất bại"
        }
        return status_map.get(self.upload_status.lower(), self.upload_status)

    @property
    def is_successful(self) -> bool:
        """Check if upload was successful."""
        return self.upload_status.lower() == "completed"

    @property
    def has_error(self) -> bool:
        """Check if upload has error."""
        return self.upload_status.lower() == "failed" or self.error_message is not None

    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size / (1024 * 1024) if self.file_size else 0.0

    @property
    def aspect_ratio(self) -> float:
        """Calculate image aspect ratio (width/height)."""
        return self.width / self.height if self.height > 0 else 0.0

    @classmethod
    def create_image(
        cls,
        woundhistory_id: str,
        file_name: str,
        file_path: str,
        file_size: int,
        file_type: str,
        width: int,
        height: int,
        upload_status: str = "pending",
        error_message: Optional[str] = None
    ) -> "ImageInformation":
        """Create a new image information record."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        return cls(
            woundhistory_id=woundhistory_id,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            width=width,
            height=height,
            upload_status=upload_status,
            error_message=error_message,
            created_at=current_time,
            updated_at=current_time
        )

    def update_status(
        self,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Update image upload status."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        self.upload_status = status
        if error_message is not None:
            self.error_message = error_message
        self.updated_at = current_time

    def mark_as_completed(self) -> None:
        """Mark image upload as completed."""
        self.update_status("completed")

    def mark_as_failed(self, error_message: str) -> None:
        """Mark image upload as failed with error message."""
        self.update_status("failed", error_message)

    def to_detail_dict(self) -> dict:
        """Convert image to detail dictionary for API responses."""
        return {
            "id": self.wound_images_id,
            "woundhistory_id": self.woundhistory_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_size_mb": round(self.file_size_mb, 2),
            "file_type": self.file_type,
            "width": self.width,
            "height": self.height,
            "aspect_ratio": round(self.aspect_ratio, 2),
            "upload_status": self.upload_status,
            "status_display": self.status_display,
            "error_message": self.error_message,
            "is_successful": self.is_successful,
            "has_error": self.has_error,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }