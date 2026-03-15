from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UUID, UniqueConstraint
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging

from app.modules.firstaid.utils import unwrap_jsonb_list

logger = logging.getLogger(__name__)

VALID_WOUND_TYPES = ["abrasion", "bruise", "burn", "cut"]
VALID_SEVERITIES = ["mild", "moderate", "severe"]
VALID_BURN_SUBTYPES = ["blister", "skintear"]
EXPECTED_GUIDE_COUNT = 15


def _current_timestamp() -> datetime:
    """Generate current UTC timestamp without timezone info."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class FirstAidGuide(SQLModel, table=True):
    __tablename__ = "firstaid_guides"
    __table_args__ = (
        UniqueConstraint(
            "wound_type", "severity", "sub_type",
            name="firstaid_guides_wound_severity_subtype_key"
        ),
    )

    firstaidguide_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )

    wound_type: str = Field(nullable=False, index=True)
    severity: str = Field(nullable=False, index=True)
    sub_type: Optional[str] = Field(default=None, nullable=True, index=True)
    
    title: str = Field(nullable=False)

    steps: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    dos: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    donts: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    supplies_needed: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    estimated_healing_time: Optional[str] = None
    source: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    is_active: bool = Field(default=True, index=True)
    is_deleted: bool = Field(default=False, index=True)
    version: int = Field(default=1)
    created_by: Optional[uuid.UUID] = Field(default=None, foreign_key="users.user_id")

    created_at: datetime = Field(default_factory=_current_timestamp)
    updated_at: datetime = Field(default_factory=_current_timestamp)

    @classmethod
    def create_guide(
        cls,
        wound_type: str,
        severity: str,
        title: str,
        sub_type: Optional[str] = None,
        steps: Optional[Dict[str, Any]] = None,
        dos: Optional[Dict[str, Any]] = None,
        donts: Optional[Dict[str, Any]] = None,
        supplies_needed: Optional[Dict[str, Any]] = None,
        estimated_healing_time: Optional[str] = None,
        source: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
        created_by: Optional[uuid.UUID] = None
    ) -> "FirstAidGuide":
        current_time = _current_timestamp()

        guide = cls(
            wound_type=wound_type.lower(),
            severity=severity.lower(),
            sub_type=sub_type.lower() if sub_type else None,
            title=title,
            steps=steps,
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
            raise ValueError(f"Hướng dẫn không hợp lệ: {guide.wound_type}/{guide.severity}")

        logger.info(f"[FIRSTAID_MODEL] Đã tạo hướng dẫn: {guide.wound_type}/{guide.severity}")
        return guide

    def validate(self) -> bool:
        if self.wound_type.lower() not in VALID_WOUND_TYPES:
            logger.error(f"[FIRSTAID_MODEL] Loại vết thương không hợp lệ: {self.wound_type}")
            return False

        if self.severity.lower() not in VALID_SEVERITIES:
            logger.error(f"[FIRSTAID_MODEL] Mức độ nghiêm trọng không hợp lệ: {self.severity}")
            return False

        return True

    def to_snapshot(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "steps": unwrap_jsonb_list(self.steps),
            "dos": unwrap_jsonb_list(self.dos),
            "donts": unwrap_jsonb_list(self.donts),
            "supplies_needed": unwrap_jsonb_list(self.supplies_needed),
            "estimated_healing_time": self.estimated_healing_time
        }

    @staticmethod
    def extract_list(jsonb_data: Optional[Dict[str, Any]]) -> List[Any]:
        """Extract list from JSONB field."""
        if not jsonb_data:
            return []
        if isinstance(jsonb_data, dict):
            return jsonb_data.get("items", [])
        if isinstance(jsonb_data, list):
            return jsonb_data
        return []

    def __repr__(self) -> str:
        sub = f"/{self.sub_type}" if self.sub_type else ""
        return f"<FirstAidGuide({self.wound_type}/{self.severity}{sub}: {self.title})>"