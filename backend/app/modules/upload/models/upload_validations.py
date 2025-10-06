from typing import Optional, Any, Dict
from datetime import datetime, timezone
import uuid
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB

class UploadValidation(SQLModel, table=True):
    __tablename__ = "upload_validations"  # type: ignore

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    user_id: Optional[str] = Field(default=None, foreign_key="users.id", index=True)

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

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    def __init__(self, **data):
        if 'validation_passed' not in data:
            data['validation_passed'] = False
        super().__init__(**data)