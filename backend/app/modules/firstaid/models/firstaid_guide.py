# backend/app/modules/firstaid/models/firstaid_guide.py
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class FirstAidGuide(SQLModel, table=True):
    __tablename__ = "firstaid_guides"

    # Primary Fields
    firstaidguide_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )

    wound_type: str = Field(nullable=False, index=True)
    severity: str = Field(nullable=False, index=True)  # mild/moderate/severe
    sub_type: Optional[str] = Field(default=None, nullable=True, index=True)  # blister/skintear for burns
    
    title: str = Field(nullable=False)
    description: Optional[str] = None

    # Instructions (JSONB)
    steps: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    warnings: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    dos: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    donts: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    supplies_needed: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Metadata
    estimated_healing_time: Optional[str] = None
    is_active: bool = Field(default=True, index=True)
    version: int = Field(default=1)
    created_by: Optional[str] = Field(default=None, foreign_key="users.user_id")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


    @property
    def severity_level(self) -> str:
        """Get severity as Vietnamese string."""
        severity_map = {
            "mild": "Nhẹ",
            "moderate": "Trung bình",
            "severe": "Nặng"
        }
        return severity_map.get(self.severity.lower(), self.severity)

    @property
    def wound_type_display(self) -> str:
        """Get wound type as Vietnamese string."""
        wound_type_map = {
            "abrasion": "Vết trầy xước",
            "bruise": "Vết bầm tím",
            "burn": "Bỏng",
            "cut": "Vết cắt"
        }
        return wound_type_map.get(self.wound_type.lower(), self.wound_type)

    @property
    def sub_type_display(self) -> Optional[str]:
        """Get sub_type as Vietnamese string."""
        if not self.sub_type:
            return None
        
        sub_type_map = {
            "blister": "Phồng rộp",
            "skintear": "Rách da"
        }
        return sub_type_map.get(self.sub_type.lower(), self.sub_type)

    @property
    def full_classification(self) -> str:
        """
        Get full classification string.
        """
        parts = [self.wound_type.lower(), self.severity.lower()]
        if self.sub_type:
            parts.append(self.sub_type.lower())
        return "_".join(parts)

    @property
    def has_complete_instructions(self) -> bool:
        """Check if guide has both do and don't instructions."""
        return bool(self.dos and self.donts)

    @property
    def instructions_count(self) -> int:
        """Count number of instructions in steps."""
        if not self.steps:
            return 0
        if isinstance(self.steps, list):
            return len(self.steps)
        elif isinstance(self.steps, dict):
            return len(self.steps.get('items', []))
        return 0

    @property
    def supplies_count(self) -> int:
        """Count number of supplies needed."""
        if not self.supplies_needed:
            return 0
        if isinstance(self.supplies_needed, list):
            return len(self.supplies_needed)
        elif isinstance(self.supplies_needed, dict):
            return len(self.supplies_needed.get('items', []))
        return 0


    def get_steps_list(self) -> List[str]:
        """Extract steps as list of strings."""
        if not self.steps:
            return []
        if isinstance(self.steps, list):
            return self.steps
        elif isinstance(self.steps, dict):
            return self.steps.get('items', [])
        return []

    def get_warnings_list(self) -> List[str]:
        """Extract warnings as list of strings."""
        if not self.warnings:
            return []
        if isinstance(self.warnings, list):
            return self.warnings
        elif isinstance(self.warnings, dict):
            return self.warnings.get('items', [])
        return []

    def get_dos_list(self) -> List[str]:
        """Extract dos as list of strings."""
        if not self.dos:
            return []
        if isinstance(self.dos, list):
            return self.dos
        elif isinstance(self.dos, dict):
            return self.dos.get('items', [])
        return []

    def get_donts_list(self) -> List[str]:
        """Extract donts as list of strings."""
        if not self.donts:
            return []
        if isinstance(self.donts, list):
            return self.donts
        elif isinstance(self.donts, dict):
            return self.donts.get('items', [])
        return []

    def get_supplies_list(self) -> List[str]:
        """Extract supplies as list of strings."""
        if not self.supplies_needed:
            return []
        if isinstance(self.supplies_needed, list):
            return self.supplies_needed
        elif isinstance(self.supplies_needed, dict):
            return self.supplies_needed.get('items', [])
        return []

    def validate(self) -> bool:
        """
        Validate guide data.
        """
        valid_wound_types = ["abrasion", "bruise", "burn", "cut"]
        valid_severities = ["mild", "moderate", "severe"]
        valid_burn_subtypes = ["blister", "skintear"]

        # Check wound_type
        if self.wound_type.lower() not in valid_wound_types:
            logger.error(f"Invalid wound_type: {self.wound_type}")
            return False

        # Check severity
        if self.severity.lower() not in valid_severities:
            logger.error(f"Invalid severity: {self.severity}")
            return False

        # Check sub_type (only for burns)
        if self.sub_type:
            if self.wound_type.lower() != "burn":
                logger.error(f"Sub_type only allowed for burn wounds")
                return False
            if self.sub_type.lower() not in valid_burn_subtypes:
                logger.error(f"Invalid burn sub_type: {self.sub_type}")
                return False

        return True
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
        created_by: Optional[str] = None
    ) -> "FirstAidGuide":
        """Create a new first aid guide."""
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
            created_by=created_by,
            created_at=current_time,
            updated_at=current_time
        )
        
        # Validate
        if not guide.validate():
            raise ValueError(f"Invalid guide: {guide.full_classification}")
        
        logger.info(f"Created guide: {guide.full_classification}")
        return guide


    def update_guide(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        sub_type: Optional[str] = None,
        steps: Optional[Dict[str, Any]] = None,
        warnings: Optional[Dict[str, Any]] = None,
        dos: Optional[Dict[str, Any]] = None,
        donts: Optional[Dict[str, Any]] = None,
        supplies_needed: Optional[Dict[str, Any]] = None,
        estimated_healing_time: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> None:
        """Update guide information."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if sub_type is not None:
            self.sub_type = sub_type.lower() if sub_type else None
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "firstaidguide_id": self.firstaidguide_id,
            "wound_type": self.wound_type,
            "wound_type_display": self.wound_type_display,
            "severity": self.severity,
            "severity_display": self.severity_level,
            "sub_type": self.sub_type,
            "sub_type_display": self.sub_type_display,
            "full_classification": self.full_classification,
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

    def to_snapshot(self) -> Dict[str, Any]:
        """Convert to snapshot format for wound analysis storage."""
        return {
            "title": self.title,
            "description": self.description,
            "steps": self.get_steps_list(),
            "warnings": self.get_warnings_list(),
            "dos": self.get_dos_list(),
            "donts": self.get_donts_list(),
            "supplies_needed": self.get_supplies_list(),
            "estimated_healing_time": self.estimated_healing_time
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<FirstAidGuide({self.full_classification}: {self.title})>"