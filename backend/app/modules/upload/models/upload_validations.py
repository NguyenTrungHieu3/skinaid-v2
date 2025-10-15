from typing import Optional, Any, Dict
import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB

class UploadValidation(SQLModel, table=True):
    __tablename__ = "upload_validations"  # type: ignore

    upload_validations_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    user_id: Optional[str] = Field(default=None, foreign_key="users.user_id", index=True)

    # file information
    file_name: Optional[str] = Field(default=None)
    file_size: Optional[int] = Field(default=None)
    file_type: Optional[str] = Field(default=None)

    # validation results
    validation_passed: bool = Field(default=False)
    validation_errors: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True)
    )

    # Request metadata
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), index=True)
    attempt_count: int = Field(default=1, ge=0)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    def __init__(self, **data):
        if 'validation_passed' not in data:
            data['validation_passed'] = False
        if 'attempt_count' not in data:
            data['attempt_count'] = 1
        super().__init__(**data)

    @property
    def validation_status(self) -> str:
        """Get validation status in Vietnamese."""
        if self.validation_passed:
            return "Thành công"
        else:
            return "Thất bại"

    @property
    def is_first_attempt(self) -> bool:
        """Check if this is the first validation attempt."""
        return self.attempt_count == 1

    @property
    def has_multiple_attempts(self) -> bool:
        """Check if there are multiple validation attempts."""
        return self.attempt_count > 1

    @classmethod
    def create_validation(
        cls,
        user_id: Optional[str] = None,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None,
        validation_passed: bool = False,
        validation_errors: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> "UploadValidation":
        """Create a new upload validation record."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        return cls(
            user_id=user_id,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            validation_passed=validation_passed,
            validation_errors=validation_errors,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id or str(uuid.uuid4()),
            attempt_count=1,
            created_at=current_time,
            updated_at=current_time
        )

    def add_validation_attempt(
        self,
        validation_passed: bool,
        validation_errors: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a new validation attempt."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        self.validation_passed = validation_passed
        self.validation_errors = validation_errors
        self.attempt_count += 1
        self.updated_at = current_time

    def to_response_dict(self) -> dict:
        """Convert validation to response dictionary."""
        return {
            "upload_validations_id": self.upload_validations_id,
            "user_id": self.user_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "validation_passed": self.validation_passed,
            "validation_status": self.validation_status,
            "validation_errors": self.validation_errors,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "attempt_count": self.attempt_count,
            "is_first_attempt": self.is_first_attempt,
            "has_multiple_attempts": self.has_multiple_attempts,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }