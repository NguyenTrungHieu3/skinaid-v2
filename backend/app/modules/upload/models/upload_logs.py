
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy import UUID
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid


class UploadLog(SQLModel, table=True):
    __tablename__ = "upload_logs"  # type: ignore

    upload_log_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.user_id", index=True)
    analysis_id: Optional[uuid.UUID] = Field(default=None, foreign_key="wound_analyses.analysis_id", index=True)

    file_name: str = Field(max_length=255)
    file_size: int = Field(gt=0)
    mime_type: str = Field(max_length=100)

    upload_status: str = Field(default="pending", max_length=50)

    validation_errors: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True)
    )
    error_message: Optional[str] = Field(default=None)

    ip_address: Optional[str] = Field(default=None, sa_column=Column(INET, nullable=True))
    user_agent: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    @property
    def status_display(self) -> str:
        """Lấy trạng thái upload hiển thị dưới dạng tiếng Việt thân thiện."""
        status_map = {
            "pending": "Đang chờ",
            "success": "Thành công",
            "failed": "Thất bại"
        }
        return status_map.get(self.upload_status.lower(), self.upload_status)

    @property
    def is_successful(self) -> bool:
        """Kiểm tra upload có thành công hay không."""
        return self.upload_status.lower() == "success"

    @property
    def has_error(self) -> bool:
        """Kiểm tra upload có lỗi hay không (bao gồm trạng thái failed hoặc có thông điệp lỗi)."""
        return self.upload_status.lower() == "failed" or self.error_message is not None

    @property
    def has_validation_errors(self) -> bool:
        """Kiểm tra xem có tồn tại lỗi xác thực nào hay không."""
        return self.validation_errors is not None and len(self.validation_errors) > 0

    @property
    def file_size_mb(self) -> float:
        """Lấy kích thước tệp theo đơn vị MB (hỗ trợ hiển thị)."""
        return self.file_size / (1024 * 1024)

    @classmethod
    def create_log(
        cls,
        user_id: Optional[uuid.UUID] = None,
        analysis_id: Optional[uuid.UUID] = None,
        file_name: str = "",
        file_size: int = 0,
        mime_type: str = "",
        upload_status: str = "pending",
        validation_errors: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> "UploadLog":
        """Tạo một bản ghi log upload mới với đầy đủ thông tin liên quan."""
        return cls(
            user_id=user_id,
            analysis_id=analysis_id,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            upload_status=upload_status,
            validation_errors=validation_errors,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def mark_success(self) -> None:
        """Đánh dấu upload là thành công."""
        self.upload_status = "success"

    def mark_failed(self, error_message: str, validation_errors: Optional[Dict[str, Any]] = None) -> None:
        """Đánh dấu upload thất bại và lưu chi tiết lỗi/xác thực (nếu có)."""
        self.upload_status = "failed"
        self.error_message = error_message
        if validation_errors:
            self.validation_errors = validation_errors

    def update_analysis_id(self, analysis_id: uuid.UUID) -> None:
        """Cập nhật analysis_id sau khi quá trình phân tích hoàn tất."""
        self.analysis_id = analysis_id

    def to_response_dict(self) -> dict:
        """Chuyển đổi log upload sang dict phục vụ phản hồi API hoặc hiển thị."""
        return {
            "upload_log_id": self.upload_log_id,
            "user_id": self.user_id,
            "analysis_id": self.analysis_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_size_mb": round(self.file_size_mb, 2),
            "mime_type": self.mime_type,
            "upload_status": self.upload_status,
            "status_display": self.status_display,
            "validation_errors": self.validation_errors,
            "error_message": self.error_message,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "user_agent": self.user_agent,
            "created_at": self.created_at,
            "is_successful": self.is_successful,
            "has_error": self.has_error,
            "has_validation_errors": self.has_validation_errors
        }