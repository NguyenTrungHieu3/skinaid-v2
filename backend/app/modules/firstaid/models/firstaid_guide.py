from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

class FirstAidGuide(SQLModel, table=True):
    __tablename__ = "firstaid_guides"  # type: ignore

    firstaidguide_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )

    wound_type: str = Field(nullable=False)
    severity: str = Field(nullable=False)  # mild/moderate/severe
    title: str = Field(nullable=False)
    description: Optional[str] = None

    steps: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    warnings: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    dos: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    donts: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    supplies_needed: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    estimated_healing_time: Optional[str] = None
    is_active: bool = Field(default=True)
    version: int = Field(default=1)
    created_by: Optional[str] = Field(default=None, foreign_key="users.user_id")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    @property
    def severity_level(self) -> str:
        """Get the severity level as a readable string."""
        severity_map = {
            "mild": "Nhẹ",
            "moderate": "Trung bình",
            "severe": "Nặng"
        }
        return severity_map.get(self.severity.lower(), self.severity)

    @property
    def has_complete_instructions(self) -> bool:
        """Check if the guide has both do and don't instructions."""
        return bool(self.dos and self.donts)

    @property
    def instructions_count(self) -> int:
        """Count the number of instructions in the steps section."""
        if not self.steps:
            return 0
        if isinstance(self.steps, list):
            return len(self.steps)
        elif isinstance(self.steps, dict):
            return len(self.steps.get('items', []))
        return 0

    @property
    def supplies_count(self) -> int:
        """Count the number of supplies needed."""
        if not self.supplies_needed:
            return 0
        if isinstance(self.supplies_needed, list):
            return len(self.supplies_needed)
        elif isinstance(self.supplies_needed, dict):
            return len(self.supplies_needed.get('items', []))
        return 0

    @classmethod
    def create_guide(
        cls,
        wound_type: str,
        severity: str,
        title: str,
        description: Optional[str] = None,
        steps: Optional[Dict[str, Any]] = None,
        warnings: Optional[Dict[str, Any]] = None,
        dos: Optional[Dict[str, Any]] = None,
        donts: Optional[Dict[str, Any]] = None,
        supplies_needed: Optional[Dict[str, Any]] = None,
        estimated_healing_time: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> "FirstAidGuide":
        """Create a new first aid guide."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        return cls(
            wound_type=wound_type,
            severity=severity,
            title=title,
            description=description,
            steps=steps,
            warnings=warnings,
            dos=dos,
            donts=donts,
            supplies_needed=supplies_needed,
            estimated_healing_time=estimated_healing_time,
            created_by=created_by,
            created_at=current_time,
            updated_at=current_time
        )

    def update_guide(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        steps: Optional[Dict[str, Any]] = None,
        warnings: Optional[Dict[str, Any]] = None,
        dos: Optional[Dict[str, Any]] = None,
        donts: Optional[Dict[str, Any]] = None,
        supplies_needed: Optional[Dict[str, Any]] = None,
        estimated_healing_time: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> None:
        """Update the guide information."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if steps is not None:
            self.steps = steps
        if warnings is not None:
            self.warnings = warnings
        if dos is not None:
            self.dos = dos
        if donts is not None:
            self.donts = donts
        if supplies_needed is not None:
            self.supplies_needed = supplies_needed
        if estimated_healing_time is not None:
            self.estimated_healing_time = estimated_healing_time
        if is_active is not None:
            self.is_active = is_active

        self.updated_at = current_time

    def to_dict(self) -> dict:
        """Convert the model to a dictionary for API responses."""
        return {
            "firstaidguide_id": self.firstaidguide_id,
            "wound_type": self.wound_type,
            "severity": self.severity,
            "severity_display": self.severity_level,
            "title": self.title,
            "description": self.description,
            "steps": self.steps,
            "warnings": self.warnings,
            "dos": self.dos,
            "donts": self.donts,
            "supplies_needed": self.supplies_needed,
            "estimated_healing_time": self.estimated_healing_time,
            "is_active": self.is_active,
            "version": self.version,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "has_complete_instructions": self.has_complete_instructions,
            "instructions_count": self.instructions_count,
            "supplies_count": self.supplies_count
        }