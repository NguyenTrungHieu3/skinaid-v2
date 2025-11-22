from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UUID
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class FirstAidGuide(SQLModel, table=True):
    __tablename__ = "firstaid_guides"

    firstaidguide_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )

    wound_type: str = Field(nullable=False, index=True)
    severity: str = Field(nullable=False, index=True)
    sub_type: Optional[str] = Field(default=None, nullable=True, index=True)
    
    title: str = Field(nullable=False)
    description: Optional[str] = None

    steps: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    warnings: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    dos: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    donts: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    supplies_needed: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    estimated_healing_time: Optional[str] = None
    source: Optional[str] = None
    is_active: bool = Field(default=True, index=True)
    is_deleted: bool = Field(default=False, index=True)
    version: int = Field(default=1)
    created_by: Optional[uuid.UUID] = Field(default=None, foreign_key="users.user_id")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    @staticmethod
    def extract_list(data: Optional[Any]) -> List[str]:
        if not data:
            return []
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get('items', [])
        return []

    @classmethod
    def create_guide(
        cls,
        wound_type: str,
        severity: str,
        title: str,
        description: Optional[str] = None,
        sub_type: Optional[str] = None,
        steps: Optional[Dict[str, Any]] = None,
        warnings: Optional[Dict[str, Any]] = None,
        dos: Optional[Dict[str, Any]] = None,
        donts: Optional[Dict[str, Any]] = None,
        supplies_needed: Optional[Dict[str, Any]] = None,
        estimated_healing_time: Optional[str] = None,
        source: Optional[str] = None,
        is_active: bool = True,
        created_by: Optional[uuid.UUID] = None
    ) -> "FirstAidGuide":
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        
        guide = cls(
            wound_type=wound_type.lower(),
            severity=severity.lower(),
            sub_type=sub_type.lower() if sub_type else None,
            title=title,
            description=description,
            steps=steps,
            warnings=warnings,
            dos=dos,
            donts=donts,
            supplies_needed=supplies_needed,
            estimated_healing_time=estimated_healing_time,
            source=source,
            is_active=is_active,
            created_by=created_by,
            created_at=current_time,
            updated_at=current_time
        )
        
        if not guide.validate():
            raise ValueError(f"Invalid guide: {guide.wound_type}/{guide.severity}")
        
        logger.info(f"Đã tạo hướng dẫn: {guide.wound_type}/{guide.severity}")
        return guide

    def validate(self) -> bool:
        valid_wound_types = ["abrasion", "bruise", "burn", "cut"]
        valid_severities = ["mild", "moderate", "severe"]
        valid_burn_subtypes = ["blister", "skintear"]

        if self.wound_type.lower() not in valid_wound_types:
            logger.error(f"Loại vết thương không hợp lệ: {self.wound_type}")
            return False

        if self.severity.lower() not in valid_severities:
            logger.error(f"Mức độ nghiêm trọng không hợp lệ: {self.severity}")
            return False

        # Sub-type validation removed to allow flexibility
        # if self.sub_type:
        #     if self.wound_type.lower() != "burn":
        #         logger.error("Sub_type chỉ được phép cho vết bỏng")
        #         return False
        #     if self.sub_type.lower() not in valid_burn_subtypes:
        #         logger.error(f"Sub_type bỏng không hợp lệ: {self.sub_type}")
        #         return False

        return True

    def to_snapshot(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "steps": self.extract_list(self.steps),
            "warnings": self.extract_list(self.warnings),
            "dos": self.extract_list(self.dos),
            "donts": self.extract_list(self.donts),
            "supplies_needed": self.extract_list(self.supplies_needed),
            "estimated_healing_time": self.estimated_healing_time,
            "source": self.source
        }

    def __repr__(self) -> str:
        sub = f"/{self.sub_type}" if self.sub_type else ""
        return f"<FirstAidGuide({self.wound_type}/{self.severity}{sub}: {self.title})>"