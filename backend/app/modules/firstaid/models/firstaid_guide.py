from sqlmodel import SQLModel, Field
import uuid
from typing import Optional
from datetime import datetime, timezone
class FirstAidGuide(SQLModel, table=True):
    __tablename__ = "firstaidguides"

    firstaidguides_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )

    wound_type: str = Field(max_length=100, nullable=False)
    severity: str = Field(nullable=False)  # mild/moderate/severe

    cause: Optional[str] = None
    symptoms: Optional[str] = None
    risks: Optional[str] = None
    first_aid_do: Optional[str] = None
    first_aid_dont: Optional[str] = None
    tip_easy_remember: Optional[str] = None

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
        return bool(self.first_aid_do and self.first_aid_dont)

    @property
    def instructions_count(self) -> int:
        """Count the number of instructions in the do section."""
        if not self.first_aid_do:
            return 0
        return len([line.strip() for line in self.first_aid_do.split('\n') if line.strip()])

    @classmethod
    def create_guide(
        cls,
        wound_type: str,
        severity: str,
        cause: Optional[str] = None,
        symptoms: Optional[str] = None,
        risks: Optional[str] = None,
        first_aid_do: Optional[str] = None,
        first_aid_dont: Optional[str] = None,
        tip_easy_remember: Optional[str] = None
    ) -> "FirstAidGuide":
        """Create a new first aid guide."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        return cls(
            wound_type=wound_type,
            severity=severity,
            cause=cause,
            symptoms=symptoms,
            risks=risks,
            first_aid_do=first_aid_do,
            first_aid_dont=first_aid_dont,
            tip_easy_remember=tip_easy_remember,
            created_at=current_time,
            updated_at=current_time
        )

    def update_guide(
        self,
        cause: Optional[str] = None,
        symptoms: Optional[str] = None,
        risks: Optional[str] = None,
        first_aid_do: Optional[str] = None,
        first_aid_dont: Optional[str] = None,
        tip_easy_remember: Optional[str] = None
    ) -> None:
        """Update the guide information."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        if cause is not None:
            self.cause = cause
        if symptoms is not None:
            self.symptoms = symptoms
        if risks is not None:
            self.risks = risks
        if first_aid_do is not None:
            self.first_aid_do = first_aid_do
        if first_aid_dont is not None:
            self.first_aid_dont = first_aid_dont
        if tip_easy_remember is not None:
            self.tip_easy_remember = tip_easy_remember

        self.updated_at = current_time

    def to_dict(self) -> dict:
        """Convert the model to a dictionary for API responses."""
        return {
            "firstaidguides_id": self.firstaidguides_id,
            "wound_type": self.wound_type,
            "severity": self.severity,
            "severity_display": self.severity_level,
            "information": {
                "cause": self.cause,
                "symptoms": self.symptoms,
                "risks": self.risks
            },
            "instructions": {
                "do": self._parse_instructions(self.first_aid_do) if self.first_aid_do else [],
                "dont": self._parse_instructions(self.first_aid_dont) if self.first_aid_dont else []
            },
            "tip": self.tip_easy_remember,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "has_complete_instructions": self.has_complete_instructions,
            "instructions_count": self.instructions_count
        }

    def _parse_instructions(self, instructions_text: Optional[str]) -> list[str]:
        """Parse instructions text into a list of instructions."""
        if not instructions_text:
            return []

        instructions = []
        for line in instructions_text.split('\n'):
            line = line.strip()
            if line:
                if line[0].isdigit() and '. ' in line[:4]:
                    line = line.split('. ', 1)[1]
                instructions.append(line)

        return instructions